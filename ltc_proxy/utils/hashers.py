import hashlib
from hashlib import sha256
import scrypt


def dsha256(b: bytes) -> bytes:
    return sha256(sha256(b).digest()).digest()


def scrypt_pow(header80: bytes) -> bytes:
    """
    Scrypt PoW hash used by Litecoin and Meowcoin.
    Parameters: N=1024, r=1, p=1, output length=32 bytes
    """
    h = scrypt.hash(header80, header80, 1024, 1, 1, 32)
    if not isinstance(h, (bytes, bytearray)) or len(h) != 32:
        raise ValueError("scrypt returned invalid digest")
    return bytes(h)
