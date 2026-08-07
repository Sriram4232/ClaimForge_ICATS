import hashlib
import os

def hash_password(password: str, salt: bytes = None) -> str:
    """
    Hashes a plain text password using PBKDF2 HMAC SHA-256 with a random salt.
    Returns string representation of "salt_hex:key_hex".
    """
    if salt is None:
        salt = os.urandom(16)
    # Perform 100,000 iterations of PBKDF2 HMAC SHA-256
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return f"{salt.hex()}:{key.hex()}"

def verify_password(stored_password: str, provided_password: str) -> bool:
    """
    Verifies a provided password against the stored password hash.
    Supports a plain text fallback if the stored password is not hashed.
    """
    if not stored_password:
        return False
        
    try:
        # Check if stored value matches standard "salt_hex:key_hex" format
        if ":" in stored_password:
            salt_hex, key_hex = stored_password.split(":", 1)
            salt = bytes.fromhex(salt_hex)
            key = bytes.fromhex(key_hex)
            new_key = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
            return new_key == key
    except Exception:
        pass
        
    # Plain text fallback for non-migrated users or legacy checks
    return stored_password == provided_password
