from flask import Blueprint, render_template, request, redirect
from models import get_db
from datetime import datetime

billing = Blueprint("billing", __name__)


@billing.route("/billing", methods=["GET", "POST"])
def billing_page():
    conn = get_db()
    cur = conn.cursor()

    error = None

    if request.method == "POST":
        # 1. Customer + payment info
        customer_id_raw = request.form.get("customer_id")
        payment_type = request.form.get("payment_type", "cash")  # "cash" or "credit"
        due_date = request.form.get("due_date") or None          # string "YYYY-MM-DD" or None

        # for cash payments we ignore any date
        if payment_type != "credit":
            due_date = None

        if customer_id_raw in (None, "", "cash"):
            customer_id = None
        else:
            customer_id = int(customer_id_raw)

        # 2. Items from hidden inputs
        product_ids = request.form.getlist("product_id[]")
        quantities = request.form.getlist("quantity[]")
        prices = request.form.getlist("price[]")

        items = []
        total = 0.0

        for pid, qty, price in zip(product_ids, quantities, prices):
            pid = (pid or "").strip()
            qty = (qty or "").strip()
            price = (price or "").strip()

            if not pid:
                continue

            try:
                product_id = int(pid)
                quantity = int(float(qty)) if qty else 0
                price_val = float(price) if price else 0.0
            except ValueError:
                continue

            if quantity <= 0 or price_val <= 0:
                continue

            line_total = quantity * price_val
            total += line_total

            items.append({
                "product_id": product_id,
                "quantity": quantity,
                "price": price_val,
                "line_total": line_total,
            })

        if not items:
            error = "No valid items in bill."
        else:
            # 3. STOCK CHECK
            for item in items:
                cur.execute(
                    "SELECT name, stock FROM products WHERE id = ?",
                    (item["product_id"],)
                )
                row = cur.fetchone()
                if not row:
                    error = "Some product does not exist."
                    break

                name = row["name"]
                available = row["stock"]

                if item["quantity"] > available:
                    error = (
                        f"Not enough stock for '{name}'. "
                        f"Available: {available}, requested: {item['quantity']}."
                    )
                    break

        if error:
            # reload data and render form with error
            cur.execute("SELECT id, name FROM customers")
            customers = cur.fetchall()

            cur.execute("SELECT id, name, sell_price, unit FROM products")
            products = cur.fetchall()

            conn.close()
            return render_template(
                "billing.html",
                customers=customers,
                products=products,
                error=error,
                show_nav=True,
            )

        # 4. Insert bill
        created_at = datetime.now().isoformat(timespec="seconds")
        cur.execute(
            """
            INSERT INTO bills (customer_id, total, payment_type, due_date, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (customer_id, total, payment_type, due_date, created_at),
        )
        bill_id = cur.lastrowid

        # 5. Insert items + update stock
        for item in items:
            cur.execute(
                """
                INSERT INTO bill_items (bill_id, product_id, quantity, price, line_total)
                VALUES (?, ?, ?, ?, ?)
                """,
                (bill_id, item["product_id"], item["quantity"],
                 item["price"], item["line_total"]),
            )

            cur.execute(
                "UPDATE products SET stock = stock - ? WHERE id = ?",
                (item["quantity"], item["product_id"]),
            )

        # 6. Update customer due + next_payment_date for CREDIT only
        if payment_type == "credit" and customer_id is not None:
            cur.execute(
                """
                UPDATE customers
                SET due = due + ?, next_payment_date = ?
                WHERE id = ?
                """,
                (total, due_date, customer_id),
            )

        conn.commit()
        conn.close()

        # 7. Go to invoice page
        return redirect(f"/billing/{bill_id}")

    # ---------- GET: show empty billing form ----------
    cur.execute("SELECT id, name FROM customers")
    customers = cur.fetchall()

    cur.execute("SELECT id, name, sell_price, unit FROM products")
    products = cur.fetchall()

    conn.close()

    return render_template(
        "billing.html",
        customers=customers,
        products=products,
        error=None,
        show_nav=True,
    )


@billing.route("/billing/<int:bill_id>")
def invoice_page(bill_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM bills WHERE id = ?", (bill_id,))
    bill = cur.fetchone()

    if not bill:
        conn.close()
        return "Bill not found", 404

    customer = None
    if bill["customer_id"] is not None:
        cur.execute("SELECT * FROM customers WHERE id = ?", (bill["customer_id"],))
        customer = cur.fetchone()

    cur.execute(
        """
        SELECT bi.quantity, bi.price, bi.line_total, p.name, p.unit
        FROM bill_items bi
        JOIN products p ON bi.product_id = p.id
        WHERE bi.bill_id = ?
        """,
        (bill_id,),
    )
    items = cur.fetchall()

    conn.close()

    return render_template(
        "invoice.html",
        bill=bill,
        customer=customer,
        items=items,
        show_nav=True,
    )