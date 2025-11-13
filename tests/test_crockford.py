"""Tests for Crockford Base32 UUID encoding.

Tests the VibeCForms variation of Crockford Base32 encoding that uses
modulo 32 for check digits (instead of standard modulo 37).
"""

import uuid
import pytest
from src.utils import crockford


class TestCrockfordEncoding:
    """Test Crockford Base32 encoding functionality."""

    def test_generate_id_length(self):
        """Generated IDs should be exactly 27 characters."""
        new_id = crockford.generate_id()
        assert len(new_id) == 27

    def test_generate_id_format(self):
        """Generated IDs should only contain valid Crockford characters."""
        new_id = crockford.generate_id()
        valid_chars = set("0123456789ABCDEFGHJKMNPQRSTVWXYZ")
        assert all(char in valid_chars for char in new_id)

    def test_generate_id_uniqueness(self):
        """Generated IDs should be unique."""
        ids = [crockford.generate_id() for _ in range(100)]
        assert len(ids) == len(set(ids)), "Generated IDs should be unique"

    def test_generate_id_uppercase(self):
        """Generated IDs should be uppercase."""
        new_id = crockford.generate_id()
        assert new_id == new_id.upper()

    def test_encode_uuid_length(self):
        """Encoded UUIDs should be exactly 27 characters."""
        test_uuid = uuid.uuid4()
        encoded = crockford.encode_uuid(test_uuid)
        assert len(encoded) == 27

    def test_encode_uuid_deterministic(self):
        """Same UUID should always encode to same string."""
        test_uuid = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
        encoded1 = crockford.encode_uuid(test_uuid)
        encoded2 = crockford.encode_uuid(test_uuid)
        assert encoded1 == encoded2

    def test_encode_uuid_known_value(self):
        """Test encoding of a known UUID."""
        # Test with a simple UUID
        test_uuid = uuid.UUID("00000000-0000-0000-0000-000000000000")
        encoded = crockford.encode_uuid(test_uuid)

        # Should be 26 zeros plus check digit
        assert len(encoded) == 27
        assert encoded[:26] == "0" * 26
        # Check digit for all zeros should be '0' (0 % 32 = 0)
        assert encoded[26] == "0"


class TestCrockfordDecoding:
    """Test Crockford Base32 decoding functionality."""

    def test_decode_encoded_uuid(self):
        """Decoding an encoded UUID should return the original UUID."""
        original_uuid = uuid.uuid4()
        encoded = crockford.encode_uuid(original_uuid)
        decoded = crockford.decode(encoded)
        assert decoded == original_uuid

    def test_decode_invalid_length(self):
        """Decoding invalid length string should return None."""
        assert crockford.decode("SHORT") is None
        assert crockford.decode("TOOLONG" * 10) is None

    def test_decode_invalid_characters(self):
        """Decoding string with invalid characters should return None."""
        # Include excluded letters I, L, O, U
        invalid_id = "I" * 26 + "L"
        assert crockford.decode(invalid_id) is None

        # Include special characters
        invalid_id = "!" * 27
        assert crockford.decode(invalid_id) is None

    def test_decode_case_insensitive(self):
        """Decoding should accept lowercase input."""
        original_uuid = uuid.uuid4()
        encoded = crockford.encode_uuid(original_uuid)
        decoded_upper = crockford.decode(encoded.upper())
        decoded_lower = crockford.decode(encoded.lower())
        assert decoded_upper == decoded_lower == original_uuid

    def test_decode_wrong_checksum(self):
        """Decoding with wrong check digit should return None."""
        valid_id = crockford.generate_id()

        # Change the check digit to a different valid character
        corrupted_id = valid_id[:26] + ("1" if valid_id[26] != "1" else "2")

        assert crockford.decode(corrupted_id) is None

    def test_decode_round_trip(self):
        """Multiple encode/decode cycles should preserve UUID."""
        original_uuid = uuid.uuid4()

        # Encode and decode multiple times
        for _ in range(5):
            encoded = crockford.encode_uuid(original_uuid)
            decoded = crockford.decode(encoded)
            assert decoded == original_uuid


class TestCrockfordValidation:
    """Test Crockford Base32 validation functionality."""

    def test_validate_generated_id(self):
        """Generated IDs should always be valid."""
        for _ in range(10):
            new_id = crockford.generate_id()
            assert crockford.validate(new_id)

    def test_validate_invalid_length(self):
        """IDs with wrong length should be invalid."""
        assert not crockford.validate("SHORT")
        assert not crockford.validate("0" * 26)  # Missing check digit
        assert not crockford.validate("0" * 28)  # Too long

    def test_validate_invalid_characters(self):
        """IDs with invalid characters should be invalid."""
        # Excluded letters
        assert not crockford.validate("I" * 27)
        assert not crockford.validate("L" * 27)
        assert not crockford.validate("O" * 27)
        assert not crockford.validate("U" * 27)

        # Special characters
        assert not crockford.validate("!" * 27)
        assert not crockford.validate("*" * 27)

    def test_validate_wrong_checksum(self):
        """IDs with wrong check digit should be invalid."""
        valid_id = crockford.generate_id()

        # Corrupt the check digit
        corrupted_id = valid_id[:26] + ("X" if valid_id[26] != "X" else "Y")

        assert not crockford.validate(corrupted_id)

    def test_validate_case_insensitive(self):
        """Validation should accept lowercase input."""
        valid_id = crockford.generate_id()
        assert crockford.validate(valid_id.upper())
        assert crockford.validate(valid_id.lower())

    def test_validate_all_zeros(self):
        """Special case: all zeros with correct check digit."""
        # All zeros UUID should have check digit '0'
        all_zeros = "0" * 27
        assert crockford.validate(all_zeros)


