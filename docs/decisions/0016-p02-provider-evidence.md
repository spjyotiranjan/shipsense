# Decision 0016 - P02 provider evidence verification

**Date:** 28 November 2026.
**Status:** Proposed provider boundary implementation. Live configuration and activation are pending.

FastAPI independently validates provider evidence from a purpose-bound exchange. Google tokens use RS256 with trusted server-resolved keys, a single configured web audience, the expected exchange nonce, and the documented issuer and mailbox checks. The verifier never accepts key URLs from the token. Fixed-origin JWKS retrieval, rotation, and single-use exchange state are required before runtime activation.

GitHub identity reads use the pinned HTTPX client with verified TLS, redirects and environment proxies disabled, and fixed GitHub API paths. Fetch `/user` and paginate `/user/emails` with the same exchanged token. Start with 100 items per page and require an empty terminal page within five requests. Bound total time to five seconds and each body to 64 KiB. Incomplete pagination, missing scope, unverified or ambiguous primary mail, or out-of-budget responses give no identity evidence. Recheck these limits with authorized test apps before activation.

The provider evidence retains the stable subject and delivery address. Canonical email-key normalization, recovery, linking, account creation, revocation and session issuance remain separate gates. No provider credential is printed or placed in a tracked file. Blank configuration names are listed in [`.env.example`](../../.env.example).

**Sources:** [Decision 0009](0009-p02-sign-in-methods.md), [Google ID-token verification](https://developers.google.com/identity/gsi/web/guides/verify-google-id-token), and [GitHub authenticated email API](https://docs.github.com/en/rest/users/emails#list-email-addresses-for-the-authenticated-user).
