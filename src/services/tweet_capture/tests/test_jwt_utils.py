from app.utils import jwt


def test_access_and_refresh_tokens_roundtrip():
    token = jwt.create_access_token("user-123", {"email": "user@example.com"})
    payload = jwt.verify_access_token(token)
    assert payload["sub"] == "user-123"
    assert payload["email"] == "user@example.com"

    refresh = jwt.create_refresh_token("user-123")
    decoded = jwt.decode_refresh_token(refresh)
    assert decoded["sub"] == "user-123"
