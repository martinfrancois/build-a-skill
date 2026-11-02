def reset_password(account, new_password: str, reset_token: str) -> None:
    if len(new_password) < 12:
        raise ValueError(f'cannot reset password for "{account.email}": expected at least 12 characters')
    if not account.verify_reset(reset_token):
        raise PermissionError(f"cannot reset password: token {reset_token} is not valid")
    if account.locked:
        raise PermissionError(f'cannot reset password for "{account.email}": the account is locked, contact support')
    if new_password in account.previous_passwords:
        raise ValueError(f'cannot reset password "{new_password}": expected one not used before')
