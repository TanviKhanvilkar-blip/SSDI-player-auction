from flask import Flask, render_template, request, jsonify
import psycopg2
import os

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS players (
        id SERIAL PRIMARY KEY,
        name TEXT,
        strike_rate FLOAT,
        batting_avg FLOAT,
        base_price INT,
        current_bid INT
    )
    """)

    conn.commit()

    # insert players if table empty
    cur.execute("SELECT COUNT(*) FROM players")
    count = cur.fetchone()[0]

    if count == 0:
        players = [
            ("Virat Kohli", 138.15, 52.7, 2000000, 2000000),
            ("Rohit Sharma", 140.2, 48.3, 1800000, 1800000),
            ("Hardik Pandya", 152.4, 34.1, 1500000, 1500000),
            ("KL Rahul", 134.9, 45.2, 1400000, 1400000),
            ("Rishabh Pant", 148.2, 38.4, 1600000, 1600000),
            ("Shubman Gill", 142.6, 44.9, 1300000, 1300000)
        ]

        for p in players:
            cur.execute(
                "INSERT INTO players (name,strike_rate,batting_avg,base_price,current_bid) VALUES (%s,%s,%s,%s,%s)",
                p
            )

        conn.commit()

    cur.close()
    conn.close()


@app.route("/")
def index():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM players ORDER BY current_bid DESC")
    players = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("index.html", players=players)


@app.route("/bid", methods=["POST"])
def bid():

    player_id = request.form["player_id"]
    new_bid = int(request.form["bid"])

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT current_bid FROM players WHERE id=%s", (player_id,))
    current_bid = cur.fetchone()[0]

    if new_bid <= current_bid:
        return jsonify({"status": "error", "message": "Bid must be higher than current bid."})

    cur.execute(
        "UPDATE players SET current_bid=%s WHERE id=%s",
        (new_bid, player_id)
    )

    conn.commit()

    cur.close()
    conn.close()

    return jsonify({"status": "success"})


if __name__ == "__main__":
    init_db()
    app.run(debug=True)