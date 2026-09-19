# Security

## Reporting

Email security@sigrix.io with what you found and how to reproduce it. Do not
open a public issue for a vulnerability. You will get an acknowledgement
within three working days.

## What this server holds

One secret: the seller API token in `SIGRIX_SELLER_TOKEN`. The server sends it
only in the `Authorization` header of requests to `SIGRIX_BASE_URL`, never
logs it, and never writes it to disk. The token can create, edit and submit
the holder's own draft listings for review; it cannot approve or publish, and
it reaches no other route on the platform.

If a token leaks, revoke or regenerate it on the Sigrix account settings page.
The old token stops working on the next request.

## What to report to the platform instead

Anything about the seller API itself — what a token can reach, how a draft is
moderated — is the platform's, not this client's. Report it to the same
address; it will be routed.
