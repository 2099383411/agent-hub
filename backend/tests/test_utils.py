"""工具函数测试"""

from app.utils.security import (
    hash_password, verify_password,
    create_jwt_token, decode_jwt_token,
    generate_app_credentials,
    generate_mcp_signature, verify_mcp_signature,
)


class TestPassword:
    def test_hash_and_verify(self):
        hashed = hash_password("test123")
        assert verify_password("test123", hashed)
        assert not verify_password("wrong", hashed)

    def test_different_hashes(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2  # bcrypt 每次 salt 不同


class TestJWT:
    def test_create_and_decode(self):
        token = create_jwt_token({"sub": "admin"})
        payload = decode_jwt_token(token)
        assert payload["sub"] == "admin"

    def test_invalid_token(self):
        result = decode_jwt_token("invalid.token.here")
        assert result is None


class TestCredentials:
    def test_generate_app_credentials(self):
        app_id, app_secret = generate_app_credentials()
        assert app_id.startswith("qw_")
        assert len(app_id) > 10
        assert len(app_secret) > 20


class TestMCPSignature:
    def test_sign_and_verify(self):
        app_id = "qw_test123"
        app_secret = "test_secret_key_12345"
        timestamp, nonce, signature = generate_mcp_signature(app_id, app_secret)
        assert verify_mcp_signature(app_id, timestamp, nonce, signature, app_secret)

    def test_wrong_secret_fails(self):
        app_id = "qw_test123"
        app_secret = "correct_secret"
        wrong_secret = "wrong_secret"
        timestamp, nonce, signature = generate_mcp_signature(app_id, app_secret)
        assert not verify_mcp_signature(app_id, timestamp, nonce, signature, wrong_secret)
