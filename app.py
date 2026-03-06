from flask import Flask, render_template, request, redirect, session
import psycopg2
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "auction_secret"

DATABASE_URL = os.environ.get("DATABASE_URL")

def db():
    return psycopg2.connect(DATABASE_URL)

def init_db():

    conn=db()
    cur=conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

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

    cur.execute("""
    CREATE TABLE IF NOT EXISTS bids(
        id SERIAL PRIMARY KEY,
        user_id INT,
        player_id INT,
        bid INT
    )
    """)

    cur.execute("SELECT COUNT(*) FROM players")
    count=cur.fetchone()[0]

    if count==0:

        players=[
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
            "INSERT INTO players(name,team,role,strike_rate,price) VALUES(%s,%s,%s,%s,%s)",p)

    conn.commit()
    cur.close()
    conn.close()

init_db()

@app.route("/")

def home():

    if "user" not in session:
        return redirect("/login")

    search=request.args.get("search","")
    team=request.args.get("team","")
    role=request.args.get("role","")
    sr_min=request.args.get("sr_min","0")
    sr_max=request.args.get("sr_max","1000")

    conn=db()
    cur=conn.cursor()

    query="""
    SELECT * FROM players
    WHERE name ILIKE %s
    AND team ILIKE %s
    AND role ILIKE %s
    AND strike_rate BETWEEN %s AND %s
    """

    cur.execute(query,
    (f"%{search}%",f"%{team}%",f"%{role}%",sr_min,sr_max))

    players=cur.fetchall()

    cur.close()
    conn.close()

    return render_template("index.html",players=players,user=session["user"])


@app.route("/bid/<id>",methods=["POST"])
def bid(id):

    if "user" not in session:
        return redirect("/login")

    new_bid=int(request.form["bid"])

    conn=db()
    cur=conn.cursor()

    cur.execute("SELECT price FROM players WHERE id=%s",(id,))
    current=cur.fetchone()[0]

    if new_bid>current:

        cur.execute(
        "UPDATE players SET price=%s WHERE id=%s",(new_bid,id))

        cur.execute(
        "INSERT INTO bids(user_id,player_id,bid) VALUES(%s,%s,%s)",
        (session["user_id"],id,new_bid))

        conn.commit()

    cur.close()
    conn.close()

    return redirect("/")


@app.route("/signup",methods=["GET","POST"])
def signup():

    if request.method=="POST":

        user=request.form["username"]
        pw=generate_password_hash(request.form["password"])

        conn=db()
        cur=conn.cursor()

        cur.execute(
        "INSERT INTO users(username,password) VALUES(%s,%s)",
        (user,pw))

        conn.commit()

        cur.close()
        conn.close()

        return redirect("/login")

    return render_template("signup.html")


@app.route("/login",methods=["GET","POST"])
def login():

    if request.method=="POST":

        user=request.form["username"]
        pw=request.form["password"]

        conn=db()
        cur=conn.cursor()

        cur.execute("SELECT * FROM users WHERE username=%s",(user,))
        data=cur.fetchone()

        cur.close()
        conn.close()

        if data and check_password_hash(data[2],pw):

            session["user"]=user
            session["user_id"]=data[0]

            return redirect("/")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
