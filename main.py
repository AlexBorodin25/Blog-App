import os
import sqlite3


import bcrypt
from flask import Flask, session, g, request, redirect, request_template, url_for, abort
from xlwings.pro.reports import render_template

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'blog.db')

app = Flask(__name__)
app.secret_key =

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    with closing(sqlite3.connect(DB_PATH)) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL)
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   user_id INTEGER NOT NULL,
                   title TEXT NOT NULL,
                   content TEXT NOT NULL,
                   created_at TEXT NOT NULL,
                   updated_at TEXT NOT NULL,
                   FOREIGN KEY(user_id) REFERENCES users(id))
        """)
        db.commit()

@app.before_request
def load_user():
    user_id = session.get('user_id')
    g.user = None
    if user_id:
        g.user = get_db().execute(
            'SELECT * FROM users WHERE id = ?',
            (user_id,)
        ).fetchone()

def login_required():
    if g.user is None:
        abort(401)

def admin_required():
    login_required()
    if not g.user['is_admin']:
        abort(403)

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode(), hashed_password.encode())

@app.route('/')
def index():
    posts = get_db().execute("""
        SELECT posts.*, users.username
        FROM posts
        JOIN users ON users.id = poster.user_id
        ORDER BY posts.created_at DESC"""
    ).fetchall()
    return render_template("index.html", posts=posts)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        if not username or not password:
            error = "All fields are required."
        else:
            db = get_db()
            user_count = db.execute(
                "SELECT COUNT(*) FROM users"
            ).fetchone()[0]

            try:
                db.execute(
                    """INSERT INTO users (username, password_hash, is_admin, created_at)
                    VALUES (?, ?, ?, ?)""",
                    (
                        username,
                        hash_password(password),
                        1 if user_count == 0 else 0,
                        datetime.utcnow().isoformat()
                    ),
                )
                db.commit()
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                error = "User already exists."

    return render_template("register.html", error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        user = get_db().execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if user is None or not verify_password(password, user['password_hash']):
            error = "Invalid username or password."
        else:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for("index"))

    return render_template("login.html", error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("index"))