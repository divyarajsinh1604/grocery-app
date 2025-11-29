import sqlite3
from werkzeug.security import generate_password_hash

DB_NAME = "grocery.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    # ----- Users -----
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    );
    """)

    # ----- Products (with unit) -----
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        cost_price REAL NOT NULL,
        sell_price REAL NOT NULL,
        stock INTEGER NOT NULL,
        unit TEXT NOT NULL DEFAULT 'pcs'
    );
    """)

    # ----- Customers (with next_payment_date) -----
    cur.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        due REAL NOT NULL DEFAULT 0,
        next_payment_date TEXT
    );
    """)

    # ----- Bills -----
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        total REAL NOT NULL,
        payment_type TEXT NOT NULL,
        due_date TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers(id)
    );
    """)

    # ----- Bill items -----
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bill_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bill_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        line_total REAL NOT NULL,
        FOREIGN KEY (bill_id) REFERENCES bills(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    );
    """)

    conn.commit()
    conn.close()


def ensure_admin():
    """Make sure there is an admin/admin123 user."""
    conn = get_db()
    cur = conn.cursor()

    password_hash = generate_password_hash("admin123")

    cur.execute(
        """
        INSERT OR IGNORE INTO users (username, password_hash)
        VALUES (?, ?)
        """,
        ("admin", password_hash),
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    # For local manual runs
    init_db()
    ensure_admin()