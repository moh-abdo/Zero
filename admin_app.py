import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
import db_service
from werkzeug.security import generate_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-me")

# Simple login_required decorator for admin routes
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if db_service.check_admin_credentials(username, password):
            session["admin_logged_in"] = True
            session["admin_username"] = username
            flash("Logged in successfully.", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid credentials.", "danger")
    return render_template("admin_login.html")

@app.route("/admin/logout")
@login_required
def admin_logout():
    session.pop("admin_logged_in", None)
    session.pop("admin_username", None)
    flash("Logged out.", "info")
    return redirect(url_for("admin_login"))

@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    users_count = db_service.count_users()
    receipts_count = db_service.count_receipts()
    recent_users = db_service.get_users(limit=10)
    recent_receipts = db_service.get_receipts(limit=10)
    return render_template("dashboard.html", users_count=users_count, receipts_count=receipts_count,
                           recent_users=recent_users, recent_receipts=recent_receipts)

@app.route("/admin/users")
@login_required
def admin_users():
    users = db_service.get_users()
    return render_template("users.html", users=users)

@app.route("/admin/receipts")
@login_required
def admin_receipts():
    receipts = db_service.get_receipts()
    return render_template("receipts.html", receipts=receipts)

# CLI helpers to initialize DB and create admin from environment variables
@app.cli.command("init-db")
def init_db_command():
    """Initialize the database."""
    db_service.init_db()
    print("Initialized the database.")

@app.cli.command("create-admin-from-env")
def create_admin_from_env():
    """Create an admin user using ADMIN_USERNAME and ADMIN_PASSWORD from environment."""
    username = os.getenv("ADMIN_USERNAME")
    password = os.getenv("ADMIN_PASSWORD")
    if not username or not password:
        print("Set ADMIN_USERNAME and ADMIN_PASSWORD in environment before running this command.")
        return
    try:
        db_service.create_admin(username, password)
        print(f"Admin user '{username}' created (or already exists).")
    except Exception as e:
        print("Failed to create admin:", e)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=os.getenv("FLASK_DEBUG", "0") == "1")
