from fastapi import FastAPI, HTTPException, Form, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import sqlite3
import os
from datetime import datetime
import shutil

app = FastAPI(title="Celeiro Familiar - Neural HUD Finance")

DB_FILE = "finance.db"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

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
            date TEXT NOT NULL,
            bank TEXT NOT NULL,
            receipt TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

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
async def create_transaction(
    description: str = Form(...),
    amount: float = Form(...),
    type: str = Form(...),
    category: str = Form(...),
    user_name: str = Form(...),
    bank: str = Form(...),
    date: str = Form(None),
    receipt: UploadFile = File(None)
):
    if type not in ["income", "expense"]:
        raise HTTPException(status_code=400, detail="Tipo inválido")
    if user_name not in ["Denis William", "Nicole Santos"]:
        raise HTTPException(status_code=400, detail="Usuário inválido")
    if bank not in ["Nubank", "Uber Conta", "Santander"]:
        raise HTTPException(status_code=400, detail="Banco inválido")
    
    tx_date = date if date else datetime.now().strftime("%Y-%m-%d")
    
    receipt_filename = None
    if receipt and receipt.filename:
        file_ext = os.path.splitext(receipt.filename)[1]
        receipt_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{receipt.filename}"
        file_path = os.path.join(UPLOAD_DIR, receipt_filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(receipt.file, buffer)
        receipt_filename = f"/uploads/{receipt_filename}"

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO transactions (description, amount, type, category, user_name, date, bank, receipt) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (description, amount, type, category, user_name, tx_date, bank, receipt_filename)
    )
    conn.commit()
    tx_id = cursor.lastrowid
    conn.close()
    return {"id": tx_id, "message": "Transação registrada com sucesso"}

@app.delete("/api/transactions/{tx_id}")
def delete_transaction(tx_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT receipt FROM transactions WHERE id = ?", (tx_id,))
    row = cursor.fetchone()
    if row and row[0]:
        file_path = row[0].lstrip("/")
        if os.path.exists(file_path):
            os.remove(file_path)
            
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
