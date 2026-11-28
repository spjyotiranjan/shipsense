"""Interpret trusted sign-in evidence after a verified provider exchange."""

from collections.abc import Mapping
from dataclasses import dataclass

from shipsense_domain.account_matching import ProviderSubject


@dataclass(frozen=True)
class ProviderMailbox:
    subject: ProviderSubject
    email: str


def _email_address(value: object) -> str | None:
    if not isinstance(value, str) or len(value) > 254:
        return None
    local, delimiter, domain = value.partition("@")
    if (
        not delimiter
        or not local
        or not domain
        or "@" in domain
        or any(char.isspace() or not char.isprintable() for char in value)
    ):
        return None
    return value


def google_mailbox(claims: Mapping[str, object]) -> ProviderMailbox | None:
    """Consume claims only after the OAuth/OIDC verifier approves the exchange."""
    subject = claims.get("sub")
    email = _email_address(claims.get("email"))
    hosted_domain = claims.get("hd")
    hosted = isinstance(hosted_domain, str) and bool(hosted_domain.strip())
    if (
        not isinstance(subject, str)
        or not 1 <= len(subject) <= 255
        or not subject.isascii()
        or not subject.isprintable()
        or any(char.isspace() for char in subject)
        or email is None
        or claims.get("email_verified") is not True
        or not (email.lower().endswith("@gmail.com") or hosted)
    ):
        return None
    return ProviderMailbox(ProviderSubject("google", subject), email)


def github_mailbox(profile: Mapping[str, object], emails: object) -> ProviderMailbox | None:
    """Use authenticated /user and complete /user/emails results from one token."""
    subject = profile.get("id")
    if (
        not isinstance(subject, int)
        or isinstance(subject, bool)
        or subject <= 0
        or not isinstance(emails, list)
    ):
        return None

    primary = None
    for row in emails:
        if not isinstance(row, Mapping):
            return None
        flag = row.get("primary")
        if flag is False:
            continue
        if flag is not True or primary is not None or row.get("verified") is not True:
            return None
        primary = _email_address(row.get("email"))
        if primary is None or primary.lower().endswith("@users.noreply.github.com"):
            return None
    if primary is None:
        return None
    return ProviderMailbox(ProviderSubject("github", str(subject)), primary)
