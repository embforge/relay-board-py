#!/usr/bin/python3
"""relay_board_pattern.py module."""
from __future__ import annotations
if __package__ is None or __package__ == "":
    from serial_number import SerialNumber  # type: ignore
else:
    from .serial_number import SerialNumber
import json
from typing import List, Dict, Any, Optional


class RelayBoardPattern():
    """RelayBoardPattern class."""

    def __init__(self, aliases: Dict[str, str], patterns: Dict[str, Any]):
        """Init a RelayBoardPattern object."""
        RelayBoardPattern.assert_aliases_format(aliases)
        RelayBoardPattern.assert_patterns_format(aliases, patterns)
        self.aliases = aliases
        self.patterns = patterns

    def __repr__(self) -> str:
        """Return string representation of RelayBoardConfig object."""
        return str(self.__dict__)

    def get_serial_numbers(self) -> List[str]:
        """Return a list of all serial-numbers available in the pattern."""
        serial_numbers: List[str] = []
        for alias in self.aliases:
            serial_numbers.append(self.aliases[alias])
        return serial_numbers

    def get_pattern(self, serial_number: str, pattern: Optional[str] = None) \
            -> Dict[str, List[int]]:
        """Return the pattern for a serial-number."""
        alias = self.get_alias_by_serial_number(serial_number)
        return self.get_pattern_by_alias(alias, pattern)

    def get_pattern_by_alias(self, alias: str, pattern: Optional[str] = None) \
            -> Dict[str, List[int]]:
        """Return the pattern of an alias."""
        # if None and only one pattern defined, this pattern is automatically used
        if (pattern is None):
            keys = list(self.patterns.keys())
            if (len(keys) != 1):
                raise RelayBoardPatternException(f"Pattern undetermined. Use one of {keys}")
            pattern = keys[0]
        # assert that pattern is available
        if (pattern not in self.patterns):
            raise RelayBoardPatternException(f"Couldn't find pattern {pattern}")
        # search for the pattern and alias
        if alias in self.patterns[pattern]:
            return self.patterns[pattern][alias]
        return {}

    def get_alias_by_serial_number(self, serial_number: str) -> str:
        """Return the alias of a serial-number."""
        for alias in self.aliases:
            if (serial_number == self.aliases[alias]):
                return alias
        raise RelayBoardPatternException(f"Serial number {serial_number} has no alias")

    @staticmethod
    def assert_aliases_format(aliases: Dict[str, str]) -> None:
        """Assert the format of aliases."""
        if (len(aliases.keys()) == 0):
            raise RelayBoardPatternException("No aliases defined")
        # check the serial-number format for all aliases, and also for duplicates
        seen_serial_numbers: List[str] = []
        for alias in aliases:
            serial_number = aliases[alias]
            SerialNumber.decode(serial_number)
            if (serial_number in seen_serial_numbers):
                raise RelayBoardPatternException(f"Duplicate serial-number {serial_number}")
            seen_serial_numbers.append(serial_number)

    @staticmethod
    def assert_patterns_format(aliases: Dict[str, str], patterns: Dict[str, Any]) -> None:
        """Assert the format of patterns."""
        if (len(patterns.keys()) == 0):
            raise RelayBoardPatternException("No patterns defined")

        for p in patterns:
            pattern = patterns[p]
            if (len(pattern.keys()) == 0):
                raise RelayBoardPatternException(f"Pattern {p} empty")
            for alias in pattern:
                if alias not in aliases:
                    raise RelayBoardPatternException(f"alias {alias} not defined")
                states = pattern[alias]
                for state in states:
                    available_states = ["open", "close"]
                    if state not in available_states:
                        raise RelayBoardPatternException(f"Unknown state \"{state}\". " +
                                                         f"Must be one of {available_states}")
                    pins = states[state]
                    for pin in pins:
                        if type(pin) is not int:
                            raise RelayBoardPatternException(f"Invalid pin type {type(pin)}")

    @staticmethod
    def from_file(file: str) -> RelayBoardPattern:
        """Create RelayBoardPattern from file."""
        with open(file, "r") as f:
            j = json.load(f)
        if "aliases" not in j:
            raise RelayBoardPatternException("aliases not in json file")
        if "patterns" not in j:
            raise RelayBoardPatternException("patterns not in json file")

        return RelayBoardPattern(j["aliases"], j["patterns"])

    @staticmethod
    def from_serial_number(serial_number: str,
                           open: Optional[List[int]] = None,
                           close: Optional[List[int]] = None) -> RelayBoardPattern:
        """Create RelayBoardPattern from serial-number."""
        state = {}
        if (open is not None):
            state["open"] = open
        if (close is not None):
            state["close"] = close
        # create a simply named alias and pattern
        aliases = {"A": serial_number}
        patterns = {"P": {"A": state}}
        return RelayBoardPattern(aliases, patterns)


class RelayBoardPatternException(Exception):
    """RelayBoardPattern exception class."""

    pass


if __name__ == "__main__":
    pattern = RelayBoardPattern.from_file("../examples/example_pattern_multiple.json")
    print(pattern)
    print(pattern.get_pattern(pattern.get_serial_numbers()[0], "P1"))
