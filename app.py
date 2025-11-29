from flask import Flask, render_template, session, redirect
from datetime import datetime

from auth import auth
from products import products
from stock import stock
from billing import billing
from customers import customers_bp
from models import get_db
import os
from dotenv import load_dotenv

load_dotenv()


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# register blueprints
app.register_blueprint(auth)
app.register_blueprint(products)
app.register_blueprint(stock)
app.register_blueprint(billing)
app.register_blueprint(customers_bp)

@app.route("/")
def home():
    if "user_id" in session:
        return redirect("/dashboard")
    return redirect("/login")


@app.route("/dashboard")
def dashboard():
    conn = get_db()
    cur = conn.cursor()

    # 1) Today's sales
    cur.execute("""
        SELECT COALESCE(SUM(total), 0) AS today_sales
        FROM bills
        WHERE DATE(created_at) = DATE('now','localtime')
    """)
    row = cur.fetchone()
    today_sales = row["today_sales"] if row else 0

    # 2) Total udhar
    cur.execute("SELECT COALESCE(SUM(due), 0) AS total_udhar FROM customers")
    row = cur.fetchone()
    total_udhar = row["total_udhar"] if row else 0

    # 3) Bills today
    cur.execute("""
        SELECT COUNT(*) AS bills_today
        FROM bills
        WHERE DATE(created_at) = DATE('now','localtime')
    """)
    row = cur.fetchone()
    bills_today = row["bills_today"] if row else 0

    # 4) Low stock (your existing query, just make sure the comma is there)
    LOW_STOCK_LIMIT = 10
    cur.execute("""
        SELECT name, stock, unit
        FROM products
        WHERE stock <= ?
        ORDER BY stock ASC
    """, (LOW_STOCK_LIMIT,))
    low_stock = cur.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        show_nav=True,
        today_sales=today_sales,
        total_udhar=total_udhar,
        bills_today=bills_today,
        low_stock=low_stock,
    )

if __name__ == "__main__":
    app.run(debug=True)