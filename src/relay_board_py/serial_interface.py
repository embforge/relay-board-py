#!/usr/bin/python3
"""serial_interface.py module."""
from __future__ import annotations
import serial  # type: ignore
from serial.tools import list_ports  # type: ignore
from serial.serialutil import PARITY_NONE, PARITY_EVEN  # type: ignore
from typing import List, Optional
import os


class Device():
    """Device class."""

    def __init__(self,
                 port: str,
                 manufacturer: Optional[str] = None,
                 vid: Optional[int] = None,
                 pid: Optional[int] = None,
                 serial_number: Optional[str] = None):
        """Init a Device object."""
        self.port = port
        self.manufacturer = manufacturer
        self.vid_pid = None if (None in [vid, pid]) else f"{vid:0{4}X}{pid:0{4}X}"
        self.serial_number = serial_number
        self.ser = None

    def __repr__(self) -> str:
        """Return string representation of Device object."""
        return str(self.__dict__)

    def open(self, baudrate: int = 115200) -> None:
        """Open wrapper."""
        # self.ser = serial.Serial(self.port, baudrate=baudrate)
        # https://github.com/pyserial/pyserial/issues/124
        self.ser = serial.Serial()
        self.ser.port = self.port  # type: ignore
        self.ser.baudrate = baudrate  # type: ignore
        if (os.name == 'nt'):
            # On Windows set the default RTS/DTR state before opening the port
            # On Linux, this would trigger a reset
            self.set_rts(True)
            self.set_dtr(True)
        self.ser.open()  # type: ignore

    def close(self) -> None:
        """Close wrapper."""
        if (self.ser is None):
            raise SerialInterfaceException("self.ser is None -> call open() first!")
        self.ser.close()

    def write(self, data: bytes) -> None:
        """Write wrapper."""
        if (self.ser is None):
            raise SerialInterfaceException("self.ser is None -> call open() first!")
        self.ser.write(data)

    def read(self, size: int = 1, timeout: float = 0.1) -> bytes:
        """Read wrapper."""
        if (self.ser is None):
            raise SerialInterfaceException("self.ser is None -> call open() first!")
        self.ser.timeout = timeout
        return self.ser.read(size=size)

    def read_until(self, expected: bytes = b'\n\r', size: Optional[int] = None,
                   timeout: float = 0.1) -> bytes:
        """Read until wrapper."""
        if (self.ser is None):
            raise SerialInterfaceException("self.ser is None -> call open() first!")
        self.ser.timeout = timeout
        return self.ser.read_until(expected=expected, size=size)

    def set_rts(self, level: bool):
        """Set rts pin level."""
        # rts value is inverted level
        value = not level
        if (self.ser is None):
            raise SerialInterfaceException("self.ser is None -> call open() first!")
        self.ser.rts = value

    def set_dtr(self, level: bool):
        """Set dtr pin level."""
        # dtr value is inverted level
        value = not level
        if (self.ser is None):
            raise SerialInterfaceException("self.ser is None -> call open() first!")
        self.ser.dtr = value

    def set_parity_none(self) -> None:
        """Set parity none."""
        if (self.ser is None):
            raise SerialInterfaceException("self.ser is None -> call open() first!")
        self.ser.parity = PARITY_NONE

    def set_parity_even(self) -> None:
        """Set parity even."""
        if (self.ser is None):
            raise SerialInterfaceException("self.ser is None -> call open() first!")
        self.ser.parity = PARITY_EVEN

    @staticmethod
    def by_port(port) -> Device:
        """Create Device object by port."""
        device_list = Device.get_device_list()
        for d in device_list:
            if (d.port == port):
                return d
        raise SerialInterfaceException(f"port {port} not found!")

    @staticmethod
    def by_serial_number(serial_number) -> Device:
        """Create Device object by serial_number."""
        device_list = Device.get_device_list()
        for d in device_list:
            if ((d.serial_number is not None) and (d.serial_number.startswith(serial_number))):
                return d
        raise SerialInterfaceException(f"serial_number {serial_number} not found!")

    @staticmethod
    def get_device_list() -> List[Device]:
        """Get device list of currently connected comports."""
        device_list = []
        com_ports = list_ports.comports()
        for d in com_ports:
            device_list.append(Device(d.device, d.manufacturer, d.vid, d.pid, d.serial_number))
        return device_list


class SerialInterfaceException(Exception):
    """Serial interface exception class."""

    pass
