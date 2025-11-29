import sqlite3
from werkzeug.security import generate_password_hash

DB_NAME = "grocery_v2.db"   # NEW FILE, fresh DB


import sqlite3
from werkzeug.security import generate_password_hash

def get_db():
    conn = sqlite3.connect("grocery_v2.db")
    conn.row_factory = sqlite3.Row
    return conn

# 🔧 ADD THIS FUNCTION
def migrate_customers_table():
    """Ensure customers table has next_payment_date column."""
    conn = get_db()
    cur = conn.cursor()

    # Read existing columns
    cur.execute("PRAGMA table_info(customers)")
    cols = [row[1] for row in cur.fetchall()]   # row[1] = column name

    # If column missing -> add it
    if "next_payment_date" not in cols:
        cur.execute("ALTER TABLE customers ADD COLUMN next_payment_date TEXT")
        conn.commit()

    conn.close()

def init_db():
    conn = get_db()
    cur = conn.cursor()

    # Users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    );
    """)

    # Products table WITH unit column
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

    # Customers table WITH next_payment_date
    cur.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        due REAL NOT NULL DEFAULT 0,
        next_payment_date TEXT
    );
    """)

    # Bills table
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

    # Bill items table
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


def create_admin():
    conn = get_db()
    cur = conn.cursor()

    password_hash = generate_password_hash("admin123")

    cur.execute("""
    INSERT OR IGNORE INTO users (username, password_hash)
    VALUES (?, ?)
    """, ("admin", password_hash))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    create_admin()