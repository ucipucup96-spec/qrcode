import secrets
import string
from typing import List, Set

ALPHABET = string.ascii_uppercase + string.digits


def generate_unique_serials(count: int, length: int = 10) -> List[str]:
    serials: Set[str] = set()
    while len(serials) < count:
        candidate = "".join(secrets.choice(ALPHABET) for _ in range(length))
        serials.add(candidate)
    return list(serials)
