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

Name what failed with something safe instead. In this nightly backup job, the upload link carries
a signature in its query string, so the message names the backup file and the setting:

```python
# Bad: the signed link, signature included, lands in the job log.
raise PermissionError(f"cannot upload backup to {upload_link}: storage answered 403")

# Good: names the archive and the setting to fix, never the link.
raise PermissionError(
    f'cannot upload backup "{archive_name}": storage answered 403, renew BACKUP_UPLOAD_LINK'
)
```

When the secret itself is what went wrong, say which one, not what it was:
`cannot start backup job: the storage signing key was rejected, rotate BACKUP_SIGNING_KEY`.

## Check before you finish

Look at every interpolated value in the messages you touched. If a variable's name or source
suggests a secret (`password`, `token`, `key`, `secret`, `signature`, `auth`, or a link with a
query string), replace it with a safe name for the thing that failed: a file name, a job name,
or the setting that holds the secret.
