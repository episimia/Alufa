
import os
from functools import wraps
from flask import (
    Flask, request, jsonify, send_from_directory,
    session, redirect, url_for
)

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]

VIEWER_PASSWORD = os.environ["VIEWER_PASSWORD"]
latest_location = None

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == VIEWER_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("parent"))
        error = "パスワードが違います"

    return f"""
    <!DOCTYPE html>
    <html lang="ja">
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>ログイン</title>
    <h2>閲覧ページのログイン</h2>
    <p>{error}</p>
    <form method="post">
      <input type="password" name="password"
             placeholder="パスワード" required>
      <button type="submit">ログイン</button>
    </form>
    </html>
    """

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/parent.html")
@login_required
def parent():
    return send_from_directory(".", "parent.html")

@app.post("/location")
def receive_location():
    # まだ実際の位置情報は送らず、ダミーでテストする
    global latest_location
    data = request.get_json()
    if not data:
        return jsonify({"error": "データがありません"}), 400

    latest_location = {
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude")
    }
    return jsonify({"ok": True})

@app.get("/location")
@login_required
def get_location():
    return jsonify(latest_location)
