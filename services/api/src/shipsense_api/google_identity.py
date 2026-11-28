"""Verify Google ID tokens using keys obtained by a trusted server-side resolver."""

import hmac
import re
from collections.abc import Mapping

import jwt
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from shipsense_domain.provider_mailbox import ProviderMailbox, google_mailbox

from shipsense_api.service_credentials import InvalidServiceCredential, read_segment

_ISSUERS = ("https://accounts.google.com", "accounts.google.com")
_CLOCK_SKEW = 30


def verify_google_id_token(
    token: str,
    *,
    client_id: str,
    expected_nonce: str,
    trusted_keys: Mapping[str, RSAPublicKey],
    now: int,
) -> ProviderMailbox | None:
    """Validate one token against a single web audience and a caller-bound nonce.

    This takes a trusted key snapshot and trusted exchange nonce. The caller
    still owns bounded JWKS retrieval and one-use exchange consumption.
    """
    if (
        not 1 <= len(token) <= 8192
        or not client_id
        or not expected_nonce
        or not expected_nonce.isascii()
    ):
        return None
    segments = token.split(".")
    if len(segments) != 3 or not re.fullmatch(r"[A-Za-z0-9_-]+", segments[2]):
        return None
    try:
        header, claims = (read_segment(part) for part in segments[:2])
    except InvalidServiceCredential, ValueError, RecursionError:
        return None
    kid = header.get("kid")
    if (
        set(header) - {"alg", "kid", "typ"}
        or header.get("alg") != "RS256"
        or header.get("typ", "JWT") != "JWT"
        or not isinstance(kid, str)
        or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", kid)
    ):
        return None
    key = trusted_keys.get(kid)
    if key is None or key.key_size < 2048:
        return None
    nonce = claims.get("nonce")
    issued = claims.get("iat")
    expires = claims.get("exp")
    not_before = claims.get("nbf", issued)
    if (
        claims.get("iss") not in _ISSUERS
        or claims.get("aud") != client_id
        or claims.get("azp", client_id) != client_id
        or not isinstance(nonce, str)
        or not nonce.isascii()
        or not hmac.compare_digest(nonce, expected_nonce)
        or type(issued) is not int
        or type(expires) is not int
        or type(not_before) is not int
        or not 0 <= issued < expires
        or not 0 <= not_before < expires
        or max(issued, not_before) > now + _CLOCK_SKEW
        or expires <= now - _CLOCK_SKEW
    ):
        return None
    try:
        jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            options={
                "verify_exp": False,
                "verify_iat": False,
                "verify_nbf": False,
                "verify_aud": False,
                "verify_iss": False,
            },
        )
    except jwt.InvalidTokenError, ValueError:
        return None
    return google_mailbox(claims)
