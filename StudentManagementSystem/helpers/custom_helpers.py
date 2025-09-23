import hmac, hashlib, base64, json, time
import os

from django.conf import settings
API_SECRET = os.getenv("API_SECRET") # put in .env
print(API_SECRET)

def make_access_token(student_id, ttl_minutes=5):
    """Create short-lived signed access token (default 5 mins)."""
    payload = {
        "sid": student_id,
        "iat": int(time.time()),
        "exp": int(time.time() + ttl_minutes * 60),
    }
    raw = json.dumps(payload, separators=(",", ":")).encode()
    sig = hmac.new(API_SECRET.encode(), raw, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(raw + b"." + sig).decode()

def verify_access_token(token):
    """Verify signature + expiration of an access token."""
    try:
        decoded = base64.urlsafe_b64decode(token.encode())
        raw, sig = decoded.rsplit(b".", 1)
        expected = hmac.new(API_SECRET.encode(), raw, hashlib.sha256).digest()
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(raw.decode())
        if payload["exp"] < time.time():
            return None
        return payload
    except Exception:
        return None
