"""
Crockford Base32 ID System for VibeCForms.

This module implements a UUID-based ID system using Crockford Base32 encoding
with check digits for data integrity.

Format: 27 characters (26 UUID + 1 check digit)
Example: 3HNMQR8PJSG0C9VWBYTE12K

Character set: 0123456789ABCDEFGHJKMNPQRSTVWXYZ (excludes I, L, O, U)
Check digit: Modulo 32 calculation using character position values

Benefits:
- URL-safe and human-readable
- Error detection via check digit
- Shorter than hex UUID (27 vs 36 characters)
- Case-insensitive for user input
"""

import uuid
from typing import Optional


# Crockford Base32 alphabet (32 symbols, excludes I, L, O, U for clarity)
ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

# Reverse mapping for decoding
DECODE_MAP = {char: idx for idx, char in enumerate(ALPHABET)}

# Character normalization for case-insensitive and typo-tolerant input
NORMALIZE_MAP = {
    # Lowercase variants
    **{char.lower(): char for char in ALPHABET},
    # Common typos/confusions
    "I": "1",
    "i": "1",
    "L": "1",
    "l": "1",
    "O": "0",
    "o": "0",
    "U": "V",
    "u": "V",
}


def encode_uuid(uuid_obj: uuid.UUID) -> str:
    """
    Encode a UUID to 26-character Crockford Base32 string.

    Args:
        uuid_obj: UUID object to encode

    Returns:
        26-character Crockford Base32 encoded string (uppercase)

    Example:
        >>> import uuid
        >>> u = uuid.UUID('550e8400-e29b-41d4-a716-446655440000')
        >>> encoded = encode_uuid(u)
        >>> len(encoded)
        26
    """
    # Convert UUID to 128-bit integer
    num = uuid_obj.int

    # Encode to Base32 (5 bits per character, 128 bits = 26 chars)
    result = []
    for _ in range(26):
        result.append(ALPHABET[num & 0x1F])  # Get last 5 bits
        num >>= 5  # Shift right by 5 bits

    # Reverse because we built it backwards
    return "".join(reversed(result))


def decode_uuid(encoded: str) -> uuid.UUID:
    """
    Decode a Crockford Base32 string to UUID.

    Args:
        encoded: 26 or 27 character Crockford Base32 string
                 (if 27 chars, check digit is removed automatically)

    Returns:
        UUID object

    Raises:
        ValueError: If encoded string is invalid format

    Example:
        >>> encoded = "3HNMQR8PJSG0C9VWBYTE12"
        >>> u = decode_uuid(encoded)
        >>> isinstance(u, uuid.UUID)
        True
    """
    # Remove check digit if present
    if len(encoded) == 27:
        encoded = encoded[:-1]
    elif len(encoded) != 26:
        raise ValueError(f"Invalid encoded length: {len(encoded)} (expected 26 or 27)")

    # Normalize input (uppercase, handle typos)
    normalized = []
    for char in encoded:
        if char in NORMALIZE_MAP:
            normalized.append(NORMALIZE_MAP[char])
        elif char in ALPHABET:
            normalized.append(char)
        else:
            raise ValueError(f"Invalid character: {char}")

    encoded_normalized = "".join(normalized)

    # Decode from Base32 to integer
    num = 0
    for char in encoded_normalized:
        if char not in DECODE_MAP:
            raise ValueError(f"Invalid character after normalization: {char}")
        num = (num << 5) | DECODE_MAP[char]

    # Convert to UUID
    return uuid.UUID(int=num)


