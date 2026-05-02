def test_splash_renders(client):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "<video" in body
    assert "hero-poster.jpg" in body
    assert "/register" in body
    # Single H1 (the headline).
    assert body.count("<h1") == 1
    # No inline scripts or styles (CSP safety, defense-in-depth assertion).
    assert "<script>" not in body
    assert " style=\"" not in body
