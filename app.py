from flask import Flask, request, jsonify
import numpy as np
import mysql.connector
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)

import os

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=os.environ.get("DB_PORT", "3306"),
        user=os.environ.get("DB_USERNAME", "root"),
        password=os.environ.get("DB_PASSWORD", "changeme"),
        database=os.environ.get("DB_NAME", "bloodbank_db")
    )

@app.route("/")
def hello():
    return "Blood bank AI service is alive!"

@app.route("/forecast", methods=["POST"])
def forecast():
    data = request.get_json()
    history = data.get("history", [])

    if len(history) == 0:
        return jsonify({"error": "history cannot be empty"}), 400

    window = history[-7:] if len(history) >= 7 else history
    predicted_demand = round(float(np.mean(window)), 2)

    return jsonify({
        "history_used": window,
        "predicted_next_period_demand": predicted_demand
    })

@app.route("/forecast/from-db", methods=["GET"])
def forecast_from_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Count donations per day, most recent 7 days that actually have data
    cursor.execute("""
        SELECT donation_date, COUNT(*) as count
        FROM donations
        GROUP BY donation_date
        ORDER BY donation_date DESC
        LIMIT 7
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if len(rows) == 0:
        return jsonify({"error": "no donation data found"}), 404

    # rows come back newest-first, reverse so it reads oldest to newest
    history = [row[1] for row in reversed(rows)]
    predicted_demand = round(float(np.mean(history)), 2)

    return jsonify({
        "history_used": history,
        "predicted_next_period_demand": predicted_demand
    })

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=debug_mode)