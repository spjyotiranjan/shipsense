# Decision 0010 - P02 session bridge

**Date:** 12 November 2026
**Status:** Accepted, bounded initial implementation.
**Decision owner:** Patrick Jane.

NextAuth 4.24.15 JWT/no-adapter integration and PyJWT 2.15.1/cryptography 50.0.2 are initial pins, subject to integration and security verification. NextAuth encryption remains library-managed; clamp cookie, encrypted token and public session expiration to canonical immutable 900-second absolute and 600-second idle limits. Extract session cookies only, never bearer fallback; expose no session handle or provider tokens in the public DTO. A valid encrypted cookie alone grants no authority: FastAPI independently resolves canonical session state and authorization for protected operations. No refresh tokens.

Separate BFF service credentials use RS256 with fixed issuer, audience and subject, auth-only scopes, at most 60-second lifetime, at most 30-second skew, strict claim types/size and fixed kid/key-status allowlist; reject duplicate claims, header-directed keys and algorithms. Private signing key remains server-only and uses Azure secret management when deployed; API holds public allowlist. Explicit active-key overlap is allowed; retired keys are denied. Browser credentials and workload credentials are distinct. Default disabled and fail closed when authority is unavailable.

**Rationale:** Constrain rolling expiry, bearer fallback and revocation ambiguity demonstrated in compatibility probes.

**Scope:** Bridge contract and implementation only; live provider and durable authority require separate proof and authorization.

**Source:** PAT-125 compatibility-330838c.md and Patrick technical acceptance, 12 November 2026 (comment eace74c9-55ac-4c0e-a53a-c015ea0dad75).
