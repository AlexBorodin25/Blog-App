# Blog-App
This is a simple Blog App made with Flask.
You are able to register/login, post, comment, and access the admin page.
Requirements: Flask, bcrypt.
To run with docker use "docker run -e FLASK_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')" -p 8000:8000 blog-app"
