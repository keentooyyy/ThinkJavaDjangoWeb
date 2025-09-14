import hashlib


def make_login_key(identifier: str, role: str) -> str:
    """
    Generate a stable login_key from ID + role.
    Example: 12-3456-789:STUDENT → unique 64-char SHA256 hash.
    """
    raw = f"{identifier}:{role}"
    return hashlib.sha512(raw.encode()).hexdigest()