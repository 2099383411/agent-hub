"""REST API 兜底测试 — HMAC 签名鉴权验证"""

import pytest
import time
import hmac
import hashlib
import secrets

from app.utils.security import (
    generate_app_credentials,
    verify_mcp_signature,
    generate_mcp_signature,
    hash_password,
    verify_password,
    create_jwt_token,
    decode_jwt_token,
    generate_onboard_token,
    verify_onboard_token,
)


class TestVerifyMCPSignature:
    """MCP 签名验证测试"""

    def test_valid_signature(self):
        app_id, app_secret = generate_app_credentials()
        timestamp = str(int(time.time()))
        nonce = secrets.token_hex(8)
        message = f"{app_id}\nGET\n/mcp/sse\n{timestamp}\n{nonce}"
        signature = hmac.new(app_secret.encode(), message.encode(), hashlib.sha256).hexdigest()

        assert verify_mcp_signature(app_id, timestamp, nonce, signature, app_secret)

    def test_expired_signature(self):
        app_id, app_secret = generate_app_credentials()
        timestamp = str(int(time.time()) - 600)  # 10 分钟前
        nonce = secrets.token_hex(8)
        message = f"{app_id}\nGET\n/mcp/sse\n{timestamp}\n{nonce}"
        signature = hmac.new(app_secret.encode(), message.encode(), hashlib.sha256).hexdigest()

        assert not verify_mcp_signature(app_id, timestamp, nonce, signature, app_secret)

    def test_wrong_secret(self):
        app_id, _ = generate_app_credentials()
        timestamp = str(int(time.time()))
        nonce = secrets.token_hex(8)
        signature = "wrong_signature"

        assert not verify_mcp_signature(app_id, timestamp, nonce, signature, "wrong_secret")

    def test_generate_mcp_signature(self):
        app_id, app_secret = generate_app_credentials()
        timestamp, nonce, signature = generate_mcp_signature(app_id, app_secret)

        assert verify_mcp_signature(app_id, timestamp, nonce, signature, app_secret)


class TestOnboardToken:
    """Onboard Token 生命周期测试"""

    def test_generate_and_verify(self):
        token, expires_at = generate_onboard_token()
        assert len(token) > 20
        assert expires_at is not None

        assert verify_onboard_token(token, token, expires_at)

    def test_invalid_token(self):
        token, expires_at = generate_onboard_token()
        assert not verify_onboard_token("wrong_token", token, expires_at)

    def test_none_stored_token(self):
        token, expires_at = generate_onboard_token()
        assert not verify_onboard_token(token, None, expires_at)


class TestCredentials:
    """凭证生成测试"""

    def test_generate_unique(self):
        id1, secret1 = generate_app_credentials()
        id2, secret2 = generate_app_credentials()
        assert id1 != id2
        assert secret1 != secret2
        assert id1.startswith("qw_")


class TestJWT:
    """JWT 令牌生命周期测试"""

    def test_create_and_decode(self):
        token = create_jwt_token({"sub": "admin", "role": "admin"})
        payload = decode_jwt_token(token)
        assert payload["sub"] == "admin"
        assert payload["role"] == "admin"

    def test_invalid_token(self):
        assert decode_jwt_token("invalid") is None


class TestPassword:
    """密码哈希测试"""

    def test_hash_and_verify(self):
        hashed = hash_password("my_password")
        assert verify_password("my_password", hashed)
        assert not verify_password("wrong", hashed)

    def test_same_password_different_hashes(self):
        """每次 bcrypt salt 不同"""
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2
