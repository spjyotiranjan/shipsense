# Decision 0017 - P02 email delivery through Azure

**Date:** 28 November 2026.
**Status:** Accepted provider selection by the project owner. Runtime integration and live delivery verification are pending.

Use Azure Communication Services Email for registration verification and password recovery. This supersedes the email provider selection in [Decision 0009](0009-p02-sign-in-methods.md). FastAPI owns challenge issuance and consumption. Provider delivery status conveys no account authority.

Use an Azure-managed domain for initial non-production testing. Keep the connection string in private API configuration and use the linked domain's MailFrom address. Evaluate managed identity for deployment. Validate data location, quotas and costs before provisioning. Live sends and activation require separate verification.

[Azure Email quickstart](https://learn.microsoft.com/en-us/azure/communication-services/quickstarts/email/send-email?pivots=programming-language-python)

## Local adapter design

Use the documented Azure Email 2025-09-01 REST send endpoint with the existing pinned HTTP client and HMAC authentication. Each outbox attempt may submit one plain-text message with tracking disabled. A 202 records provider submission acceptance. A quota response is explicit and the adapter does not automatically resend. A missing acknowledgement is unknown and must be reconciled by the outbox. Requests use a fixed public Azure Communication Services endpoint and do not follow redirects. Credential-free verification uses a mock transport.

[Email Send REST reference](https://learn.microsoft.com/en-us/rest/api/communication/email/email/send) and [ACS request signing](https://learn.microsoft.com/en-us/rest/api/communication/authentication).
