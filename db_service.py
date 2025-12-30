import os
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.getenv("DATABASE_PATH", "./data.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def row_to_dict(row):
    if row is None:
        return None
    return {k: row[k] for k in row.keys()}

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    # admins table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    # users table (example)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    # receipts table (example)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

# Admin functions
def create_admin(username, password):
    if not username or not password:
        raise ValueError("username and password are required")
    conn = get_connection()
    cur = conn.cursor()
    password_hash = generate_password_hash(password)
    created_at = datetime.utcnow().isoformat()
    try:
        cur.execute("INSERT INTO admins (username, password_hash, created_at) VALUES (?, ?, ?)",
                    (username, password_hash, created_at))
        conn.commit()
    except sqlite3.IntegrityError:
        # user already exists: ignore
        pass
    finally:
        conn.close()

def get_admin_by_username(username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM admins WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    return row_to_dict(row)

def check_admin_credentials(username, password):
    admin = get_admin_by_username(username)
    if not admin:
        return False
    return check_password_hash(admin["password_hash"], password)

# Users functions
def create_user(name, email):
    conn = get_connection()
    cur = conn.cursor()
    created_at = datetime.utcnow().isoformat()
    try:
        cur.execute("INSERT INTO users (name, email, created_at) VALUES (?, ?, ?)",
                    (name, email, created_at))
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_user_by_id(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row_to_dict(row)

def get_users(limit=None, offset=0):
    conn = get_connection()
    cur = conn.cursor()
    if limit:
        cur.execute("SELECT * FROM users ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset))
    else:
        cur.execute("SELECT * FROM users ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]

def count_users():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as cnt FROM users")
    row = cur.fetchone()
    conn.close()
    return row["cnt"] if row else 0

# Receipts functions
def create_receipt(user_id, amount, status="pending", description=None):
    conn = get_connection()
    cur = conn.cursor()
    created_at = datetime.utcnow().isoformat()
    cur.execute(
        "INSERT INTO receipts (user_id, amount, status, description, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, amount, status, description, created_at)
    )
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return rid

def get_receipt_by_id(receipt_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM receipts WHERE id = ?", (receipt_id,))
    row = cur.fetchone()
    conn.close()
    return row_to_dict(row)

def get_receipts(limit=None, offset=0):
    conn = get_connection()
    cur = conn.cursor()
    if limit:
        cur.execute("SELECT * FROM receipts ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset))
    else:
        cur.execute("SELECT * FROM receipts ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]

def get_receipts_by_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM receipts WHERE user_id = ? ORDER BY id DESC", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]

def count_receipts():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as cnt FROM receipts")
    row = cur.fetchone()
    conn.close()
    return row["cnt"] if row else 0
