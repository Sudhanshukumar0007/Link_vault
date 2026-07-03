import secrets
import string

RESERVED_SLUGS = {
    "health",
    "metrics",
    "docs",
    "redoc",
    "openapi.json",
    "api",
    "favicon.ico",
}

def generate_slug(length:int = 6) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))