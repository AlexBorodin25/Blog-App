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

def login(client, username="testing", password="password"):
    return client.post("/login", data={"username": username, "password": password})

def test_database_and_password(client):
    with main.app.app_context():
        conn = main.get_db()
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()

    table_name = {table["name"] for table in tables}

    assert isinstance(conn, sqlite3.Connection)
    assert conn.row_factory == sqlite3.Row
    assert {"users", "posts", "comments"}.issubset(table_name)

    hashed_password = main.hash_password("secret")

    assert hashed_password != "secret"
    assert main.verify_password("secret", hashed_password)
    assert not main.verify_password("wrong", hashed_password)

def test_register_login_logout(client):
    response = client.post(
        "/register",
        data={"username": "testing", "password": "password"},
    )

    assert response.status_code == 302

    with main.app.app_context():
        user = main.get_db().execute(
            "SELECT * FROM users WHERE username = ?",
            ("testing",),
        ).fetchone()

    assert user["is_admin"] == 1

    dupe_response = client.post(
        "/register",
        data={"username": "testing", "password": "password"},
    )

    assert dupe_response.status_code == 200

    login_response = login(client)

    assert login_response.status_code == 302

    with client.session_transaction() as sess:
        assert sess["user_id"] == user["id"]

    bad_login_response = client.post(
        "/login",
        data={"username": "testing", "password": "wrong"},
    )

    assert bad_login_response.status_code == 200

    logout_response = client.get("/logout")

    assert logout_response.status_code == 302

    with client.session_transaction() as sess:
        assert "user_id" not in sess

def test_crud_post(client):
    assert client.get("/posts/new").status_code == 401

    with main.app.app_context():
        user = add_user()

    login(client)

    create_response = client.post(
        "/posts/new",
        data={"title": "New Post", "content": "Content"},
    )

    assert create_response.status_code == 302

    with main.app.app_context():
        post = main.get_db().execute(
            "SELECT * FROM posts WHERE title = ?",
            ("New Post",),
        ).fetchone()

    assert post is not None
    assert client.get(f"/posts/{post['id']}").status_code == 200
    assert client.get("/posts/wrong").status_code == 404

    edit_response = client.post(
        f"/posts/{post['id']}/edit",
        data={"title": "New Title", "content": "New Content"},
    )

    assert edit_response.status_code == 302

    with main.app.app_context():
        updated_post = main.get_db().execute(
            "SELECT * FROM posts WHERE id = ?",
            (post["id"],),
        ).fetchone()

    assert updated_post["title"] == "New Title"

    delete_response = client.post(f"/posts/{post['id']}/delete")

    assert delete_response.status_code == 302

    with main.app.app_context():
        deleted_post = main.get_db().execute(
            "SELECT * FROM posts WHERE id = ?",
            (post["id"],),
        ).fetchone()

    assert deleted_post is None

def test_crud_comment(client):
    assert client.post("/posts/1/comments", data={"content": "No login"}).status_code == 401

    with main.app.app_context():
        user = add_user()
        post_id = add_post(user["id"])

    login(client)

    create_response = client.post(
        f"/posts/{post_id}/comments",
        data={"content": "First Comment"},
    )

    assert create_response.status_code == 302

    with main.app.app_context():
        comment = main.get_db().execute(
            "SELECT * FROM comments WHERE post_id = ?",
            (post_id,),
        ).fetchone()

    assert comment is not None

    edit_response = client.post(
        f"/comments/{comment['id']}/edit",
        data={"content": "New Comment"},
    )

    assert edit_response.status_code == 302

    with main.app.app_context():
        updated_comment = main.get_db().execute(
            "SELECT * FROM comments WHERE id = ?",
            (comment["id"],),
        ).fetchone()

    assert updated_comment["content"] == "New Comment"

    delete_response = client.post(f"/comments/{comment['id']}/delete")

    assert delete_response.status_code == 302

    with main.app.app_context():
        deleted_comment = main.get_db().execute(
            "SELECT * FROM comments WHERE id = ?",
            (comment["id"],),
        ).fetchone()

    assert deleted_comment is None