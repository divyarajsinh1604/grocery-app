from flask import Blueprint, render_template, request, redirect, session
from werkzeug.security import check_password_hash
from models import get_db

auth = Blueprint("auth", __name__)

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            return redirect("/")

        # Wrong login → show same page with error message
        return render_template("login.html", error="Invalid username or password")

    # First time GET → just show empty form
    return render_template("login.html")


@auth.route("/logout")
def logout():
    session.clear()
    return redirect("/login")