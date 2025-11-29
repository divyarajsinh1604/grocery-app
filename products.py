from flask import Blueprint, render_template, request, redirect
from models import get_db

# Available units for products
UNITS = ["kg", "g", "L", "ml", "pcs", "pack", "box"]

# Blueprint for all product-related routes
products = Blueprint("products", __name__)

@products.route("/products", methods=["GET", "POST"])
def products_page():
    """
    /products:
    - GET  -> show list of products
    - POST -> add a new product
    """
    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        # Read data from the form
        name = (request.form.get("name") or "").strip()
        cost_price = (request.form.get("cost_price") or "0").strip()
        sell_price = (request.form.get("sell_price") or "0").strip()
        stock = (request.form.get("stock") or "0").strip()
        unit = (request.form.get("unit") or "pcs").strip()

        if name:
            cur.execute(
                """
                INSERT INTO products (name, cost_price, sell_price, stock, unit)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, float(cost_price), float(sell_price), int(stock), unit),
            )
            conn.commit()

    # Fetch all products for listing
    cur.execute("SELECT * FROM products")
    items = cur.fetchall()
    conn.close()

    # Send 'items' list to products.html as 'products'
    return render_template(
        "products.html",
        products=items,
        units=UNITS,
        show_nav=True
    )


@products.route("/products/<int:product_id>/delete", methods=["POST"])
def delete_product(product_id):
    conn = get_db()
    cur = conn.cursor()

    # delete the row with this id
    cur.execute("DELETE FROM products WHERE id = ?", (product_id,))

    conn.commit()
    conn.close()

    # go back to products page
    return redirect("/products")


@products.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
def edit_product(product_id):
    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        name = request.form.get("name")
        cost_price = float(request.form.get("cost_price"))
        sell_price = float(request.form.get("sell_price"))
        stock = int(request.form.get("stock"))
        unit = request.form.get("unit")  # 👈 READ UNIT

        cur.execute(
            """
            UPDATE products
            SET name = ?, cost_price = ?, sell_price = ?, stock = ?, unit = ?
            WHERE id = ?
            """,
            (name, cost_price, sell_price, stock, unit, product_id),
        )
        conn.commit()
        conn.close()
        return redirect("/products")

    cur.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cur.fetchone()
    conn.close()

    return render_template("edit_product.html", product=product, show_nav=True)