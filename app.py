from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

latest_location = None


@app.route("/")
def home():
    return send_from_directory(".", "index.html")


@app.route("/parent.html")
def parent():
    return send_from_directory(".", "parent.html")


@app.post("/location")
def receive_location():
    global latest_location

    data = request.get_json()

    print("受信したデータ:", data)

    latest_location = {
        "latitude": data["latitude"],
        "longitude": data["longitude"]
    }

    return jsonify({"ok": True})


@app.get("/location")
def get_location():
    return jsonify(latest_location)