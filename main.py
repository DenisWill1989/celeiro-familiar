from fastapi import FastAPI, HTTPException, Form, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os
from datetime import datetime
import shutil

app = FastAPI(title="Celeiro Familiar - Neural HUD Finance")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "finance.db"
UPLOAD_DIR = "uploads"
STATIC_DIR = "static"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            user_name TEXT NOT NULL,
            bank TEXT NOT NULL,
            due_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
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

@app.get("/apple-touch-icon.png")
def get_apple_icon():
    return FileResponse("static/apple-touch-icon.png")

@app.get("/favicon.ico")
def get_favicon():
    return FileResponse("static/icon-512.png")

@app.get("/api/transactions")
def get_transactions():
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transactions ORDER BY date DESC, id DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception:
        return []

@app.post("/api/transactions")
async def create_transaction(
    description: str = Form(""),
    amount: str = Form("0"),
    type: str = Form("expense"),
    category: str = Form("Outros"),
    user_name: str = Form("Denis William"),
    bank: str = Form("Nubank"),
    date: str = Form(""),
    receipt: UploadFile = File(None)
):
    try:
        tx_date = date if date else datetime.now().strftime("%Y-%m-%d")
        amount_float = float(amount) if amount else 0.0

        receipt_filename = None
        if receipt and receipt.filename and receipt.filename.strip():
            receipt_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{receipt.filename}"
            file_path = os.path.join(UPLOAD_DIR, receipt_filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(receipt.file, buffer)
            receipt_filename = f"/uploads/{receipt_filename}"

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO transactions (description, amount, type, category, user_name, date, bank, receipt) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (description, amount_float, type, category, user_name, tx_date, bank, receipt_filename)
        )
        conn.commit()
        tx_id = cursor.lastrowid
        conn.close()
        return {"id": tx_id, "message": "Transação registrada com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/transactions/{tx_id}")
def delete_transaction(tx_id: int):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
        conn.commit()
        conn.close()
        return {"message": "Transação removida"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/summary")
def get_summary():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'income'")
        total_income = cursor.fetchone()[0] or 0.0
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'expense'")
        total_expense = cursor.fetchone()[0] or 0.0
        conn.close()
        balance = total_income - total_expense
        return {"total_income": total_income, "total_expense": total_expense, "balance": balance}
    except Exception:
        return {"total_income": 0.0, "total_expense": 0.0, "balance": 0.0}

@app.get("/api/bills")
def get_bills():
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bills ORDER BY due_date ASC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception:
        return []

@app.post("/api/bills")
async def create_bill(
    description: str = Form(""),
    amount: str = Form("0"),
    category: str = Form("Outros"),
    user_name: str = Form("Denis William"),
    bank: str = Form("Nubank"),
    due_date: str = Form("")
):
    try:
        amount_float = float(amount) if amount else 0.0
        tx_date = due_date if due_date else datetime.now().strftime("%Y-%m-%d")
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO bills (description, amount, category, user_name, bank, due_date, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (description, amount_float, category, user_name, bank, tx_date, "pending", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        bill_id = cursor.lastrowid
        conn.close()
        return {"id": bill_id, "message": "Conta a pagar criada com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/bills/{bill_id}/pay")
async def pay_bill(bill_id: int):
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM bills WHERE id = ?", (bill_id,))
        bill = cursor.fetchone()
        
        if not bill:
            conn.close()
            raise HTTPException(status_code=404, detail="Conta não encontrada")
        
        bill = dict(bill)
        
        cursor.execute(
            "INSERT INTO transactions (description, amount, type, category, user_name, date, bank, receipt) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (bill["description"], bill["amount"], "expense", bill["category"], bill["user_name"], datetime.now().strftime("%Y-%m-%d"), bill["bank"], None)
        )
        
        cursor.execute("UPDATE bills SET status = 'paid' WHERE id = ?", (bill_id,))
        conn.commit()
        conn.close()
        
        return {"message": "Conta paga e registrada como despesa automaticamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/bills/{bill_id}")
def delete_bill(bill_id: int):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bills WHERE id = ?", (bill_id,))
        conn.commit()
        conn.close()
        return {"message": "Conta removida"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bills/summary")
def get_bills_summary():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(amount) FROM bills WHERE status = 'pending'")
        pending_total = cursor.fetchone()[0] or 0.0
        cursor.execute("SELECT COUNT(*) FROM bills WHERE status = 'pending'")
        pending_count = cursor.fetchone()[0] or 0
        conn.close()
        return {"pending_total": pending_total, "pending_count": pending_count}
    except Exception:
        return {"pending_total": 0.0, "pending_count": 0}
