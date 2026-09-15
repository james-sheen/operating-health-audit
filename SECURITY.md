# Security

## Reporting

Report a vulnerability through GitHub's private advisory form on this
repository: **Security -> Report a vulnerability**. That channel is private and
reaches the maintainers without disclosing the issue publicly first.

Please do not open a public issue for a vulnerability.

## What this package touches

It reads two local files and writes one. It opens no network connection, runs
no subprocess, and holds no credential. Stage 2 imports `arbiter-engine` in one
module and passes it data already read from disk.

The most likely real issue is not memory safety but **a wrong answer**: an audit
that reports clean about an organisation it could not actually see. Those are
tracked in `FINDINGS.md` as defects rather than as vulnerabilities, and four of
the nine recorded there have that shape.

## Supported versions

The latest released version. This project is pre-1.0 and fixes land forward.
