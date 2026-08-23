from fastapi import FastAPI, HTTPException, Form, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
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
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT, amount REAL, type TEXT,
        category TEXT, user_name TEXT, date TEXT,
        bank TEXT, receipt TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS bills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT, amount REAL, category TEXT,
        user_name TEXT, bank TEXT, due_date TEXT,
        status TEXT DEFAULT 'pending', created_at TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

@app.get("/", response_class=HTMLResponse)
def read_root():
    p = os.path.join("templates", "index.html")
    return open(p, "r", encoding="utf-8").read() if os.path.exists(p) else "<h1>Erro</h1>"

@app.get("/manifest.json")
def get_manifest(): return FileResponse("manifest.json")

@app.get("/apple-touch-icon.png")
def get_apple_icon(): return FileResponse("static/apple-touch-icon.png")

@app.get("/favicon.ico")
def get_favicon(): return FileResponse("static/icon-512.png")

@app.get("/health")
def health(): return {"status": "ok"}

@app.get("/api/transactions")
def get_transactions():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM transactions ORDER BY date DESC, id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

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
        try: amount_float = float(amount)
        except: amount_float = 0.0

        receipt_path = None
        if receipt and receipt.filename:
            fname = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{receipt.filename}"
            fpath = os.path.join(UPLOAD_DIR, fname)
            with open(fpath, "wb") as f:
                shutil.copyfileobj(receipt.file, f)
            receipt_path = f"/uploads/{fname}"

        conn = sqlite3.connect(DB_FILE)
        conn.execute(
            "INSERT INTO transactions (description, amount, type, category, user_name, date, bank, receipt) VALUES (?,?,?,?,?,?,?,?)",
            (description, amount_float, type, category, user_name, tx_date, bank, receipt_path)
        )
        conn.commit()
        conn.close()
        return JSONResponse({"ok": True, "msg": "Registrado!"})
    except Exception as e:
        return JSONResponse({"ok": False, "msg": str(e)}, status_code=500)

@app.delete("/api/transactions/{tx_id}")
def delete_transaction(tx_id: int):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("DELETE FROM transactions WHERE id=?", (tx_id,))
    conn.commit()
    conn.close()
    return {"ok": True}

@app.get("/api/summary")
def get_summary():
    conn = sqlite3.connect(DB_FILE)
    inc = conn.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='income'").fetchone()[0]
    exp = conn.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='expense'").fetchone()[0]
    conn.close()
    return {"total_income": inc, "total_expense": exp, "balance": inc - exp}

@app.get("/api/bills")
def get_bills():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM bills WHERE status='pending' ORDER BY due_date ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

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
        try: amount_float = float(amount)
        except: amount_float = 0.0
        d = due_date if due_date else datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect(DB_FILE)
        conn.execute(
            "INSERT INTO bills (description, amount, category, user_name, bank, due_date, status, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (description, amount_float, category, user_name, bank, d, "pending", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        conn.close()
        return JSONResponse({"ok": True, "msg": "Conta criada!"})
    except Exception as e:
        return JSONResponse({"ok": False, "msg": str(e)}, status_code=500)

@app.put("/api/bills/{bill_id}/pay")
def pay_bill(bill_id: int):
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        bill = dict(conn.execute("SELECT * FROM bills WHERE id=?", (bill_id,)).fetchone())
        if not bill:
            conn.close()
            return JSONResponse({"ok": False, "msg": "Conta não encontrada"}, status_code=404)

        conn.execute(
            "INSERT INTO transactions (description, amount, type, category, user_name, date, bank, receipt) VALUES (?,?,?,?,?,?,?,?)",
            (bill["description"], bill["amount"], "expense", bill["category"], bill["user_name"], datetime.now().strftime("%Y-%m-%d"), bill["bank"], None)
        )
        conn.execute("UPDATE bills SET status='paid' WHERE id=?", (bill_id,))
        conn.commit()
        conn.close()
        return JSONResponse({"ok": True, "msg": "Conta paga e registrada como despesa!"})
    except Exception as e:
        return JSONResponse({"ok": False, "msg": str(e)}, status_code=500)

@app.delete("/api/bills/{bill_id}")
def delete_bill(bill_id: int):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("DELETE FROM bills WHERE id=?", (bill_id,))
    conn.commit()
    conn.close()
    return {"ok": True}

@app.get("/api/bills/summary")
def get_bills_summary():
    conn = sqlite3.connect(DB_FILE)
    total = conn.execute("SELECT COALESCE(SUM(amount),0) FROM bills WHERE status='pending'").fetchone()[0]
    count = conn.execute("SELECT COUNT(*) FROM bills WHERE status='pending'").fetchone()[0]
    conn.close()
    return {"pending_total": total, "pending_count": count}
