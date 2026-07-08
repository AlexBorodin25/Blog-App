import os
import sqlite3

import pytest

os.environ.setdefault("FLASK_SECRET_KEY", "test-secret-key")

import main

@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "test_blog.db"

    monkeypatch.setattr(main, "DB_PATH", str(test_db))
    monkeypatch.setattr(main, "render_template", lambda name, **ctx: name)

    main.app.config.update(
        TESTING = True,
        WTF_CSRF_ENABLED=False,
        SECRET_KEY = "test-secret-key",
    )

    main.init_db()

    with main.app.test_client() as test_client:
        yield test_client

def add_user(username="testing", password="password", is_admin=0):
    db = main.get_db()
    db.execute(
        """
        INSERT INTO users (username, password_hash, is_admin, created_at)
        VALUES (?, ?, ?, datetime('now'))
        """,
        (username, main.hash_password(password), is_admin),
    )
    db.commit()

    return db.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,),
    ).fetchone()

def add_post(user_id, title="Title", content="Content"):
    db = main.get_db()
    cursor = db.execute(
        """
        INSERT INTO posts (user_id, title, content, created_at, updated_at)
        VALUES (?, ?, ?, datetime('now'), datetime('now'))
        """,
        (user_id, title, content),
    )
    db.commit()

    return cursor.lastrowid

def add_comment(post_id, user_id, content="Comment"):
    db = main.get_db()
    cursor = db.execute(
        """
        INSERT INTO comments (post_id, user_id, content, created_at, updated_at)
        VALUES (?, ?, ?, datetime('now'), datetime('now'))
        """,
        (post_id, user_id, content),
    )
    db.commit()

    return cursor.lastrowid