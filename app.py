from flask import Flask, render_template, request, redirect, session
import psycopg2
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "auction_secret_key"

DATABASE_URL = os.environ.get("DATABASE_URL")


# -------------------------
# DATABASE CONNECTION
# -------------------------
def get_db():
    return psycopg2.connect(DATABASE_URL)


# -------------------------
# INITIALIZE DATABASE
# -------------------------
def init_db():

    conn = get_db()
    cur = conn.cursor()

    # Users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    # Players table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS players(
        id SERIAL PRIMARY KEY,
        name TEXT,
        team TEXT,
        role TEXT,
        strike_rate FLOAT,
        price INT
    )
    """)

    # Bids table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bids(
        id SERIAL PRIMARY KEY,
        user_id INT,
        player_id INT,
        bid INT,
        bid_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Insert players if table empty
    cur.execute("SELECT COUNT(*) FROM players")
    count = cur.fetchone()[0]

    if count == 0:

        players = [
            ("Virat Kohli","RCB","Batsman",138.1,2000000),
            ("Rohit Sharma","MI","Batsman",140.2,1800000),
            ("Hardik Pandya","MI","All-Rounder",152.4,1500000),
            ("KL Rahul","LSG","Wicketkeeper",134.9,1400000),
            ("Rishabh Pant","DC","Wicketkeeper",148.2,1600000),
            ("Jasprit Bumrah","MI","Bowler",85.2,1700000),
            ("Shubman Gill","GT","Batsman",142.6,1300000)
        ]

        for p in players:
            cur.execute(
                "INSERT INTO players(name,team,role,strike_rate,price) VALUES(%s,%s,%s,%s,%s)",
                p
            )

    conn.commit()
    cur.close()
    conn.close()


# Run database setup
init_db()


# -------------------------
# LOGIN PAGE
# -------------------------
@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE username=%s",(username,))
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user and check_password_hash(user[2], password):

            session["user"] = user[1]
            session["user_id"] = user[0]

            return redirect("/")

    return render_template("login.html")


# -------------------------
# SIGNUP
# -------------------------
@app.route("/signup", methods=["GET","POST"])
def signup():

    if request.method == "POST":

        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users(username,password) VALUES(%s,%s)",
            (username,password)
        )

        conn.commit()

        cur.close()
        conn.close()

        return redirect("/login")

    return render_template("signup.html")


# -------------------------
# LOGOUT
# -------------------------
@app.route("/logout")
def logout():

    session.clear()
    return redirect("/login")


# -------------------------
# HOME PAGE (PLAYER CARDS)
# -------------------------
@app.route("/")
def home():

    if "user" not in session:
        return redirect("/login")

    search = request.args.get("search","")
    team = request.args.get("team","")
    role = request.args.get("role","")
    sr_min = request.args.get("sr_min","0")
    sr_max = request.args.get("sr_max","1000")

    conn = get_db()
    cur = conn.cursor()

    query = """
    SELECT * FROM players
    WHERE name ILIKE %s
    AND team ILIKE %s
    AND role ILIKE %s
    AND strike_rate BETWEEN %s AND %s
    ORDER BY price DESC
    """

    cur.execute(
        query,
        (f"%{search}%",f"%{team}%",f"%{role}%",sr_min,sr_max)
    )

    players = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "index.html",
        players=players,
        user=session["user"]
    )


# -------------------------
# BID SYSTEM
# -------------------------
@app.route("/bid/<int:player_id>", methods=["POST"])
def bid(player_id):

    if "user" not in session:
        return redirect("/login")

    new_bid = int(request.form["bid"])

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT price FROM players WHERE id=%s",(player_id,))
    current_price = cur.fetchone()[0]

    if new_bid > current_price:

        # Update player price
        cur.execute(
            "UPDATE players SET price=%s WHERE id=%s",
            (new_bid, player_id)
        )

        # Save bid record
        cur.execute(
            "INSERT INTO bids(user_id,player_id,bid) VALUES(%s,%s,%s)",
            (session["user_id"],player_id,new_bid)
        )

        conn.commit()

    cur.close()
    conn.close()

    return redirect("/")


# -------------------------
# PORT BINDING FOR RENDER
# -------------------------
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
