# Copyright 2026 Jiacheng Ni
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import hmac
import json
import secrets
import time


PASSWORD_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%^&*"


def generate_password(length: int = 24) -> str:
    return "".join(secrets.choice(PASSWORD_ALPHABET) for _ in range(length))


def generate_secret(length: int = 48) -> str:
    return secrets.token_urlsafe(length)


def hash_password(password: str, *, iterations: int = 260_000, salt: str | None = None) -> str:
    salt = salt or secrets.token_urlsafe(18)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
    encoded = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return f"pbkdf2_sha256${iterations}${salt}${encoded}"


def verify_password(password: str, encoded: str | None) -> bool:
    if not encoded:
        return False
    try:
        algorithm, iterations_text, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hash_password(password, iterations=int(iterations_text), salt=salt).split("$", 3)[3]
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


@dataclass(frozen=True)
class Session:
    username: str
    expires_at: int


class SessionSigner:
    def __init__(self, secret: str, ttl_seconds: int = 86_400):
        self.secret = secret.encode("utf-8")
        self.ttl_seconds = ttl_seconds

    def issue(self, username: str) -> str:
        payload = {
            "sub": username,
            "exp": int(time.time()) + self.ttl_seconds,
            "nonce": secrets.token_urlsafe(12),
        }
        body = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")).decode(
            "ascii"
        ).rstrip("=")
        signature = self._sign(body)
        return f"{body}.{signature}"

    def verify(self, token: str | None) -> Session | None:
        if not token or "." not in token:
            return None
        body, signature = token.rsplit(".", 1)
        if not hmac.compare_digest(self._sign(body), signature):
            return None
        try:
            padded = body + "=" * (-len(body) % 4)
            payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))
            expires_at = int(payload["exp"])
            username = str(payload["sub"])
        except (ValueError, KeyError, json.JSONDecodeError):
            return None
        if expires_at < int(time.time()):
            return None
        return Session(username=username, expires_at=expires_at)

    def _sign(self, body: str) -> str:
        digest = hmac.new(self.secret, body.encode("ascii"), hashlib.sha256).digest()
        return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
