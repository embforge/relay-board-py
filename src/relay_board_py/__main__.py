#!/usr/bin/python3
"""__main__.py module."""
from .relay_board import RelayBoard
import sys


# Just call the main of RelayBoard
RelayBoard.main(sys.argv[1:])
