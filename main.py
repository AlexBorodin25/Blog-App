import os
import sqlite3
from calendar import c

import bcrypt
from flask import Flask

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'blog.db')

app = Flask(__name__)
app.secret_key =

def get_db():
    if "db" not in a:
        a.db = sqlite3.connect(DB_PATH)
        a.db.row_factory = sqlite3.Row
    return a.db

@app.teardown_appcontext
def close_db(error=None):
    db = a.pop('db', None)
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