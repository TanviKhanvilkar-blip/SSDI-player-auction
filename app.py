import os
import psycopg2
from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "auction_secret_key"

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_db():
    return psycopg2.connect(DATABASE_URL)


# -----------------------------
# DATABASE SETUP
# -----------------------------
def init_db():
    conn = get_db()
    cur = conn.cursor()

    # users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    # players table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS players(
        id SERIAL PRIMARY KEY,
        name TEXT,
        team TEXT,
        role TEXT,
        strike_rate FLOAT,
        price INTEGER
    )
    """)

    conn.commit()
    conn.close()


# -----------------------------
# SEED PLAYERS
# -----------------------------
def seed_players():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM players")
    count = cur.fetchone()[0]

    if count == 0:
        players = [
            ("Virat Kohli", "RCB", "Batsman", 138.2, 2000000),
            ("Rohit Sharma", "MI", "Batsman", 131.4, 1800000),
            ("MS Dhoni", "CSK", "Wicketkeeper", 135.5, 1500000),
            ("Hardik Pandya", "MI", "All-Rounder", 145.0, 1700000),
            ("Jasprit Bumrah", "MI", "Bowler", 90.0, 1600000),
            ("KL Rahul", "LSG", "Wicketkeeper", 134.3, 1500000),
            ("Rishabh Pant", "DC", "Wicketkeeper", 148.6, 1700000),
            ("Shubman Gill", "GT", "Batsman", 136.7, 1500000),
            ("Ravindra Jadeja", "CSK", "All-Rounder", 130.5, 1600000),
            ("Mohammed Shami", "GT", "Bowler", 85.2, 1400000),
            ("Suryakumar Yadav", "MI", "Batsman", 150.1, 1800000),
            ("Jos Buttler", "RR", "Wicketkeeper", 149.0, 1750000),
            ("Andre Russell", "KKR", "All-Rounder", 174.0, 1900000),
            ("Rashid Khan", "GT", "Bowler", 120.0, 1850000),
            ("David Warner", "DC", "Batsman", 140.3, 1600000)
        ]

        cur.executemany(
            "INSERT INTO players(name,team,role,strike_rate,price) VALUES (%s,%s,%s,%s,%s)",
            players
        )

        conn.commit()

    conn.close()


init_db()
seed_players()


# -----------------------------
# LOGIN REQUIRED
# -----------------------------
def login_required():
    if "user" not in session:
        return redirect("/login")


# -----------------------------
# HOME PAGE
# -----------------------------
@app.route("/")
def home():

    if "user" not in session:
        return redirect("/login")

    search = request.args.get("search", "")
    team = request.args.get("team", "")
    role = request.args.get("role", "")
    sr_min = request.args.get("sr_min", 0)
    sr_max = request.args.get("sr_max", 1000)

    conn = get_db()
    cur = conn.cursor()

    query = """
    SELECT * FROM players
    WHERE name ILIKE %s
    AND team ILIKE %s
    AND role ILIKE %s
    AND strike_rate BETWEEN %s AND %s
    ORDER BY name
    """

    cur.execute(
        query,
        (f"%{search}%", f"%{team}%", f"%{role}%", sr_min, sr_max)
    )

    players = cur.fetchall()

    conn.close()

    return render_template("index.html", players=players)


# -----------------------------
# BID
# -----------------------------
@app.route("/bid/<int:player_id>", methods=["POST"])
def bid(player_id):

    if "user" not in session:
        return redirect("/login")

    new_price = int(request.form["price"])

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT price FROM players WHERE id=%s", (player_id,))
    current_price = cur.fetchone()[0]

    if new_price > current_price:

        cur.execute(
            "UPDATE players SET price=%s WHERE id=%s",
            (new_price, player_id)
        )

        conn.commit()

    conn.close()

    return redirect("/")


# -----------------------------
# SIGNUP
# -----------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = get_db()
        cur = conn.cursor()

        try:

            cur.execute(
                "INSERT INTO users(username,password) VALUES(%s,%s)",
                (username, password)
            )

            conn.commit()

        except:
            conn.close()
            return "User already exists"

        conn.close()

        return redirect("/login")

    return render_template("signup.html")


# -----------------------------
# LOGIN
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "SELECT password FROM users WHERE username=%s",
            (username,)
        )

        user = cur.fetchone()

        conn.close()

        if user and check_password_hash(user[0], password):

            session["user"] = username

            return redirect("/")

        return "Invalid login"

    return render_template("login.html")


# -----------------------------
# LOGOUT
# -----------------------------
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(host="0.0.0.0", port=port)
