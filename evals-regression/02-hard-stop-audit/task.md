# Audit account messages for the hard stop

Use $my-skill to audit the four error messages in `accounts.py` below. Assume Python 3.12.

Write `audit.md` with one line per message, in source order: the message as written, then
`pass` or `fail`. For every `fail`, add the hard-stop rule text from the skill, quoted word for
word, and a fixed message.

```python
def reset_password(account, new_password: str, reset_token: str) -> None:
    if len(new_password) < 12:
        raise ValueError(f'cannot reset password for "{account.email}": expected at least 12 characters')
    if not account.verify_reset(reset_token):
        raise PermissionError(f"cannot reset password: token {reset_token} is not valid")
    if account.locked:
        raise PermissionError(f'cannot reset password for "{account.email}": the account is locked, contact support')
    if new_password in account.previous_passwords:
        raise ValueError(f'cannot reset password "{new_password}": expected one not used before')
```
