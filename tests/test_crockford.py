"""
Tests for Crockford Base32 ID system.

This test suite validates the UUID encoding, check digit calculation,
ID generation, and validation functions.
"""

import uuid
import pytest
from src.utils.crockford import (
    encode_uuid,
    decode_uuid,
    calculate_check_digit,
    generate_id,
    validate_id,
    normalize_id,
    get_uuid_from_id,
    ALPHABET,
)


class TestEncoding:
    """Tests for UUID encoding to Crockford Base32."""

    def test_encode_uuid_length(self):
        """Encoded UUID should be exactly 26 characters."""
        test_uuid = uuid.uuid4()
        encoded = encode_uuid(test_uuid)
        assert len(encoded) == 26

    def test_encode_uuid_uses_valid_characters(self):
        """Encoded UUID should only use Crockford alphabet."""
        test_uuid = uuid.uuid4()
        encoded = encode_uuid(test_uuid)
        for char in encoded:
            assert char in ALPHABET

    def test_encode_uuid_is_uppercase(self):
        """Encoded UUID should be uppercase."""
        test_uuid = uuid.uuid4()
        encoded = encode_uuid(test_uuid)
        assert encoded == encoded.upper()

    def test_encode_uuid_deterministic(self):
        """Same UUID should always encode to same string."""
        test_uuid = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
        encoded1 = encode_uuid(test_uuid)
        encoded2 = encode_uuid(test_uuid)
        assert encoded1 == encoded2

    def test_encode_uuid_different_for_different_uuids(self):
        """Different UUIDs should encode to different strings."""
        uuid1 = uuid.uuid4()
        uuid2 = uuid.uuid4()
        encoded1 = encode_uuid(uuid1)
        encoded2 = encode_uuid(uuid2)
        assert encoded1 != encoded2


class TestDecoding:
    """Tests for decoding Crockford Base32 to UUID."""

    def test_decode_uuid_from_26_chars(self):
        """Should decode 26-character string to UUID."""
        test_uuid = uuid.uuid4()
        encoded = encode_uuid(test_uuid)
        decoded = decode_uuid(encoded)
        assert decoded == test_uuid

    def test_decode_uuid_from_27_chars(self):
        """Should decode 27-character string (with check digit) to UUID."""
        test_uuid = uuid.uuid4()
        encoded = encode_uuid(test_uuid)
        check = calculate_check_digit(encoded)
        full_id = encoded + check
        decoded = decode_uuid(full_id)
        assert decoded == test_uuid

    def test_decode_invalid_length_raises_error(self):
        """Should raise ValueError for invalid length."""
        with pytest.raises(ValueError, match="Invalid encoded length"):
            decode_uuid("SHORT")

    def test_decode_invalid_character_raises_error(self):
        """Should raise ValueError for invalid characters."""
        # Create exactly 26 characters: 25 valid + 1 invalid
        invalid = "ABCDEFGHJKMNPQRSTVWXYZ012@"
        assert len(invalid) == 26  # Ensure test data is correct
        with pytest.raises(ValueError, match="Invalid character"):
            decode_uuid(invalid)

    def test_encode_decode_roundtrip(self):
        """Encoding then decoding should return original UUID."""
        for _ in range(10):  # Test with 10 random UUIDs
            original = uuid.uuid4()
            encoded = encode_uuid(original)
            decoded = decode_uuid(encoded)
            assert decoded == original


class TestCheckDigit:
    """Tests for check digit calculation."""

    def test_check_digit_is_single_character(self):
        """Check digit should be single character."""
        test_uuid = uuid.uuid4()
        encoded = encode_uuid(test_uuid)
        check = calculate_check_digit(encoded)
        assert len(check) == 1

    def test_check_digit_is_in_alphabet(self):
        """Check digit should be from Crockford alphabet."""
        test_uuid = uuid.uuid4()
        encoded = encode_uuid(test_uuid)
        check = calculate_check_digit(encoded)
        assert check in ALPHABET

    def test_check_digit_deterministic(self):
        """Same input should produce same check digit."""
        test_uuid = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
        encoded = encode_uuid(test_uuid)
        check1 = calculate_check_digit(encoded)
        check2 = calculate_check_digit(encoded)
        assert check1 == check2

    def test_check_digit_invalid_length_raises_error(self):
        """Should raise ValueError for non-26 character input."""
        with pytest.raises(ValueError, match="Expected 26 characters"):
            calculate_check_digit("SHORT")


class TestIDGeneration:
    """Tests for ID generation."""

    def test_generate_id_length(self):
        """Generated ID should be 27 characters."""
        new_id = generate_id()
        assert len(new_id) == 27

    def test_generate_id_uses_valid_characters(self):
        """Generated ID should only use Crockford alphabet."""
        new_id = generate_id()
        for char in new_id:
            assert char in ALPHABET

    def test_generate_id_is_unique(self):
        """Multiple calls should generate different IDs."""
        ids = [generate_id() for _ in range(100)]
        # All IDs should be unique
        assert len(set(ids)) == 100

    def test_generate_id_is_valid(self):
        """Generated ID should pass validation."""
        new_id = generate_id()
        assert validate_id(new_id)