def calculate_check_digit(encoded: str) -> str:
    """
    Calculate check digit for a 26-character encoded UUID.

    The check digit is calculated by summing the position-weighted values
    of each character and taking modulo 32.

    Args:
        encoded: 26-character Crockford Base32 encoded UUID

    Returns:
        Single character check digit

    Example:
        >>> encoded = "3HNMQR8PJSG0C9VWBYTE12"
        >>> check = calculate_check_digit(encoded)
        >>> len(check)
        1
    """
    if len(encoded) != 26:
        raise ValueError(f"Expected 26 characters, got {len(encoded)}")

    # Normalize input
    normalized = []
    for char in encoded:
        if char in NORMALIZE_MAP:
            normalized.append(NORMALIZE_MAP[char])
        elif char in ALPHABET:
            normalized.append(char)
        else:
            raise ValueError(f"Invalid character: {char}")

    encoded_normalized = "".join(normalized)

    # Calculate checksum: sum of (position * value) mod 32
    checksum = 0
    for pos, char in enumerate(encoded_normalized, start=1):
        if char not in DECODE_MAP:
            raise ValueError(f"Invalid character after normalization: {char}")
        value = DECODE_MAP[char]
        checksum += pos * value

    # Return check digit as character from alphabet
    return ALPHABET[checksum % 32]


def generate_id() -> str:
    """
    Generate a new 27-character ID (26 UUID + 1 check digit).

    Returns:
        27-character Crockford Base32 ID with check digit

    Example:
        >>> new_id = generate_id()
        >>> len(new_id)
        27
        >>> validate_id(new_id)
        True
    """
    # Generate random UUID v4
    new_uuid = uuid.uuid4()

    # Encode to Base32
    encoded = encode_uuid(new_uuid)

    # Calculate and append check digit
    check_digit = calculate_check_digit(encoded)

    return encoded + check_digit


def validate_id(id_str: str) -> bool:
    """
    Validate a Crockford Base32 ID (format and checksum).

    Args:
        id_str: 27-character ID to validate

    Returns:
        True if valid, False otherwise

    Example:
        >>> valid_id = generate_id()
        >>> validate_id(valid_id)
        True
        >>> validate_id("INVALID")
        False
    """
    # Check length
    if len(id_str) != 27:
        return False

    try:
        # Normalize input
        normalized = []
        for char in id_str:
            if char in NORMALIZE_MAP:
                normalized.append(NORMALIZE_MAP[char])
            elif char in ALPHABET:
                normalized.append(char)
            else:
                return False

        normalized_str = "".join(normalized)

        # Split encoded part and check digit
        encoded = normalized_str[:26]
        provided_check = normalized_str[26]

        # Validate each character in encoded part
        for char in encoded:
            if char not in DECODE_MAP:
                return False

        # Calculate expected check digit
        expected_check = calculate_check_digit(encoded)

        # Compare
        return provided_check == expected_check

    except (ValueError, IndexError):
        return False


def normalize_id(id_str: str) -> Optional[str]:
    """
    Normalize an ID to canonical form (uppercase, typos corrected).

    Args:
        id_str: ID string to normalize

    Returns:
        Normalized ID string, or None if invalid

    Example:
        >>> normalize_id("3hnmqr8pjsg0c9vwbyte12k")  # lowercase
        '3HNMQR8PJSG0C9VWBYTE12K'
        >>> normalize_id("3HNMQRiPJSG0C9VWBYTE12K")  # i -> 1
        '3HNMQR1PJSG0C9VWBYTE12K'
    """
    if len(id_str) != 27:
        return None

    try:
        # Normalize each character
        normalized = []
        for char in id_str:
            if char in NORMALIZE_MAP:
                normalized.append(NORMALIZE_MAP[char])
            elif char in ALPHABET:
                normalized.append(char)
            else:
                return None

        normalized_str = "".join(normalized)

        # Validate the normalized ID
        if validate_id(normalized_str):
            return normalized_str
        else:
            return None

    except (ValueError, IndexError):
        return None


def get_uuid_from_id(id_str: str) -> Optional[uuid.UUID]:
    """
    Extract UUID from a valid ID string.

    Args:
        id_str: 27-character ID string

    Returns:
        UUID object if valid, None otherwise

    Example:
        >>> valid_id = generate_id()
        >>> u = get_uuid_from_id(valid_id)
        >>> isinstance(u, uuid.UUID)
        True
    """
    # Validate first
    if not validate_id(id_str):
        return None

    try:
        # Decode the UUID part (first 26 characters)
        return decode_uuid(id_str[:26])
    except ValueError:
        return None
