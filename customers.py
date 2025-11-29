from flask import Blueprint, render_template, request, redirect
from models import get_db

customers_bp = Blueprint("customers", __name__)


# MAIN PAGE
@customers_bp.route("/customers", methods=["GET", "POST"])
def customers_page():
    conn = get_db()
    cur = conn.cursor()

    # Add new customer
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if name:
            cur.execute(
                "INSERT INTO customers (name, due, next_payment_date) VALUES (?, ?, ?)",
                (name, 0.0, None)
            )
            conn.commit()

    # Load all customers
    cur.execute("SELECT * FROM customers ORDER BY id DESC")
    customers = cur.fetchall()

    conn.close()
    return render_template("customers.html", customers=customers, show_nav=True)


# PARTIAL PAYMENT
@customers_bp.route("/customers/<int:cid>/pay", methods=["POST"])
def pay_partial(cid):
    amount_raw = request.form.get("amount")

    try:
        amount = float(amount_raw)
    except:
        return redirect("/customers")

    conn = get_db()
    cur = conn.cursor()

    # reduce due
    cur.execute("UPDATE customers SET due = due - ? WHERE id = ?", (amount, cid))
    conn.commit()
    conn.close()

    return redirect("/customers")


# FULL PAYMENT
@customers_bp.route("/customers/<int:cid>/pay_full", methods=["POST"])
def pay_full(cid):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("UPDATE customers SET due = 0 WHERE id = ?", (cid,))
    conn.commit()
    conn.close()

    return redirect("/customers")


# DELETE CUSTOMER
@customers_bp.route("/customers/<int:cid>/delete", methods=["POST"])
def delete_customer(cid):
    conn = get_db()
    cur = conn.cursor()

    # check dues
    cur.execute("SELECT due FROM customers WHERE id = ?", (cid,))
    row = cur.fetchone()

    if not row:
        conn.close()
        return redirect("/customers")

    # If still has due — DO NOT DELETE
    if row["due"] > 0:
        conn.close()
        return redirect("/customers")

    # delete
    cur.execute("DELETE FROM customers WHERE id = ?", (cid,))
    conn.commit()
    conn.close()

    return redirect("/customers")