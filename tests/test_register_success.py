def test_register_success_renders(client):
    resp = client.get("/register/success")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "Thanks" in body
    # Generic copy: no PII echoed.
    assert "@" not in body or "example" not in body
