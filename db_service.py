import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from decimal import Decimal
import logging

DATABASE_URL = os.getenv("DATABASE_URL")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set in environment")
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT UNIQUE NOT NULL,
        username TEXT,
        balance NUMERIC DEFAULT 0,
        created_at TIMESTAMP DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS receipts (
        id SERIAL PRIMARY KEY,
        user_telegram_id BIGINT NOT NULL,
        file_path TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT NOW()
    );
    """)
    conn.commit()
    cur.close()
    conn.close()
    logger.info("Database initialized")

# User management
def create_user_if_not_exists(telegram_id: int, username: str = None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE telegram_id = %s", (telegram_id,))
    row = cur.fetchone()
    if not row:
        cur.execute(
            "INSERT INTO users (telegram_id, username) VALUES (%s, %s)",
            (telegram_id, username),
        )
        conn.commit()
    else:
        # optionally update username
        if username:
            cur.execute(
                "UPDATE users SET username = %s WHERE telegram_id = %s",
                (username, telegram_id),
            )
            conn.commit()
    cur.close()
    conn.close()

def get_user_by_username(username: str):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    # strip leading @ if provided
    if username.startswith("@"):
        username = username[1:]
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def get_user_by_telegram_id(telegram_id: int):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def get_balance(telegram_id: int) -> Decimal:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE telegram_id = %s", (telegram_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return Decimal(0)
    return Decimal(row[0])

def update_balance(telegram_id: int, amount: float) -> Decimal:
    conn = get_conn()
    cur = conn.cursor()
    # Ensure user exists
    cur.execute("SELECT id FROM users WHERE telegram_id = %s", (telegram_id,))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (telegram_id, balance) VALUES (%s, %s)",
            (telegram_id, amount),
        )
        conn.commit()
        cur.close()
        conn.close()
        return Decimal(amount)

    cur.execute(
        "UPDATE users SET balance = balance + %s WHERE telegram_id = %s RETURNING balance",
        (Decimal(str(amount)), telegram_id),
    )
    new_balance = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return Decimal(new_balance)

# Receipts
def create_receipt(telegram_id: int, file_path: str, status: str = 'pending') -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO receipts (user_telegram_id, file_path, status, created_at) VALUES (%s, %s, %s, %s) RETURNING id",
        (telegram_id, file_path, status, datetime.utcnow()),
    )
    receipt_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return receipt_id

def set_receipt_status(receipt_id: int, status: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE receipts SET status = %s WHERE id = %s", (status, receipt_id))
    conn.commit()
    cur.close()
    conn.close()
