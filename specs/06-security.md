---
id: security
version: 1.0.0
title: Security (OWASP Top 10 oriented)
order: 60
areas: [security]
inputs: [secrets, vulnerabilities, dependencies, api]
files:
  keywords: [login, auth, account, user, password, token, session, security, crypto, upload, admin, web.config]
  content: "password|Authorize|authenticat|session|cookie|crypt|hash|md5|sha1|eval\\(|exec\\(|Process\\.Start|Runtime\\.getRuntime|innerHTML|\\+\\s*\"\\s*(SELECT|WHERE)"
  globs: ["**/web.config", "**/appsettings*.json", "**/application*.properties", "**/application*.yml"]
---
## Purpose
Find the security weaknesses a reviewer would raise, mapped to OWASP Top 10 (2021) categories and CWE ids.

## Look for
- Injection: SQL, command, LDAP, XPath built from user input (A03).
- Broken access control: endpoints or pages without authorization checks, IDs taken from the request without
  ownership checks (A01).
- Weak cryptography: MD5/SHA1 for passwords, home-made crypto, hard-coded keys or IVs (A02).
- Authentication: plain-text password storage or comparison, missing lockout, insecure session or cookie flags (A07).
- Security misconfiguration: debug mode, custom errors off, permissive CORS, directory browsing (A05).
- Cross-site scripting: unencoded output, innerHTML, Html.Raw with user data (A03).
- Insecure deserialization and file upload handling (A08).
- Sensitive data in logs.

## Evidence rules
Quote the vulnerable line. Exposed secrets and vulnerable library versions are already reported by tools: only add
to them if you see how they are used.

## Business translation
Say what an attacker could do (see other customers' data, take over accounts, stop the service) and who would be
affected. Do not exaggerate: if exploitation needs special conditions, say so.

## Out of scope
Penetration testing; infrastructure outside the repository.
