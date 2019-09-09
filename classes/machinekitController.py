#!/usr/bin/python
import linuxcnc


class MachinekitController():
    """The Machinekit python interface in a class"""

    def __init__(self, axes):
        """ Constructor """
        self.axes = axes
        self.s = linuxcnc.stat()
        self.c = linuxcnc.command()

    # Class is split up in getters and setters
    def machine_power_status(self):
        # Function that returns if the machine is currently powered on or off
        self.s.poll()
        return bool(self.s.enabled)

    def machine_emergency_status(self):
        self.s.poll()
        return bool(self.s.estop)

    def machine_homed_status(self):
        self.s.poll()
        return bool(self.s.homed)
