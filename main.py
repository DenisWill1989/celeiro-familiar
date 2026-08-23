from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import sqlite3
import os
from datetime import datetime

app = FastAPI(title="Celeiro Familiar - Sistema Neural Financeiro")

DB_FILE = "finance.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            user_name TEXT NOT NULL,
            date TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

class TransactionCreate(BaseModel):
    description: str
    amount: float
    type: str
    category: str
    user_name: str
    date: str = None

@app.get("/", response_class=HTMLResponse)
def read_root():
    html_path = os.path.join("templates", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Template não encontrado</h1>"

@app.get("/manifest.json")
def get_manifest():
    return FileResponse("manifest.json")

@app.get("/api/transactions")
def get_transactions():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions ORDER BY date DESC, id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/api/transactions")
def create_transaction(tx: TransactionCreate):
    if tx.type not in ["income", "expense"]:
        raise HTTPException(status_code=400, detail="Tipo inválido")
    if tx.user_name not in ["Denis William", "Nicole Santos"]:
        raise HTTPException(status_code=400, detail="Usuário inválido")
    
    tx_date = tx.date if tx.date else datetime.now().strftime("%Y-%m-%d")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO transactions (description, amount, type, category, user_name, date) VALUES (?, ?, ?, ?, ?, ?)",
        (tx.description, tx.amount, tx.type, tx.category, tx.user_name, tx_date)
    )
    conn.commit()
    tx_id = cursor.lastrowid
    conn.close()
    return {"id": tx_id, "message": "Transação registrada com sucesso"}

@app.delete("/api/transactions/{tx_id}")
def delete_transaction(tx_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
    conn.commit()
    conn.close()
    return {"message": "Transação removida"}

@app.get("/api/summary")
def get_summary():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'income'")
    total_income = cursor.fetchone()[0] or 0.0
    
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'expense'")
    total_expense = cursor.fetchone()[0] or 0.0
    
    conn.close()
    balance = total_income - total_expense
    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance
    }
