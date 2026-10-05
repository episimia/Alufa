import os
from functools import wraps
from flask import (
    Flask, request, jsonify, send_from_directory,
    session, redirect, url_for
)
import psycopg

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]

VIEWER_PASSWORD = os.environ["VIEWER_PASSWORD"]
DATABASE_URL = os.environ["DATABASE_URL"]


def get_db():
    return psycopg.connect(DATABASE_URL)


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS locations (
                id BIGSERIAL PRIMARY KEY,
                latitude DOUBLE PRECISION NOT NULL,
                longitude DOUBLE PRECISION NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        conn.commit()


# アプリ起動時にテーブルを作る
init_db()


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
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "データがありません"}), 400

    try:
        latitude = float(data.get("latitude"))
        longitude = float(data.get("longitude"))
    except (TypeError, ValueError):
        return jsonify({"error": "座標が不正です"}), 400

    # 座標の範囲をチェック
    if not (-90 <= latitude <= 90):
        return jsonify({"error": "緯度が不正です"}), 400

    if not (-180 <= longitude <= 180):
        return jsonify({"error": "経度が不正です"}), 400

    with get_db() as conn:

        # 3日より古いデータを削除
        conn.execute("""
            DELETE FROM locations
            WHERE created_at < NOW() - INTERVAL '3 days'
        """)

        # 新しい位置情報を保存
        conn.execute("""
            INSERT INTO locations
                (latitude, longitude)
            VALUES
                (%s, %s)
        """, (latitude, longitude))

        conn.commit()

    return jsonify({"ok": True})


@app.get("/location")
@login_required
def get_location():

    with get_db() as conn:

        # 3日より古いデータを削除
        conn.execute("""
            DELETE FROM locations
            WHERE created_at < NOW() - INTERVAL '3 days'
        """)

        # 残っている位置情報を全部取得
        rows = conn.execute("""
            SELECT
                latitude,
                longitude,
                created_at
            FROM locations
            ORDER BY created_at DESC
        """).fetchall()

        conn.commit()

    locations = []

    for row in rows:
        locations.append({
            "latitude": row[0],
            "longitude": row[1],
            "created_at": row[2].isoformat()
        })

    return jsonify(locations)


if __name__ == "__main__":
    app.run()
