"""
Implement a website via which users can `buy` and `sell` stocks
"""
import os
import random
import string

import sqlite3
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, abort
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from notion_client import Client as NotionClient

from helpers import apology, login_required, get_notion_database

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///notion.db")

# # Make sure API key is set
# if not os.environ.get("API_KEY"):
#     raise RuntimeError("API_KEY not set")


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Create a widget"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not (notion_token := request.form.get("notion-token")):
            return apology("must provide notion token")

        # Ensure password was submitted
        elif not (database_url := request.form.get("database-url")):
            return apology("must provide database id")
        
        widget_id = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(8)])

        while db.execute("SELECT * FROM widgets WHERE widget_id = ?", widget_id):
            widget_id = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(8)])

        # Insert user credentials into database
        db.execute(
            """
            INSERT INTO widgets (widget_id, notion_token, database_url, username)
            VALUES (?, ?, ?, ?)
            """,
            widget_id,
            notion_token,
            database_url,
            db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])[0]["username"]
        )

        widget_url = request.host_url + "widget/" + widget_id

        # Redirect user to link
        return render_template("link.html", widget_url=widget_url)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("index.html")


def get_db():
    conn = sqlite3.connect("notion.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/widget/<widget_id>")
def show_widget(widget_id):
    db = get_db()
    widget = db.execute("SELECT * FROM widgets WHERE widget_id = ?", (widget_id,)).fetchone()
    if widget is None:
        abort(404)

    posts = get_notion_database(widget["notion_token"], widget["database_url"])
    return render_template("widget2.html", posts=posts)

print(app.url_map)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not (username := request.form.get("username")):
            return apology("must provide username")

        # Ensure password was submitted
        elif (
            not (password := request.form.get("password")) or
            not (confirmation := request.form.get("confirmation"))
        ):
            return apology("must provide password and confirmation")

        # Ensure passwords match
        elif password != confirmation:
            return apology("passwords must match")

        # Ensure username does not exist yet
        if db.execute(
            """
            SELECT username
            FROM users
            WHERE username == ?
            """,
            username
        ):
            return apology("username already exists")

        # Insert user credentials into database
        db.execute(
            """
            INSERT INTO users (username, hash)
            VALUES (?, ?)
            """,
            username,
            generate_password_hash(password)
        )

        # Remember which user has logged in
        session["user_id"] = db.execute(
            """
            SELECT id
            FROM users
            WHERE username == ?
            """,
            username
        )[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
