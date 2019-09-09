#!/usr/bin/python
import linuxcnc


class MachinekitController():
    """The Machinekit python interface in a class"""

    def __init__(self):
        """ Constructor """
        self.axes = list(["x", "y", "z"])
        self.axes_with_cords = {}
        self.s = linuxcnc.stat()
        self.c = linuxcnc.command()
        self.e = linuxcnc.error_channel()

    # Class is split up in getters and setters

    def power_status(self):
        # Function that returns if the machine is currently powered on or off

        # Check for errors in the machine
        # error = self.errors()
        # if error:
        #     print(error)

        self.s.poll()
        return bool(self.s.enabled)

    def emergency_status(self):
        # Check if the emergency button is pushed in
        self.s.poll()
        return bool(self.s.estop)

    def homed_status(self):
        # Check if all the axes are homed
        self.s.poll()
        return bool(self.s.homed)

    def axes_position(self):
        # Loop over all the axes the user wants to use and get the current position of these axes
        self.s.poll()
        i = 0
        while i < len(self.axes):
            self.axes_with_cords[self.axes[i]] = round(
                self.s.axis[i]['input'], 4)
            i += 1
        return self.axes_with_cords

    def errors(self):
        # Check if there are any errors in the machine and if so send them to a handler
        error = self.e.poll()
        if error:
            kind, text = error
            if kind in (linuxcnc.NML_ERROR, linuxcnc.OPERATOR_ERROR):
                typus = "error"
                return self.handle_errors(typus, text)
            else:
                typus = "info"
                return self.handle_errors(typus, text)

    def handle_errors(self, typus, errors):
        # Handle errors
        return ("ERRORS: ", errors)

    def ready_for_mdi_commands(self):
        # Check if the machine is ready to recieve commands
        self.s.poll()
        return not self.s.estop and self.s.enabled and self.s.homed and (self.s.interp_state == linuxcnc.INTERP_IDLE)

    # SETTERS

    def e_stop(self, command):
        """Send a command to the machine. E_STOP, E_STOP_RESET, POWER_ON, POWER_OFF"""
        if command == "E_STOP":
            self.c.state(1)
            return "200"
        if command == "E_STOP_RESET":
            self.c.state(2)
            return "200"
        if command == "POWER_ON":
            self.c.state(3)
            return "200"
        if command == "POWER_OFF":
            self.c.state(4)
            return "200"

    def mdi_command(self, command):
        """Send a MDI movement command to the machine, example "G0 Y1 X1 Z-1" """
        # Check if the machine is ready for mdi commands
        machine_ready = self.ready_for_mdi_commands()
        if machine_ready:
            self.c.mode(linuxcnc.MODE_MDI)
            self.c.wait_complete()
            self.c.mdi(command)
        else:
            print("Machine not ready")

    def home_all_axes(self):
        machine_ready = self.ready_for_mdi_commands()
        if machine_ready:
            self.c.mode(linuxcnc.MODE_MANUAL)
            self.c.wait_complete()
            self.c.home(0)
            self.c.home(1)
            self.c.home(2)
        else:
            print("Machine not ready")
