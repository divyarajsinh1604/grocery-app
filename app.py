from flask import Flask, render_template, redirect, url_for, session
from datetime import datetime
import os

from auth import auth
from products import products
from stock import stock
from billing import billing
from customers import customers_bp

from models import get_db, init_db, ensure_admin


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

# ---- IMPORTANT: init DB on startup ----
init_db()
ensure_admin()
# ---------------------------------------


# register blueprints
app.register_blueprint(auth)
app.register_blueprint(products)
app.register_blueprint(stock)
app.register_blueprint(billing)
app.register_blueprint(customers_bp)


@app.route("/")
def root():
    if "user_id" in session:
        return redirect(url_for("dashboard"))   
    # redirect to login or dashboard, whatever you decided
    return redirect("/login")   # or "/dashboard"


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    # today as YYYY-MM-DD
    today_str = datetime.now().strftime("%Y-%m-%d")

    # 1) Today's sales
    cur.execute(
        """
        SELECT COALESCE(SUM(total), 0) AS today_sales
        FROM bills
        WHERE DATE(substr(created_at, 1, 10)) = ?
        """,
        (today_str,),
    )
    row = cur.fetchone()
    today_sales = row["today_sales"] if row else 0

    # 2) Total outstanding (udhar)
    cur.execute("SELECT COALESCE(SUM(due), 0) AS total_outstanding FROM customers")
    row = cur.fetchone()
    total_outstanding = row["total_outstanding"] if row else 0

    # 3) Number of bills today
    cur.execute(
        """
        SELECT COUNT(*) AS bills_today
        FROM bills
        WHERE DATE(substr(created_at, 1, 10)) = ?
        """,
        (today_str,),
    )
    row = cur.fetchone()
    bills_today = row["bills_today"] if row else 0

    # 4) Low stock products (<= 10 units, top 5)
    LOW_STOCK_LIMIT = 10
    cur.execute(
        """
        SELECT name, stock, unit
        FROM products
        WHERE stock <= ?
        ORDER BY stock ASC
        LIMIT 5
        """,
        (LOW_STOCK_LIMIT,),
    )
    low_stock = cur.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        show_nav=True,
        today_sales=today_sales,
        total_outstanding=total_outstanding,  # you can rename label in HTML
        bills_today=bills_today,
        low_stock=low_stock,
    )


if __name__ == "__main__":
    app.run(debug=True)