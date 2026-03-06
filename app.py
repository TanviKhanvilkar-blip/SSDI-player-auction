import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"

DATABASE = "database.db"


# -------------------------------
# DATABASE CONNECTION
# -------------------------------
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# -------------------------------
# CREATE TABLES IF NOT EXIST
# -------------------------------
def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS players(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        team TEXT,
        role TEXT,
        strike_rate REAL,
        price INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS bids(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        player_id INTEGER,
        bid_price INTEGER
    )
    """)

    conn.commit()
    conn.close()


init_db()


# -------------------------------
# HOME PAGE
# -------------------------------
@app.route("/")
def home():

    search = request.args.get("search")
    team = request.args.get("team")
    role = request.args.get("role")
    min_sr = request.args.get("min_sr")
    max_sr = request.args.get("max_sr")

    query = "SELECT * FROM players WHERE 1=1"
    params = []

    if search:
        query += " AND name LIKE ?"
        params.append(f"%{search}%")

    if team:
        query += " AND team=?"
        params.append(team)

    if role:
        query += " AND role=?"
        params.append(role)

    if min_sr:
        query += " AND strike_rate >= ?"
        params.append(min_sr)

    if max_sr:
        query += " AND strike_rate <= ?"
        params.append(max_sr)

    conn = get_db()
    players = conn.execute(query, params).fetchall()
    conn.close()

    return render_template("index.html", players=players)


# -------------------------------
# SIGNUP
# -------------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = get_db()
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO users(username,password) VALUES (?,?)",
                (username, password)
            )
            conn.commit()
            flash("Account created successfully")
            return redirect("/login")

        except:
            flash("Username already exists")

        finally:
            conn.close()

    return render_template("signup.html")


# -------------------------------
# LOGIN
# -------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            return redirect("/")
        else:
            flash("Invalid credentials")

    return render_template("login.html")


# -------------------------------
# LOGOUT
# -------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# -------------------------------
# BID SYSTEM
# -------------------------------
@app.route("/bid/<int:player_id>", methods=["POST"])
def bid(player_id):

    if "user_id" not in session:
        flash("Login required to bid")
        return redirect("/login")

    bid_price = int(request.form["bid_price"])
    user_id = session["user_id"]

    conn = get_db()
    player = conn.execute(
        "SELECT * FROM players WHERE id=?",
        (player_id,)
    ).fetchone()

    if bid_price <= player["price"]:
        flash("Bid must be higher than current price")
        conn.close()
        return redirect("/")

    conn.execute(
        "UPDATE players SET price=? WHERE id=?",
        (bid_price, player_id)
    )

    conn.execute(
        "INSERT INTO bids(user_id,player_id,bid_price) VALUES (?,?,?)",
        (user_id, player_id, bid_price)
    )

    conn.commit()
    conn.close()

    flash("Bid placed successfully")
    return redirect("/")


# -------------------------------
# API SEARCH (optional for JS)
# -------------------------------
@app.route("/api/players")
def api_players():

    conn = get_db()
    players = conn.execute("SELECT * FROM players").fetchall()
    conn.close()

    return jsonify([dict(p) for p in players])


# -------------------------------
# RUN APP
# -------------------------------
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )
