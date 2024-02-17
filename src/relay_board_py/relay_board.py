#!/usr/bin/python3
"""relay_board.py module."""
if __package__ is None or __package__ == "":
    from serial_number import SerialNumber  # type: ignore
    from relay_board_hardware import RelayBoardHardware  # type: ignore
    from relay_board_pattern import RelayBoardPattern  # type: ignore
else:
    from .serial_number import SerialNumber
    from .relay_board_hardware import RelayBoardHardware
    from .relay_board_pattern import RelayBoardPattern
import argparse
import sys
from typing import Dict, List, Optional


class RelayBoard():
    """RelayBoard class."""

    REQUEST_PREFIX = "RB+"
    RESPONSE_PREFIX = "+"
    PAYLOAD_SEPARATOR = "="
    MESSAGE_SEPARATOR = "\n"

    def __init__(self, serial_number: str):
        """Init a RelayBoard object."""
        self.serial_number = serial_number
        decoded_serial_number = SerialNumber.decode(serial_number)
        config_identifier = decoded_serial_number[2:4]
        serial_device_number = decoded_serial_number[4:12]
        self.hardware = RelayBoardHardware(config_identifier, serial_device_number)

    def __repr__(self) -> str:
        """Return string representation of RelayBoard object."""
        return str(self.__dict__)

    def get_serial_number(self) -> str:
        """Return serial-number of the relay-board."""
        return self.serial_number

    def open(self) -> None:
        """Open the relay-board."""
        self.hardware.open()

    def close(self) -> None:
        """Close the relay-board."""
        self.hardware.close()

    def reset(self) -> None:
        """Reset the relay-board."""
        self.hardware.reset()

    def print_info(self) -> None:
        """Print meta-data information of the relay-board."""
        print(f"Serial-number:    {self.read_serial_number()}")
        print(f"Hardware-version: {self.read_hardware_version()}")
        print(f"Firmware-version: {self.read_firmware_version()}")

    def request(self, request_header: str, request_payload: str = "", timeout: float = 0.5) -> str:
        """Send request to relay-board and receive response."""
        # create the request string
        request_str = RelayBoard.REQUEST_PREFIX + request_header
        if (len(request_payload) > 0):
            request_str += RelayBoard.PAYLOAD_SEPARATOR + request_payload
        request_str += RelayBoard.MESSAGE_SEPARATOR
        # print("request:\n" + request_str)
        # write request string and read response string
        self.hardware.write_str(request_str)
        response_str = self.hardware.read_until_str(
            expected=RelayBoard.MESSAGE_SEPARATOR, timeout=timeout)
        response_str = response_str.replace(RelayBoard.MESSAGE_SEPARATOR, "")
        # process the response string
        # print("response:\n" + response_str)
        if (not response_str.startswith(RelayBoard.RESPONSE_PREFIX + request_header)):
            raise RelayBoardException(f"Invalid response: \"{response_str}\"")
        # extract the payload (if available)
        if (RelayBoard.PAYLOAD_SEPARATOR not in response_str):
            return ""
        else:
            return response_str.split(RelayBoard.PAYLOAD_SEPARATOR)[1]

    def read_serial_number(self) -> str:
        """Read serial-number from relay-board."""
        return self.request("SERIAL")

    def read_hardware_version(self) -> str:
        """Read hardware-version from relay-board."""
        return self.request("HW")

    def read_firmware_version(self) -> str:
        """Read firmware-version from relay-board."""
        return self.request("FW")

    def write_relay_state(self, state: Dict[str, List[int]]) -> None:
        """Write the relay state."""
        keys = {"open": "O", "close": "C"}
        # first check all keys in state
        for key in state:
            if key not in keys:
                raise RelayBoardException(f"Unknown key \"{key}\"")
        # create the set command
        commands = []
        for key in state:
            for relay in state[key]:
                commands.append(str(relay) + "-" + keys[key])
        if (len(commands) == 0):
            # nothing to do
            return
        # perform the request
        self.request("SET", ",".join(commands))
        # verify the correctness by reading the state back and compare it
        read_state = self.read_relay_state()
        for key in state:
            RelayBoard.assert_subset(state[key], read_state[key])

    def read_relay_state(self) -> Dict[str, List[int]]:
        """Read the relay state."""
        response = self.request("GET")
        state: Dict[str, List[int]] = {"open": [], "close": []}
        relays = response.split(",")
        for relay in relays:
            relay_id = int(relay.split("-")[0])
            key = "close" if relay.split("-")[1] == "C" else "open"
            state[key].append(relay_id)
        return state

    @staticmethod
    def assert_subset(subset: List[int], superset: List[int]):
        """Assert that all entries of subset are in superset."""
        for entry in subset:
            if (entry not in superset):
                raise RelayBoardException(f"Entry {entry} not present in {superset}")

    @staticmethod
    def main(args_list: List[str]):
        """Execute argument parsing and the requested operations."""
        parser = argparse.ArgumentParser(prog="relay_board.py",
                                         description="Control relay-boards: " +
                                         "by serial-number (arguments: -s, -o, -c), " +
                                         "or by json pattern file (argumments: -f, -p)",
                                         epilog="")
        parser.add_argument('-s', '--serial-number', help="Serial-number in single operation mode")
        parser.add_argument('-o', '--open', help="Specify relay ids to be opened \"-o 1,2,3\"")
        parser.add_argument('-c', '--close', help="Specify relay ids to be closed \"-c 1,2,3\"")
        parser.add_argument('-f', '--file', help="File path to json file containing the patterns")
        parser.add_argument('-p', '--pattern', help="Pattern to be used in provided json file")
        parser.add_argument('-r', '--reset', action='store_true',
                            help="Reset relay-board(s) first, before executing the operations")
        parser.add_argument('-i', '--info', action='store_true',
                            help="Print info about relay-board(s)")
        args = parser.parse_args(args_list)

        relay_board_pattern: Optional[RelayBoardPattern] = None
        pattern: Optional[str] = None

        if (args.serial_number is not None):
            # create a RelayBoardPattern object from the serial number
            open = None if args.open is None else list(map(int, args.open.split(",")))
            close = None if args.close is None else list(map(int, args.close.split(",")))
            relay_board_pattern = \
                RelayBoardPattern.from_serial_number(args.serial_number, open, close)
            pattern = None  # uses first pattern by default
        elif (args.file is not None):
            # create a RelayBoardPattern object from the provided file
            relay_board_pattern = RelayBoardPattern.from_file(args.file)
            pattern = args.pattern
        else:
            parser.print_help()
            sys.exit(1)

        serial_numbers = relay_board_pattern.get_serial_numbers()
        # create relay board objects
        relay_boards: List[RelayBoard] = []
        for serial_number in serial_numbers:
            relay_boards.append(RelayBoard(serial_number))
        # perform the actual operations on the relay boards
        for relay_board in relay_boards:
            # open the relay boards
            relay_board.open()
            # print info if required
            if (args.info):
                relay_board.print_info()
            # reset if required
            if (args.reset):
                relay_board.reset()
            # set the relay-board state
            state = relay_board_pattern.get_pattern(relay_board.get_serial_number(), pattern)
            print(state)
            relay_board.write_relay_state(state)
            # close the relay boards
            relay_board.close()


class RelayBoardException(Exception):
    """RelayBoard exception class."""

    pass


if __name__ == "__main__":
    RelayBoard.main(sys.argv[1:])
