#!/usr/bin/python3
"""serial_number.py module."""
import hashlib


class SerialNumber(object):
    """SerialNumber class."""

    @staticmethod
    def encode(serial_number: str) -> str:
        """Encode a serial number string."""
        SerialNumber.assert_format(serial_number, 12)

        # crc of all serial number bytes
        crc = Crc8.calculate_cdma2000(serial_number.encode("utf-8"))

        # 64 bits required from hash
        hash = int.from_bytes(Hash.calculate_sha256(crc)[0:8], 'big')

        # base36 decoded integer of serial_number[2:12]
        # max: 73ZZZZZZZZ (base36) -> 722204136308735 (base10)
        #      10100100001101011101000000111111111111111111111111 (base2) -> 50 bits
        serial_number_integer = Base36.decode(serial_number[2:12])

        # perform serial-number-integer XOR hash (max 50 bits set in serial_number_integer)
        serial_number_integer = SerialNumber.xor(serial_number_integer, hash, 50)

        # construct the encoded serial number
        serial_number_encoded = ""
        serial_number_encoded += serial_number[0:2]
        serial_number_encoded += Base36.encode(serial_number_integer, min_num_chars=10)
        serial_number_encoded += Base36.encode(int.from_bytes(crc, 'big'), min_num_chars=2)

        # for safety, assert the encoded serial number
        SerialNumber.assert_format(serial_number_encoded, 14)

        return serial_number_encoded

    @staticmethod
    def decode(serial_number: str) -> str:
        """Decode a serial number string."""
        SerialNumber.assert_format(serial_number, 14)

        # extract the crc from the last two chars
        crc = Base36.decode(serial_number[12:14]).to_bytes(1, "big")

        # 64 bits required from hash
        hash = int.from_bytes(Hash.calculate_sha256(crc)[0:8], 'big')

        # base36 decoded integer of serial_number[2:12]
        serial_number_integer = Base36.decode(serial_number[2:12])

        # perform serial-number-integer XOR hash (with 50 bits)
        serial_number_integer = SerialNumber.xor(serial_number_integer, hash, 50)

        # construct the decoded serial number
        serial_number_decoded = ""
        serial_number_decoded += serial_number[0:2]
        serial_number_decoded += Base36.encode(serial_number_integer, min_num_chars=10)

        # check the crc of the deocded serial number
        crc_actual = Crc8.calculate_cdma2000(serial_number_decoded.encode("utf-8"))
        if (crc != crc_actual):
            raise SerialNumberException(f"Invalid crc {crc.hex()} " +
                                        f"for serial number {serial_number}")

        # for safety, assert the decoded serial number
        SerialNumber.assert_format(serial_number_decoded, 12)

        return serial_number_decoded

    @staticmethod
    def xor(a: int, b: int, num_bits: int) -> int:
        """Perform bitwise XOR operation with num_bits."""
        bitmask = 0
        for i in range(0, num_bits):
            bitmask <<= 1
            bitmask |= 1

        return (a ^ b) & bitmask

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