class TestValidation:
    """Tests for ID validation."""

    def test_validate_valid_id(self):
        """Should return True for valid ID."""
        valid_id = generate_id()
        assert validate_id(valid_id) is True

    def test_validate_invalid_length(self):
        """Should return False for wrong length."""
        assert validate_id("SHORT") is False
        assert validate_id("TOOLONGWAYTOOMANYCHARS123456789") is False

    def test_validate_invalid_characters(self):
        """Should return False for invalid characters."""
        # 27 chars with invalid symbols
        invalid = "INVALID@CHARACTER!!!!!!!!!!"
        assert validate_id(invalid) is False

    def test_validate_wrong_checksum(self):
        """Should return False for wrong check digit."""
        # Generate valid ID
        valid_id = generate_id()
        # Corrupt the check digit
        corrupted = valid_id[:-1] + ("0" if valid_id[-1] != "0" else "1")
        assert validate_id(corrupted) is False

    def test_validate_case_insensitive(self):
        """Should accept lowercase IDs."""
        valid_id = generate_id()
        lowercase_id = valid_id.lower()
        assert validate_id(lowercase_id) is True

    def test_validate_handles_typos(self):
        """Should handle common character confusions (i->1, o->0, etc)."""
        # Generate valid ID and replace 1 with i, 0 with o
        valid_id = generate_id()
        typo_id = valid_id.replace("1", "i").replace("0", "o")
        # Should still validate (with normalization)
        assert validate_id(typo_id) is True


class TestNormalization:
    """Tests for ID normalization."""

    def test_normalize_lowercase_to_uppercase(self):
        """Should normalize lowercase to uppercase."""
        valid_id = generate_id()
        lowercase = valid_id.lower()
        normalized = normalize_id(lowercase)
        assert normalized == valid_id

    def test_normalize_fixes_typos(self):
        """Should fix common typos (i->1, l->1, o->0, u->V)."""
        # Create ID with replaceable characters
        valid_id = generate_id()
        # Replace some characters with confusable ones
        typo_id = valid_id.replace("1", "i", 1).replace("0", "o", 1)
        normalized = normalize_id(typo_id)
        # After normalization, should be valid
        assert normalized is not None
        assert validate_id(normalized)

    def test_normalize_invalid_returns_none(self):
        """Should return None for invalid IDs."""
        invalid = "INVALID@CHARACTER!!!!!!!!!!"
        assert normalize_id(invalid) is None

    def test_normalize_wrong_length_returns_none(self):
        """Should return None for wrong length."""
        assert normalize_id("SHORT") is None


class TestUUIDExtraction:
    """Tests for extracting UUID from ID."""

    def test_get_uuid_from_valid_id(self):
        """Should extract UUID from valid ID."""
        # Generate ID from known UUID
        original_uuid = uuid.uuid4()
        encoded = encode_uuid(original_uuid)
        check = calculate_check_digit(encoded)
        full_id = encoded + check

        # Extract UUID
        extracted = get_uuid_from_id(full_id)
        assert extracted == original_uuid

    def test_get_uuid_from_invalid_id_returns_none(self):
        """Should return None for invalid ID."""
        invalid = "INVALIDID123456789012345678"
        assert get_uuid_from_id(invalid) is None

    def test_get_uuid_roundtrip(self):
        """Creating ID from UUID and extracting should return original."""
        original = uuid.uuid4()
        encoded = encode_uuid(original)
        check = calculate_check_digit(encoded)
        full_id = encoded + check
        extracted = get_uuid_from_id(full_id)
        assert extracted == original


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_nil_uuid(self):
        """Should handle nil UUID (all zeros)."""
        nil_uuid = uuid.UUID("00000000-0000-0000-0000-000000000000")
        encoded = encode_uuid(nil_uuid)
        decoded = decode_uuid(encoded)
        assert decoded == nil_uuid

    def test_max_uuid(self):
        """Should handle max UUID (all ones)."""
        max_uuid = uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
        encoded = encode_uuid(max_uuid)
        decoded = decode_uuid(encoded)
        assert decoded == max_uuid

    def test_known_uuid_encoding(self):
        """Test encoding of a known UUID for consistency."""
        # Use a fixed UUID for reproducibility
        test_uuid = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
        encoded = encode_uuid(test_uuid)
        # Verify it's consistent
        assert len(encoded) == 26
        assert all(c in ALPHABET for c in encoded)
        # Decode should return original
        decoded = decode_uuid(encoded)
        assert decoded == test_uuid
