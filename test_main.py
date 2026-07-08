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