class TestCheckDigitCalculation:
    """Test check digit calculation (VibeCForms variation)."""

    def test_check_digit_range(self):
        """Check digits should always be from valid alphabet."""
        valid_chars = set("0123456789ABCDEFGHJKMNPQRSTVWXYZ")
        for _ in range(100):
            new_id = crockford.generate_id()
            check_digit = new_id[26]
            assert check_digit in valid_chars

    def test_check_digit_deterministic(self):
        """Same UUID should always produce same check digit."""
        test_uuid = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
        check_digits = [crockford.encode_uuid(test_uuid)[26] for _ in range(5)]
        assert len(set(check_digits)) == 1, "Check digit should be deterministic"

    def test_check_digit_detects_errors(self):
        """Check digit should detect most single character changes.

        With modulo 32 checksum, we expect to detect ~97% of single-character errors
        (31 out of 32 possible values will have different checksums).
        """
        original_id = crockford.generate_id()
        assert crockford.validate(original_id)

        errors_detected = 0
        total_tests = 0

        # Try changing each character in the encoded part multiple times
        for i in range(26):
            # Try multiple different characters
            for new_char in ["1", "2", "A", "Z", "9"]:
                if original_id[i] == new_char:
                    continue  # Skip if same as original

                # Change character
                chars = list(original_id)
                chars[i] = new_char
                corrupted_id = "".join(chars)

                total_tests += 1
                if not crockford.validate(corrupted_id):
                    errors_detected += 1

        # Should detect at least 80% of errors (well above 1/32 = 3.125% false positive rate)
        detection_rate = errors_detected / total_tests
        assert (
            detection_rate >= 0.80
        ), f"Only detected {detection_rate:.1%} of errors (expected ≥80%)"


class TestURLSafety:
    """Test URL safety of generated IDs."""

    def test_no_reserved_characters(self):
        """Generated IDs should not contain URL-reserved characters."""
        reserved_chars = set("!*'();:@&=+$,/?#[]")
        for _ in range(50):
            new_id = crockford.generate_id()
            assert not any(char in reserved_chars for char in new_id)

    def test_no_special_symbols(self):
        """Generated IDs should not contain special symbols used in standard Crockford."""
        special_symbols = set("*~$=")
        for _ in range(50):
            new_id = crockford.generate_id()
            assert not any(char in special_symbols for char in new_id)


class TestConvenienceFunctions:
    """Test convenience function aliases."""

    def test_is_valid_alias(self):
        """is_valid() should work like validate()."""
        valid_id = crockford.generate_id()
        assert crockford.is_valid(valid_id) == crockford.validate(valid_id)

        invalid_id = "INVALID"
        assert crockford.is_valid(invalid_id) == crockford.validate(invalid_id)

    def test_new_id_alias(self):
        """new_id() should work like generate_id()."""
        new_id1 = crockford.new_id()
        new_id2 = crockford.generate_id()

        # Both should have same format
        assert len(new_id1) == len(new_id2) == 27
        assert crockford.validate(new_id1)
        assert crockford.validate(new_id2)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_string(self):
        """Empty string should be invalid."""
        assert not crockford.validate("")
        assert crockford.decode("") is None

    def test_none_input(self):
        """None input should be handled gracefully."""
        with pytest.raises((TypeError, AttributeError)):
            crockford.validate(None)
        with pytest.raises((TypeError, AttributeError)):
            crockford.decode(None)

    def test_max_uuid(self):
        """Maximum UUID value should encode/decode correctly."""
        max_uuid = uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
        encoded = crockford.encode_uuid(max_uuid)
        decoded = crockford.decode(encoded)
        assert decoded == max_uuid

    def test_min_uuid(self):
        """Minimum UUID value should encode/decode correctly."""
        min_uuid = uuid.UUID("00000000-0000-0000-0000-000000000000")
        encoded = crockford.encode_uuid(min_uuid)
        decoded = crockford.decode(encoded)
        assert decoded == min_uuid


class TestVibeCFormsVariation:
    """Test that we're using VibeCForms variation (mod 32, not mod 37)."""

    def test_no_special_check_characters(self):
        """Check digits should never be *, ~, $, =, U (standard Crockford symbols)."""
        # Standard Crockford uses these for check values 32-36
        # VibeCForms variation should never generate these
        forbidden_checks = set("*~$=U")

        for _ in range(200):
            new_id = crockford.generate_id()
            check_digit = new_id[26]
            assert (
                check_digit not in forbidden_checks
            ), f"Found forbidden check digit: {check_digit}"

    def test_check_digit_in_alphabet(self):
        """All check digits should be from the main alphabet."""
        valid_alphabet = set("0123456789ABCDEFGHJKMNPQRSTVWXYZ")

        for _ in range(200):
            new_id = crockford.generate_id()
            check_digit = new_id[26]
            assert (
                check_digit in valid_alphabet
            ), f"Check digit {check_digit} not in alphabet"

    def test_modulo_32_distribution(self):
        """Check digits should have roughly uniform distribution over 32 values."""
        check_digits = [crockford.generate_id()[26] for _ in range(1000)]
        unique_checks = set(check_digits)

        # Should see decent variety (at least 20 of 32 possible values)
        assert (
            len(unique_checks) >= 20
        ), f"Poor check digit distribution: {len(unique_checks)} unique values"
