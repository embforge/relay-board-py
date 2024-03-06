#!/usr/bin/python3
"""relay_board_hardware.py module."""
if __package__ is None or __package__ == "":
    from serial_interface import Device  # type: ignore
else:
    from .serial_interface import Device
import time


class RelayBoardHardware():
    """RelayBoardHardware class."""

    def __init__(self, config_identifier: str, serial_device_number: str):
        """Init a RelayBoardHardware object."""
        # config_identifier is not used yet, for future purposes
        self.config_identifier: str = config_identifier
        self.serial_device: Device = Device.by_serial_number(serial_device_number)

    def __repr__(self) -> str:
        """Return string representation of RelayBoardHardware object."""
        return str(self.__dict__)

    def open(self) -> None:
        """Open the serial-device."""
        self.serial_device.open(baudrate=115200)
        # rts before dtr, otherwise a reset occurs
        self.serial_device.set_rts(True)
        self.serial_device.set_dtr(True)
        time.sleep(0.02)

    def close(self) -> None:
        """Close the serial-device."""
        self.serial_device.close()

    def write_str(self, s: str) -> None:
        """Write string wrapper."""
        self.serial_device.write(s.encode("ascii"))

    def read_until_str(self, expected: str, size: int = None,
                       timeout: float = 0.1) -> str:
        """Read until string wrapper."""
        b = self.serial_device.read_until(expected.encode("ascii"), size, timeout)
        return b.decode("ascii", errors="ignore")

    def reset(self) -> None:
        """Reset of relay-board mcu."""
        self.serial_device.set_parity_none()
        self.serial_device.set_dtr(True)
        self.serial_device.set_rts(False)
        time.sleep(0.02)
        self.serial_device.set_dtr(True)
        self.serial_device.set_rts(True)
        time.sleep(0.02)
