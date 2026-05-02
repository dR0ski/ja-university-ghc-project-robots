def _csrf_token(client):
    """Pull a CSRF token from the GET /register form."""
    resp = client.get("/register")
    body = resp.get_data(as_text=True)
    # Find the hidden csrf_token value
    marker = 'name="csrf_token"'
    i = body.index(marker)
    val_marker = 'value="'
    j = body.index(val_marker, i) + len(val_marker)
    k = body.index('"', j)
    return body[j:k]


def _form(client, **overrides):
    data = {
        "csrf_token": _csrf_token(client),
        "email": "alice@example.com",
        "display_name": "Alice",
        "password": "Sup3rSecret!Pass",
        "password_confirm": "Sup3rSecret!Pass",
        "accept_terms": "y",
        "website": "",
    }
    data.update(overrides)
    return data


def test_get_register_renders_form_with_csrf(client):
    resp = client.get("/register")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'name="csrf_token"' in body
    assert 'name="email"' in body
    assert 'name="password"' in body


def test_register_happy_path(client, db_session):
    from app.models.user import User

    resp = client.post("/register", data=_form(client))
    assert resp.status_code == 303
    assert resp.headers["Location"].endswith("/register/success")

    user = db_session.query(User).filter_by(email="alice@example.com").one()
    assert user.password_hash and user.password_hash.startswith("$argon2")
    assert user.is_verified is False


def test_register_weak_password_rejected(client, db_session):
    from app.models.user import User

    data = _form(client, password="alllowercase1", password_confirm="alllowercase1")
    resp = client.post("/register", data=data)
    assert resp.status_code == 400
    assert db_session.query(User).count() == 0


def test_register_password_mismatch(client, db_session):
    from app.models.user import User

    data = _form(client, password_confirm="Different!Pass99")
    resp = client.post("/register", data=data)
    assert resp.status_code == 400
    assert db_session.query(User).count() == 0


def test_register_missing_csrf_rejected(client, db_session):
    from app.models.user import User

    data = _form(client)
    data.pop("csrf_token")
    resp = client.post("/register", data=data)
    assert resp.status_code in (400, 403)
    assert db_session.query(User).count() == 0


def test_register_honeypot_silent(client, db_session):
    from app.models.user import User

    data = _form(client, website="http://spam.example.com")
    resp = client.post("/register", data=data)
    assert resp.status_code == 303
    assert resp.headers["Location"].endswith("/register/success")
    assert db_session.query(User).count() == 0


def test_register_duplicate_no_enumeration(client, db_session):
    from app.models.user import User

    r1 = client.post("/register", data=_form(client))
    r2 = client.post("/register", data=_form(client))

    assert r1.status_code == r2.status_code == 303
    assert r1.headers["Location"] == r2.headers["Location"]
    assert db_session.query(User).count() == 1


def test_password_must_not_contain_email_local(client, db_session):
    from app.models.user import User

    data = _form(
        client,
        email="alice@example.com",
        password="aliceALICE123!!",
        password_confirm="aliceALICE123!!",
    )
    resp = client.post("/register", data=data)
    assert resp.status_code == 400
    assert db_session.query(User).count() == 0
