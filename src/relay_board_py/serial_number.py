#!/usr/bin/python3
"""serial_number.py module."""


class SerialNumber(object):
    """SerialNumber class."""

    @staticmethod
    def encode(serial_number: str) -> str:
        """Encode a serial number string."""
        SerialNumber.assert_format(serial_number, 12)

        # construct the encoded serial number
        serial_number_encoded = serial_number[:]

        # for safety, assert the encoded serial number
        SerialNumber.assert_format(serial_number_encoded, 12)

        return serial_number_encoded

    @staticmethod
    def decode(serial_number: str) -> str:
        """Decode a serial number string."""
        SerialNumber.assert_format(serial_number, 12)

        # construct the decoded serial number
        serial_number_decoded = serial_number[:]

        # for safety, assert the decoded serial number
        SerialNumber.assert_format(serial_number_decoded, 12)

        return serial_number_decoded

    @staticmethod
    def assert_format(serial_number: str, expected_len: int) -> None:
        """Assert format of a serial-number."""
        if (len(serial_number) != expected_len):
            raise SerialNumberException(
                f"Invalid serial number {serial_number} length {len(serial_number)}, " +
                f"must be {expected_len}!")
        if (serial_number[0:2] != "RB"):
            raise SerialNumberException(f"Invalid serial number {serial_number}, " +
                                        "must start with 'RB'")


class SerialNumberException(Exception):
    """Serial number exception class."""

    pass
