from flask import Blueprint, render_template, request, redirect
from models import get_db

# blueprint object
customers_bp = Blueprint("customers", __name__)


@customers_bp.route("/customers", methods=["GET", "POST"])
def customers_page():
    """
    GET  -> show customers list
    POST -> add new customer
    """
    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()

        if name:
            cur.execute(
                """
                INSERT INTO customers (name, due, next_payment_date)
                VALUES (?, ?, ?)
                """,
                (name, 0.0, None),
            )
            conn.commit()

    cur.execute("SELECT * FROM customers")
    customers = cur.fetchall()
    conn.close()

    return render_template(
        "customers.html",
        customers=customers,
        show_nav=True,
    )


@customers_bp.route("/customers/<int:customer_id>/pay", methods=["POST"])
def pay_partial(customer_id):
    amount_raw = request.form.get("amount") or "0"
    try:
        amount = float(amount_raw)
    except ValueError:
        amount = 0.0

    if amount <= 0:
        return redirect("/customers")

    conn = get_db()
    cur = conn.cursor()

    # reduce due but not below 0
    cur.execute("SELECT due FROM customers WHERE id = ?", (customer_id,))
    row = cur.fetchone()
    if row:
        current_due = row["due"]
        new_due = max(current_due - amount, 0)
        cur.execute(
            "UPDATE customers SET due = ? WHERE id = ?",
            (new_due, customer_id),
        )
        conn.commit()

    conn.close()
    return redirect("/customers")


@customers_bp.route("/customers/<int:customer_id>/pay_full", methods=["POST"])
def pay_full(customer_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE customers SET due = 0 WHERE id = ?",
        (customer_id,),
    )
    conn.commit()
    conn.close()
    return redirect("/customers")


@customers_bp.route("/customers/<int:customer_id>/delete", methods=["POST"])
def delete_customer(customer_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
    conn.commit()
    conn.close()
    return redirect("/customers")