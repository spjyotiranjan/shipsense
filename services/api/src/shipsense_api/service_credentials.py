"""Narrow BFF authentication, never user or worker authorization (Decision 0010)."""

import base64
import json
import re
from dataclasses import dataclass
from typing import Literal

import jwt
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from cryptography.hazmat.primitives.serialization import load_pem_public_key

ISSUER = "shipsense-web"
AUDIENCE = "shipsense-auth"
SUBJECT = "shipsense-bff"
Scope = Literal["session:resolve", "session:revoke"]


class InvalidServiceCredential(Exception):
    """Intentionally contains no credential or verifier details."""


@dataclass(frozen=True)
class ServiceKey:
    public_pem: bytes
    status: Literal["active", "retired"]
    not_before: int
    not_after: int


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise InvalidServiceCredential()
        result[key] = value
    return result


def read_segment(segment: str) -> dict[str, object]:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", segment):
        raise InvalidServiceCredential()
    decoded = base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))
    result = json.loads(decoded.decode("utf-8"), object_pairs_hook=unique_object)
    if not isinstance(result, dict):
        raise InvalidServiceCredential()
    return result


def verify_service_credential(
    token: str, scope: Scope, keys: dict[str, ServiceKey], now: int, skew: int = 30
) -> None:
    """Fixed local registry only. No JWKS/header URL retrieval or algorithm negotiation."""
    try:
        if scope not in ("session:resolve", "session:revoke"):
            raise InvalidServiceCredential()
        if not 0 <= skew <= 30 or not 1 <= len(token) <= 4096:
            raise InvalidServiceCredential()
        segments = token.split(".")
        if len(segments) != 3 or not re.fullmatch(r"[A-Za-z0-9_-]+", segments[2]):
            raise InvalidServiceCredential()
        header, claims = (read_segment(part) for part in segments[:2])
        if set(header) != {"alg", "typ", "kid"}:
            raise InvalidServiceCredential()
        kid = header["kid"]
        if header["alg"] != "RS256" or header["typ"] != "JWT":
            raise InvalidServiceCredential()
        if not isinstance(kid, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", kid):
            raise InvalidServiceCredential()
        key = keys.get(kid)
        if key is None or key.status != "active" or not key.not_before <= now < key.not_after:
            raise InvalidServiceCredential()
        if set(claims) != {"iss", "aud", "sub", "scope", "iat", "nbf", "exp", "jti"}:
            raise InvalidServiceCredential()
        if (claims["iss"], claims["aud"], claims["sub"], claims["scope"]) != (
            ISSUER,
            AUDIENCE,
            SUBJECT,
            scope,
        ):
            raise InvalidServiceCredential()
        if any(type(claims[name]) is not int for name in ("iat", "nbf", "exp")):
            raise InvalidServiceCredential()
        issued, not_before, expires = (int(str(claims[name])) for name in ("iat", "nbf", "exp"))
        if not issued == not_before or not 0 < expires - issued <= 60:
            raise InvalidServiceCredential()
        if issued > now + skew or expires <= now - skew:
            raise InvalidServiceCredential()
        if not key.not_before <= issued < expires <= key.not_after:
            raise InvalidServiceCredential()
        if not isinstance(claims["jti"], str) or not re.fullmatch(
            r"[A-Za-z0-9_-]{16,64}", claims["jti"]
        ):
            raise InvalidServiceCredential()
        public = load_pem_public_key(key.public_pem)
        if not isinstance(public, RSAPublicKey) or public.key_size < 2048:
            raise InvalidServiceCredential()
        # Claim validation above uses the supplied clock for reproducible boundary tests.
        # Signature validation is always performed by the pinned verifier.
        jwt.decode(
            token,
            public,
            algorithms=["RS256"],
            options={
                "verify_exp": False,
                "verify_iat": False,
                "verify_nbf": False,
                "verify_aud": False,
                "verify_iss": False,
                "verify_sub": False,
                "verify_jti": False,
            },
        )
    except Exception:
        raise InvalidServiceCredential() from None
