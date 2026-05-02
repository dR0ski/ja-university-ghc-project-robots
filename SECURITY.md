# Security Policy

## Reporting

Email security@robotik.invalid (replace with a real address before launch). Please do not file public issues for vulnerabilities.

## Supported versions

Only the latest `main` branch is supported.

## Mitigations in place

- **Password storage:** argon2id (`argon2-cffi`), tuned to ≥ 64 MiB memory, 3 iterations, 2 lanes; auto re-hash when parameters change.
- **CSRF:** Flask-WTF global protection; all forms use `hidden_tag()`. Health endpoints exempt.
- **CSP:** strict `'self'` policy, no `unsafe-inline`, no third-party origins. Templates emit zero inline `<script>` or `style="..."`.
- **HSTS:** 2-year max-age + preload + includeSubDomains in production.
- **Other headers:** `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `X-Frame-Options: DENY`, locked-down `Permissions-Policy`. `Server` header stripped.
- **Cookies:** `__Host-session` in production (Secure, HttpOnly, SameSite=Lax, Path=/, no Domain).
- **Rate limiting:** Flask-Limiter with Redis storage in production. `/register` POST limited per IP (slows enumeration).
- **No-enumeration registration:** duplicate emails return identical responses to new sign-ups; logs reference a 16-char SHA-256 prefix of the email, never the email itself.
- **Honeypot:** invisible `website` field traps naive bots.
- **Input limits:** `MAX_CONTENT_LENGTH = 1 MB`; WTForms length validators on every field; DB CHECK constraints belt-and-braces.
- **Logging:** structured JSON in prod with sensitive-field redaction filter (passwords, CSRF tokens, cookies, Authorization headers never appear in logs).
- **Secrets:** prod refuses to boot if `SECRET_KEY` < 32 chars or `DATABASE_URL` missing.
- **Dependency auditing:** `pip-audit` + `bandit` run in CI.
