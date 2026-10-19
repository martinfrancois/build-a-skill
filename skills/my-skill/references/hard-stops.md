# Hard stops

## Secrets stay out of messages

Never put a secret into an error message or log line. Error text travels further than the code
that wrote it: into log storage, crash reports, support tickets, and screenshots.

Treat these as secrets:

- passwords and passphrases
- access tokens, refresh tokens, and API keys
- session IDs and signed cookies
- card numbers, bank account numbers, and national ID numbers
- URLs and connection strings that contain a user name and password, or a token in the query

Name the field so the reader still knows what to fix:

```python
# Bad: the whole connection string, password included, lands in the log.
raise ConnectionError(f"cannot open cache {cache_dsn}: connection refused")

# Good: names the setting and the host, never the credentials.
raise ConnectionError(f'cannot open cache "{cache_host}": connection refused, check CACHE_DSN')
```

When the only useful detail is the secret itself, say which one was wrong:
`cannot sign request: the signing key was rejected, rotate SIGNING_KEY`.

## Check before you finish

Look at every interpolated value in the messages you touched. If a variable's name or source
suggests a secret (`password`, `token`, `key`, `secret`, `dsn`, `auth`, or a card number),
replace it with the field name or a non-secret identifier such as a host name or the last four
digits.
