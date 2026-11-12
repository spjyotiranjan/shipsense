# Decision 0009 — P02 sign-in methods

**Date:** 11 November 2026
**Status:** Accepted product direction; implementation details require validation.
**Decision owner:** ShipSense project owner.

Use NextAuth for Google and GitHub sign-in and email/password sign-in. Email/password registration asks for email, password and full name; additional profile information may be added later. Use a Twilio email provider for email verification before activating email/password sign-in. Treat email as the unique account key. When an existing Google account holder attempts email/password sign-in, guide them through Google sign-in and a safe account-management flow.

Social sign-in is intended to use verified email addresses. The implementation must validate the provider's actual verified-email evidence and fail safely when unavailable; an email match alone must not silently link accounts or prove control. Research provider and account-recovery behavior, account enumeration tradeoffs and secure linking in the P02 plans. FastAPI remains the canonical authorization boundary under Decision 0002. The detailed session, token, linking, recovery and provider configurations remain subject to the P02 plan and security validation. This direction does not authorize provisioning, spending or remote persistence writes.

**Source:** authenticated owner response to PAT-120 confirmation `5187a57a-6caa-4f9d-9740-e557745bb701`, 11 November 2026. This narrows the identity selection left open in Decision 0002; it does not approve the P02 implementation plans.
