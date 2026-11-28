"""Internal account matching after verification; no provider calls or authority issuance."""

from dataclasses import dataclass
from typing import Literal, Protocol
from uuid import UUID

from shipsense_domain.models import Status


@dataclass(frozen=True)
class ProviderSubject:
    provider: Literal["google", "github"]
    subject: str


@dataclass(frozen=True)
class VerifiedProviderIdentity:
    """Construct only from a verified, purpose-bound exchange, never from request attributes."""

    subject: ProviderSubject
    email_key: str


@dataclass(frozen=True)
class DirectoryAccount:
    id: UUID
    email_key: str
    status: Status


class AccountDirectory(Protocol):
    """Canonical identity-only directory; ambiguity/errors must raise, not look like absence."""

    def by_subject(self, subject: ProviderSubject) -> DirectoryAccount | None: ...

    def by_email_key(self, key: str) -> DirectoryAccount | None: ...


@dataclass(frozen=True)
class AccountMatch:
    outcome: Literal["returning", "registration_candidate", "unavailable"]
    account_id: UUID | None = None


def match_sign_in(identity: VerifiedProviderIdentity, directory: AccountDirectory) -> AccountMatch:
    """Never serialize these outcomes publicly; only a fenced write could create a session."""
    bound = directory.by_subject(identity.subject)
    if bound is not None:
        if bound.status == "active" and bound.email_key == identity.email_key:
            return AccountMatch("returning", bound.id)
        return AccountMatch("unavailable")
    if directory.by_email_key(identity.email_key) is not None:
        return AccountMatch("unavailable")
    return AccountMatch("registration_candidate")