class Crc8(object):
    """Crc8 class."""

    REFLECT_BIT_ORDER_TABLE = (
        0x00, 0x80, 0x40, 0xC0, 0x20, 0xA0, 0x60, 0xE0,
        0x10, 0x90, 0x50, 0xD0, 0x30, 0xB0, 0x70, 0xF0,
        0x08, 0x88, 0x48, 0xC8, 0x28, 0xA8, 0x68, 0xE8,
        0x18, 0x98, 0x58, 0xD8, 0x38, 0xB8, 0x78, 0xF8,
        0x04, 0x84, 0x44, 0xC4, 0x24, 0xA4, 0x64, 0xE4,
        0x14, 0x94, 0x54, 0xD4, 0x34, 0xB4, 0x74, 0xF4,
        0x0C, 0x8C, 0x4C, 0xCC, 0x2C, 0xAC, 0x6C, 0xEC,
        0x1C, 0x9C, 0x5C, 0xDC, 0x3C, 0xBC, 0x7C, 0xFC,
        0x02, 0x82, 0x42, 0xC2, 0x22, 0xA2, 0x62, 0xE2,
        0x12, 0x92, 0x52, 0xD2, 0x32, 0xB2, 0x72, 0xF2,
        0x0A, 0x8A, 0x4A, 0xCA, 0x2A, 0xAA, 0x6A, 0xEA,
        0x1A, 0x9A, 0x5A, 0xDA, 0x3A, 0xBA, 0x7A, 0xFA,
        0x06, 0x86, 0x46, 0xC6, 0x26, 0xA6, 0x66, 0xE6,
        0x16, 0x96, 0x56, 0xD6, 0x36, 0xB6, 0x76, 0xF6,
        0x0E, 0x8E, 0x4E, 0xCE, 0x2E, 0xAE, 0x6E, 0xEE,
        0x1E, 0x9E, 0x5E, 0xDE, 0x3E, 0xBE, 0x7E, 0xFE,
        0x01, 0x81, 0x41, 0xC1, 0x21, 0xA1, 0x61, 0xE1,
        0x11, 0x91, 0x51, 0xD1, 0x31, 0xB1, 0x71, 0xF1,
        0x09, 0x89, 0x49, 0xC9, 0x29, 0xA9, 0x69, 0xE9,
        0x19, 0x99, 0x59, 0xD9, 0x39, 0xB9, 0x79, 0xF9,
        0x05, 0x85, 0x45, 0xC5, 0x25, 0xA5, 0x65, 0xE5,
        0x15, 0x95, 0x55, 0xD5, 0x35, 0xB5, 0x75, 0xF5,
        0x0D, 0x8D, 0x4D, 0xCD, 0x2D, 0xAD, 0x6D, 0xED,
        0x1D, 0x9D, 0x5D, 0xDD, 0x3D, 0xBD, 0x7D, 0xFD,
        0x03, 0x83, 0x43, 0xC3, 0x23, 0xA3, 0x63, 0xE3,
        0x13, 0x93, 0x53, 0xD3, 0x33, 0xB3, 0x73, 0xF3,
        0x0B, 0x8B, 0x4B, 0xCB, 0x2B, 0xAB, 0x6B, 0xEB,
        0x1B, 0x9B, 0x5B, 0xDB, 0x3B, 0xBB, 0x7B, 0xFB,
        0x07, 0x87, 0x47, 0xC7, 0x27, 0xA7, 0x67, 0xE7,
        0x17, 0x97, 0x57, 0xD7, 0x37, 0xB7, 0x77, 0xF7,
        0x0F, 0x8F, 0x4F, 0xCF, 0x2F, 0xAF, 0x6F, 0xEF,
        0x1F, 0x9F, 0x5F, 0xDF, 0x3F, 0xBF, 0x7F, 0xFF,
    )

    def __init__(self, width: int = 8, poly: int = 0x07, initvalue: int = 0x00,
                 reflect_input: bool = False, reflect_output: bool = False,
                 xor_output: int = 0x00, check_result: int = 0xF4, residue: int = 0x00) -> None:
        """Init Crc8 object."""
        self._width = width
        self._poly = poly
        self._initvalue = initvalue
        self._reflect_input = reflect_input
        self._reflect_output = reflect_output
        self._xor_output = xor_output
        self._check_result = check_result
        self._residue = residue
        self._value = self._initvalue

    def process(self, data: bytes) -> None:
        """Process given data."""
        crc = self._value

        reflect = self._reflect_input
        poly = self._poly
        for byte in data:
            if reflect:
                byte = Crc8.REFLECT_BIT_ORDER_TABLE[byte]
            crc = crc ^ byte
            for i in range(0, 8):
                if crc & 0x80:
                    crc = (crc << 1) ^ poly
                else:
                    crc = (crc << 1)
            crc &= 0xFF
        self._value = crc

    def final(self) -> bytes:
        """Finalize the calculation."""
        crc = self._value
        if self._reflect_output:
            crc = Crc8.reflectbitorder(self._width, crc)
        crc ^= self._xor_output
        return crc.to_bytes(1, "big")

    @staticmethod
    def reflectbitorder(width: int, value: int) -> int:
        """Reflect bit order of the given value according to the given bit width."""
        binstr = ("0" * width + bin(value)[2:])[-width:]
        return int(binstr[::-1], 2)

    @staticmethod
    def calculate_cdma2000(data: bytes) -> bytes:
        """Calculate crc8-cdma2000."""
        obj = Crc8(poly=0x9B, initvalue=0xFF, check_result=0xDA)
        obj.process(data)
        return obj.final()


class Hash(object):
    """Hash class."""

    @staticmethod
    def calculate_sha256(data: bytes) -> bytes:
        """Calculate hash sha256."""
        hash = hashlib.sha256(data).digest()
        return hash


class Base36(object):
    """Base36 class."""

    ALPHABET = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']

    @staticmethod
    def encode(input: int, min_num_chars: int = 0) -> str:
        """Encode an integer."""
        output = ""
        while (input > 0):
            index = input % 36
            input = int(input / 36)
            output = Base36.get_char_from_index(index) + output

        # Pad with 0, until reached min_num_chars
        while (min_num_chars > len(output)):
            output = Base36.get_char_from_index(0) + output

        return output

    @staticmethod
    def decode(input: str) -> int:
        """Decode a string."""
        output = 0
        for i in range(0, len(input)):
            output = output * 36
            output = output + int(Base36.get_index_from_char(input[i]))
        return output

    @staticmethod
    def get_char_from_index(index: int) -> str:
        """Return char of index in ALPHABET."""
        if (index >= len(Base36.ALPHABET)):
            raise Base36Exception(f"Invalid index {index}, must be < {len(Base36.ALPHABET)}!")
        return Base36.ALPHABET[index]

    @staticmethod
    def get_index_from_char(c: str) -> int:
        """Return index of char in ALPHABET."""
        if (len(c) != 1):
            raise Base36Exception("Invalid char size, must be 1!")
        for i in range(0, len(Base36.ALPHABET)):
            if (c == Base36.ALPHABET[i]):
                return i
        raise Base36Exception(f"Invalid char {c}. Must be [0-9/A-Z]!")


class SerialNumberException(Exception):
    """Serial number exception class."""

    pass


class Base36Exception(Exception):
    """Base36 exception class."""

    pass


if __name__ == "__main__":

    serial_number = "RB00D30GR9J1"

    encoded_serial_number = SerialNumber.encode(serial_number)
    decoded_serial_number = SerialNumber.decode(encoded_serial_number)

    print(f"serial_number:         {serial_number}")
    print(f"encoded_serial_number: {encoded_serial_number}")
    print(f"decoded_serial_number: {decoded_serial_number}")
