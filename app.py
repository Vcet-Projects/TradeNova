import os
import sqlite3

from flask import Flask, flash, redirect, render_template, request, session,url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd,DB

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# db = SQL("sqlite:///finance.db")
db =DB(path="finance.db")



@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    bought=request.args.get("bought")
    wallet = db.execute(
        "select symbol,shares from shares where user_id is ? and shares>0;", session.get("user_id"))
    for share in wallet:
        stock = lookup(share["symbol"])
        share["price"] = stock["price"]
        share["total"] = share["price"]*share["shares"]
    cash = db.execute("SELECT cash FROM users WHERE id = ?", session.get("user_id"))[
        0]["cash"]
    total = sum(share["total"] for share in wallet)+cash
    return render_template("index.html", wallet=wallet, cash=cash, total=total,bought=bought)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")

    user_id = session.get("user_id")
    symbol = request.form.get("symbol")
    stock = lookup(symbol)
    if not stock:
        return apology("INVALID SYMBOL")
    symbol = stock.get("symbol")
    shares = request.form.get("shares")
    try:
        shares = int(shares)
        assert shares > 0
    except (ValueError, AssertionError):
        return apology("INVALID SHARES")
    cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[
        0]["cash"]
    cost = stock["price"]*shares
    if cash < cost:
        return apology("OUT OF BALANCE")
    db.execute("INSERT INTO transactions (user_id, symbol, shares, price) VALUES (?, ?, ?, ?);",
               user_id, stock["symbol"], shares, stock["price"])

    if not db.execute("Select * from shares where user_id=? and symbol = ?;", user_id, symbol):
        # crete entry if not already
        db.execute("Insert into shares (user_id,symbol) values (?,?);",
                   user_id, symbol)
    db.execute("update shares set shares=shares+? where user_id=? and symbol= ?;",
               shares, user_id, symbol)
    db.execute("UPDATE users SET cash= cash - ?  WHERE id= ?", cost, user_id)

    return redirect(url_for("index", bought=True))


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    history = db.execute(
        "select id,symbol,shares,price,log_time from transactions where user_id=?;", session["user_id"])
    return render_template("history.html", history=history)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get(
                "username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        stock = lookup(symbol)
        if not stock:
            return apology("INVALID SYMBOL")
        return render_template("quoted.html", stock=stock)
    return render_template("quote.html")


@app.route("/quote/<symbol>")
@login_required
def quote_symbol(symbol):
    stock = lookup(symbol)
    if not stock:
        return apology("INVALID SYMBOL")
    return render_template("quoted.html", stock=stock)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        if not username:
            return apology("Input is blank")
        if not request.form.get("password") or request.form.get("password") != request.form.get("confirmation"):
            return apology("Input is blank or the passwords do not match")
        hash = generate_password_hash(request.form.get("password"))
        try:
            db.execute("INSERT INTO users(username,hash) VALUES(?,?)",
                       username, hash)
        except ValueError:
            return apology("User already exists.")
        return redirect("/login")
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    if request.method == "GET":
        symbols = [sym["symbol"] for sym in db.execute(
            "Select symbol from shares where user_id=? and shares>0 order by symbol;", session["user_id"])]
        return render_template("sell.html", symbols=symbols)

    symbol = request.form.get("symbol")
    stock = lookup(symbol)
    if not stock:
        return apology("INVALID SYMBOL")
    shares = request.form.get("shares")
    try:
        shares = int(shares)
        assert shares > 0
    except (ValueError, AssertionError):
        return apology("INVALID SHARES")
    avail_shares = db.execute(
        "select shares from shares where user_id=? and symbol=?;", session["user_id"], stock["symbol"])[0]["shares"]
    if avail_shares < shares:
        return apology("You dont have enough shares!")
    cost = shares*stock["price"]
    db.execute("INSERT INTO transactions (user_id, symbol, shares, price) VALUES (?, ?, ?, ?);",
               session["user_id"], stock["symbol"], -shares, stock["price"])
    db.execute("update shares set shares=shares-? where user_id=? and symbol= ?;",
               shares, session["user_id"], stock.get("symbol"))
    db.execute("update users set cash=cash+? where id=?;",
               cost, session["user_id"])
    return redirect("/")
