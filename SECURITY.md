# Security Policy

## How kite-mcp handles your data

- **Credentials** are passed via environment variables -- never stored in code or config files within the repo
- **Access tokens** are cached locally at `~/.zerodha_kite_token.json` with owner-only permissions and expire daily
- **All communication** with Zerodha uses HTTPS
- **The server runs locally** on your machine -- no data is sent to third-party servers
- **No telemetry** or analytics of any kind

## Reporting a vulnerability

If you discover a security vulnerability, please **do not** open a public issue.

Instead, email **mail2amit.ranjan@gmail.com** with:
- Description of the vulnerability
- Steps to reproduce
- Potential impact

You will receive a response within 48 hours. Critical issues will be patched and released as soon as possible.

## Supported versions

| Version | Supported |
|---------|-----------|
| Latest  | Yes       |
| < Latest | No -- please upgrade |
