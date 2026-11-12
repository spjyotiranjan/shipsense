# Decision 0011 - P02 canonical session lifecycle

**Date:** 12 November 2026
**Status:** Accepted, bounded initial implementation.
**Decision owner:** Patrick Jane.

Store only a SHA-256 digest of the existing random 256-bit session handle. The canonical session record binds account ID and authentication epoch, immutable creation and absolute expiry, idle deadline, revocation and revision. At trusted server time, resolve requires an active account, matching epoch, no revocation and unexpired absolute and idle deadlines. This initial slice does not renew idle time; the encrypted envelope remains an upper bound. Revoke is idempotent, with its state transition and redacted correlated audit in the same transaction contract. Unknown, revoked and expired sessions have the same denial; unavailable storage or audit produces unavailable. Neither raw handle nor digest appears in audit or public DTOs.

**Scope:** Strict records, pure lifecycle rules, fenced transaction port and API composition with deterministic synthetic storage. Runtime remains unavailable; no login issuance, memory authority, MongoDB writes or indexes, provider calls or new BFF scope are authorized. Durable restart and concurrency proof remain outstanding. Decisions 0009 and 0010 remain in force.

**Rationale:** Support revocable canonical authority and atomic audit while failing closed until durable storage is separately authorized and proven.

**Source:** PAT-127 canonical-session policy handoff d9df85e8, accepted by Patrick on 12 November 2026.
