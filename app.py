from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3
import random

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Secret key for session management

DATABASE = "database.db"

# Configure session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

# Function to connect to the database
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

# Initialize Database
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)"""
        )
        db.commit()

init_db()

# Home route (Login page)
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()

        if user:
            session["username"] = username  # Store username in session
            return redirect(url_for("game"))
        else:
            return render_template("login.html", error="Invalid username or password!")
    
    return render_template("login.html")

# Signup route
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            db.commit()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return render_template("signup.html", error="Username already exists!")

    return render_template("signup.html")

# Game route (requires login)
@app.route("/game", methods=["GET", "POST"])
def game():
    if "username" not in session:
        return redirect(url_for("login"))

    if "target_number" not in session:
        session["target_number"] = random.randint(1, 100)
        session["attempts"] = 0

    message = ""
    if request.method == "POST":
        guess = int(request.form["guess"])
        session["attempts"] += 1

        if guess < session["target_number"]:
            message = "Too low! Try again."
        elif guess > session["target_number"]:
            message = "Too high! Try again."
        else:
            return redirect(url_for("result"))

    return render_template("game.html", message=message, attempts=session["attempts"])

# Result page
@app.route("/result")
def result():
    if "username" not in session:
        return redirect(url_for("login"))

    target_number = session.pop("target_number", None)
    attempts = session.pop("attempts", None)

    return render_template("result.html", number=target_number, attempts=attempts)

# Logout route
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# Close database connection
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

if __name__ == "__main__":
    app.run(debug=True)
