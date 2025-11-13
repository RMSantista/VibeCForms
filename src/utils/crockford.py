"""Crockford Base32 encoding for VibeCForms UUIDs.

This module implements a modified Crockford Base32 encoding for UUIDs:
- Standard Crockford: Uses modulo 37 with check symbols *~$=U (5 special characters for values 32-36)
- VibeCForms Variation: Uses modulo 32 with check digit from the same 32-character alphabet

Rationale for VibeCForms Variation:
- All IDs are fully URL-safe (no reserved characters)
- Consistent character set throughout entire ID
- Simpler implementation (no special symbol mapping)
- Still provides error detection capability (1 in 32 chance of random error passing)

Trade-off: Slightly reduced error detection (32 vs 37 possible check values),
but sufficient for our use case.

Format:
- Character set: 0123456789ABCDEFGHJKMNPQRSTVWXYZ (32 symbols, excludes I, L, O, U)
- UUID encoding: 128 bits → 26 Base32 characters (⌈128 ÷ 5⌉ = 25.6 → 26)
- Check digit: Uses modulo 32, mapped to same 32-symbol character set
- Final format: 27 characters total (26 encoded + 1 check digit)
- Example: 3HNMQR8PJSG0C9VWBYTE12K where K is the check digit
- URL Safety: ✅ All characters are RFC 3986 unreserved or safe for URLs
"""

import uuid as uuid_module
from typing import Optional

# Crockford Base32 alphabet (excludes I, L, O, U to avoid confusion)
ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

# Reverse mapping for decoding
DECODE_MAP = {char: idx for idx, char in enumerate(ALPHABET)}


def generate_id() -> str:
    """Generate a new Crockford Base32 encoded UUID with check digit.

    Returns:
        str: 27-character Crockford Base32 UUID (26 UUID + 1 check digit)

    Example:
        >>> id1 = generate_id()
        >>> len(id1)
        27
        >>> validate(id1)
        True
    """
    # Generate UUID v4 (128 bits)
    new_uuid = uuid_module.uuid4()

    # Encode to Crockford Base32 with check digit
    return encode_uuid(new_uuid)


def encode_uuid(uuid_obj: uuid_module.UUID) -> str:
    """Encode a UUID object to Crockford Base32 with check digit.

    Args:
        uuid_obj: UUID object to encode

    Returns:
        str: 27-character Crockford Base32 string (26 UUID + 1 check digit)

    Example:
        >>> import uuid
        >>> test_uuid = uuid.UUID('550e8400-e29b-41d4-a716-446655440000')
        >>> encoded = encode_uuid(test_uuid)
        >>> len(encoded)
        27
    """
    # Get UUID as 128-bit integer
    uuid_int = uuid_obj.int

    # Encode to Base32 (26 characters for 128 bits)
    encoded_chars = []
    for _ in range(26):
        encoded_chars.append(ALPHABET[uuid_int % 32])
        uuid_int //= 32

    # Reverse to get most significant digit first
    encoded = "".join(reversed(encoded_chars))

    # Calculate check digit (VibeCForms variation: modulo 32)
    check_digit = _calculate_check_digit(encoded)

    return encoded + check_digit


def decode(crockford_id: str) -> Optional[uuid_module.UUID]:
    """Decode a Crockford Base32 string back to UUID.

    Args:
        crockford_id: 27-character Crockford Base32 string with check digit

    Returns:
        UUID object if valid, None if invalid format or failed validation

    Example:
        >>> encoded = generate_id()
        >>> decoded = decode(encoded)
        >>> decoded is not None
        True
        >>> encode_uuid(decoded) == encoded
        True
    """
    # Normalize to uppercase
    crockford_id = crockford_id.upper()

    # Validate format
    if not _is_valid_format(crockford_id):
        return None

    # Validate check digit
    if not validate(crockford_id):
        return None

    # Remove check digit
    encoded = crockford_id[:26]

    # Decode from Base32
    uuid_int = 0
    for char in encoded:
        uuid_int = uuid_int * 32 + DECODE_MAP[char]

    # Create UUID from integer
    try:
        return uuid_module.UUID(int=uuid_int)
    except ValueError:
        return None


def validate(crockford_id: str) -> bool:
    """Validate a Crockford Base32 UUID with check digit.

    Args:
        crockford_id: 27-character Crockford Base32 string to validate

    Returns:
        bool: True if format and check digit are valid, False otherwise

    Example:
        >>> valid_id = generate_id()
        >>> validate(valid_id)
        True
        >>> validate("INVALID")
        False
        >>> validate("0" * 26 + "1")  # Wrong check digit
        False
    """
    # Normalize to uppercase
    crockford_id = crockford_id.upper()

    # Check format
    if not _is_valid_format(crockford_id):
        return False

    # Extract encoded part and check digit
    encoded = crockford_id[:26]
    provided_check = crockford_id[26]

    # Calculate expected check digit
    expected_check = _calculate_check_digit(encoded)

    return provided_check == expected_check


def _is_valid_format(crockford_id: str) -> bool:
    """Check if string matches Crockford Base32 format.

    Args:
        crockford_id: String to validate

    Returns:
        bool: True if format is valid (27 chars, all in alphabet)
    """
    # Must be exactly 27 characters
    if len(crockford_id) != 27:
        return False

    # All characters must be in alphabet
    return all(char in DECODE_MAP for char in crockford_id)


def _calculate_check_digit(encoded: str) -> str:
    """Calculate check digit for encoded UUID (VibeCForms variation).

    Uses weighted sum modulo 32 to ensure all character positions contribute
    to the checksum, providing better error detection.

    Args:
        encoded: 26-character encoded UUID string

    Returns:
        str: Single character check digit from ALPHABET
    """
    # Calculate weighted sum where each position is weighted by its index + 1
    # This ensures changes at any position affect the checksum
    checksum = 0
    for i, char in enumerate(encoded):
        value = DECODE_MAP[char]
        # Weight by position (1-indexed) to make all positions significant
        checksum += value * (i + 1)

    # Reduce modulo 32 (VibeCForms variation, not 37)
    checksum = checksum % 32

    # Map to alphabet (same character set as main encoding)
    return ALPHABET[checksum]


# Convenience function aliases
def is_valid(crockford_id: str) -> bool:
    """Alias for validate() for more natural API."""
    return validate(crockford_id)


def new_id() -> str:
    """Alias for generate_id() for shorter calls."""
    return generate_id()
