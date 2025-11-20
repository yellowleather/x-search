from app.utils.password import hash_password, verify_password


def test_password_hash_roundtrip():
    hashed = hash_password("Test1234!")
    assert hashed != "Test1234!"
    assert verify_password("Test1234!", hashed)
