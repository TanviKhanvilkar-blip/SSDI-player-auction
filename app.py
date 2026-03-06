from flask import Flask, render_template, request, redirect
import psycopg2
import os

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS players(
        id SERIAL PRIMARY KEY,
        name TEXT,
        strike_rate FLOAT,
        average FLOAT,
        price INTEGER
    )
    """)

    cur.execute("SELECT COUNT(*) FROM players")
    count = cur.fetchone()[0]

    if count == 0:
        players = [
            ("Virat Kohli",138.1,52.7,2000000),
            ("Rohit Sharma",140.2,48.3,1800000),
            ("Hardik Pandya",152.4,34.1,1500000),
            ("KL Rahul",134.9,45.2,1400000),
            ("Rishabh Pant",148.2,38.4,1600000),
            ("Shubman Gill",142.6,44.9,1300000)
        ]

        for p in players:
            cur.execute(
                "INSERT INTO players (name,strike_rate,average,price) VALUES (%s,%s,%s,%s)",
                p
            )

    conn.commit()
    cur.close()
    conn.close()


@app.route("/")
def index():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM players ORDER BY name")
    players = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("index.html", players=players)


@app.route("/player/<int:id>")
def player(id):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM players WHERE id=%s",(id,))
    player = cur.fetchone()

    cur.close()
    conn.close()

    return render_template("player.html", player=player)


@app.route("/bid/<int:id>", methods=["POST"])
def bid(id):

    new_bid = int(request.form["bid"])

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT price FROM players WHERE id=%s",(id,))
    current = cur.fetchone()[0]

    if new_bid > current:
        cur.execute(
            "UPDATE players SET price=%s WHERE id=%s",
            (new_bid,id)
        )
        conn.commit()

    cur.close()
    conn.close()

    return redirect(f"/player/{id}")


if __name__ == "__main__":
    init_db()
    app.run()
