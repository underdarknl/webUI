#!/usr/bin/python
import linuxcnc


class MachinekitController():
    """The Machinekit python interface in a class"""

    def __init__(self):
        """ Constructor. Basic controllers with X Y Z axes"""
        self.axes = list(["x", "y", "z"])
        self.axes_with_cords = {}
        self.s = linuxcnc.stat()
        self.c = linuxcnc.command()
        self.e = linuxcnc.error_channel()

    # Class is split up in getters and setters

    def power_status(self):
        """ Returns bool from the current power status """
        self.s.poll()
        return bool(self.s.enabled)

    def emergency_status(self):
        """ Returns bool that represents if the emergency button is pressed """
        self.s.poll()
        return bool(self.s.estop)

    def homed_status(self):
        """ Checks if all axes are homed """
        self.s.poll()
        return bool(self.s.homed)

    def velocity(self):
        self.s.poll()
        return self.s.velocity

    def spindle_speed(self):
        self.s.poll()
        return self.s.spindle_speed

    def axes_position(self):
        """ Loop over axes and return position in { x: 0, y: 0, z: 0 } format """
        self.s.poll()
        i = 0
        while i < len(self.axes):
            self.axes_with_cords[self.axes[i]] = round(
                self.s.axis[i]['input'], 4)
            i += 1
        return self.axes_with_cords

    def errors(self):
        """ Check the machine error channel """
        error = self.e.poll()
        if error:
            kind, text = error
            if kind in (linuxcnc.NML_ERROR, linuxcnc.OPERATOR_ERROR):
                typus = "error"
            else:
                typus = "info"
                typus, text
        return error

    def ready_for_mdi_commands(self):
        """ Returns bool that represents if the machine is ready for MDI commands """
        self.s.poll()
        return not self.s.estop and self.s.enabled and self.s.homed and (self.s.interp_state == linuxcnc.INTERP_IDLE)

    # SETTERS

    def e_stop(self, command):
        """Send a command to the machine. E_STOP, E_STOP_RESET, POWER_ON, POWER_OFF"""
        if command == "E_STOP":
            self.c.state(1)
            if self.emergency_status():
                return "200"
            else:
                return "Command executed but machine still not in E_STOP modus"
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
            return "Machine not ready to recieve commands"

    def manual_control(self, axes, speed, increment, command):
        """ Manual control the CNC machine with continious transmission. axes=int speed=int in mm  increment=int in mm command=string"""
        # Check mode 1=MDI 2=AUTO 3=MANUAL
        self.s.poll()
        if self.s.task_mode is not 3:
            self.c.mode(linuxcnc.MODE_MANUAL)
            self.c.wait_complete()

        if command == "STOP":
            return self.c.jog(linuxcnc.JOG_STOP, axes)

        return self.c.jog(linuxcnc.JOG_INCREMENT, axes, speed, increment)

    def set_home(self, axe):
        """ Takes axe as int as parameter """
        return self.c.set_home_parameters(axe, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    def home_all_axes(self):
        """ Return all axes to their given home position """
        machine_ready = self.ready_for_mdi_commands()
        if machine_ready:
            self.c.mode(linuxcnc.MODE_MANUAL)
            self.c.wait_complete()
            self.c.home(0)
            self.c.home(1)
            self.c.home(2)
        else:
            print("Machine not ready")
