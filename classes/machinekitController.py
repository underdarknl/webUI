#!/usr/bin/python
import linuxcnc


class MachinekitController():
    """The Machinekit python interface in a class"""

    def __init__(self):
        self.s = linuxcnc.stat()
        self.c = linuxcnc.command()
        self.e = linuxcnc.error_channel()
        self.axes = self.set_axes()
        self.axes_with_cords = {}

    # Class is split up in getters and setters

    def set_axes(self):
        self.s.poll()
        axesDict = {
            0: "x",
            1: "y",
            2: "z",
            3: "a",
            4: "b",
            5: "c",
            6: "d",
            7: "e",
            8: "f",
            9: "g"
        }

        i = 0
        axesInMachine = []
        while i < self.s.axes:
            axesInMachine.append(axesDict[i])
            i += 1
        return axesInMachine

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

    def acceleration(self):
        """ returns float - default acceleration, reflects the ini entry [TRAJ] DEFAULT_ACCELERATION. """
        self.s.poll()
        return self.s.acceleration

    def active_queue(self):
        """ returns int - number of motions blending.  """
        self.s.poll()
        return self.s.active_queue

    def queue(self):
        self.s.poll()
        return self.s.queue

    def queue_full(self):
        return self.s.queue_full

    def adaptive_feed_enabled(self):
        """ returns True/False - status of adaptive feedrate override (0/1). """
        self.s.poll()
        return self.s.adaptive_feed_enabled

    def ain(self):
        """ returns tuple of floats - current value of the analog input pins """
        self.s.poll()
        return self.s.ain

    def angular_units(self):
        """ returns string - reflects [TRAJ] ANGULAR_UNITS ini value. """
        self.s.poll()
        return self.s.angular_units

    def aout(self):
        """ returns tuple of floats - current value of the analog output pins. """
        self.s.poll()
        return self.s.aout

    def axes_ini(self):
        """ returns string - reflects [TRAJ] AXES ini value. """
        self.s.poll()
        return self.s.axes

    def axis(self):
        """ returns tuple of dicts - reflecting current axis values. See The axis dictionary. """
        self.s.poll()
        return self.s.axis

    def command(self):
        """ returns string - currently executing command. """
        self.s.poll()
        return self.s.command

    def current_line(self):
        """ returns integer - currently executing line, int. """
        self.s.poll()
        return self.s.current_line

    def get_active_file(self):
        """ returns string - currently executing gcode file. """
        self.s.poll()
        return self.s.file

    def joint_actual_position(self):
        """ returns tuple of floats - actual joint positions. """
        self.s.spoll()
        return self.s.joint_actual_position

    def joint_position(self):
        """ returns tuple of floats - Desired joint positions. """
        self.s.poll()
        return self.s.joint_position

    def max_acceleration(self):
        """ returns float - maximum acceleration. reflects [TRAJ] MAX_ACCELERATION. """
        self.s.poll()
        return self.s.max_acceleration

    def max_velocity(self):
        """ returns float - maximum velocity. reflects [TRAJ] MAX_VELOCITY. """
        self.s.poll()
        return self.s.max_velocity

    def spindle_brake(self):
        """ returns integer - value of the spindle brake flag. """
        self.s.poll()
        return self.s.spindle_brake

    def spindle_direction(self):
        """ returns integer - rotational direction of the spindle. forward=1, reverse=-1. """
        self.s.poll()
        return self.s.spindle_direction

    def spindle_enabled(self):
        """ returns integer - value of the spindle enabled flag. """
        self.s.poll()
        return self.s.spindle_enabled

    def axes_position(self):
        """ Loop over axes and return position in { x: 0, y: 0, z: 0 } format """
        self.s.poll()
        i = 0
        while i < len(self.axes):
            self.axes_with_cords[self.axes[i]] = round(
                self.s.axis[i]['input'], 3)
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

    def get_all_vitals(self):
        return {"machineStatus": {
            "eStopEnabled": self.emergency_status(),
                "powerEnabled": self.power_status(),
                "homed": self.homed_status(),
                "position": self.axes_position(),
                "velocity": self.velocity(),
                "spindle_speed": self.spindle_speed()
                }}

    # SETTERS
    def e_stop(self, command):
        """Send a command to the machine. E_STOP, E_STOP_RESET, POWER_ON, POWER_OFF"""
        if command == "E_STOP":
            self.c.state(1)
            self.c.wait_complete()
            if self.emergency_status():
                return {"success": "completed"}
            else:
                return {"errors": "Command executed but machine still not in E_STOP modus"}
        if command == "E_STOP_RESET":
            self.c.state(2)
            self.c.wait_complete()
            if not self.emergency_status():
                return {"success": "completed"}
            else:
                return {"errors": "Command executed but machine still in E_STOP modus"}
        if command == "POWER_ON":
            self.c.state(4)
            self.c.wait_complete()
            if self.power_status():
                return {"success": "200"}
            else:
                return {"errors": "Command executed but machine still not powered on"}
        if command == "POWER_OFF":
            self.c.state(3)
            self.c.wait_complete()
            if not self.power_status():
                return {"succes": "200"}
            else:
                return {"errors": "Command executed but power is still on"}

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

    def set_home(self):
        """ Takes axe as int as parameter """
        i = 0
        for axe in self.axes:
            self.c.home(i)
            self.c.set_home_parameters(i, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            self.c.wait_complete()
            i = i + 1
        return

    def home_all_axes(self):
        """ Return all axes to their given home position """
        self.c.mode(linuxcnc.MODE_MANUAL)
        self.c.wait_complete()
        self.set_home()
        return {"success": "homing in progress"}

    def run_program(self, command):
        if not self.ensure_mode(linuxcnc.MODE_AUTO, linuxcnc.MODE_MDI):
            return {"error": "machine is running"}

        if command == "start":
            return self.task_run(9)
        elif command == "pause":
            return self.task_pause()
        elif command == "stop":
            return self.task_stop()
        else:
            return self.task_resume()

    def task_run(self, start_line):
        self.s.poll()
        if self.s.task_mode != linuxcnc.MODE_AUTO or self.s.interp_state in (linuxcnc.INTERP_READING, linuxcnc.INTERP_WAITING, linuxcnc.INTERP_PAUSED):
            return {"error": "Can't start machine because it is in the middle of a project"}
        self.ensure_mode(linuxcnc.MODE_AUTO)
        return self.c.auto(linuxcnc.AUTO_RUN, 9)

    def task_pause(self, *event):
        self.s.poll()
        if self.s.task_mode != linuxcnc.MODE_AUTO or self.s.interp_state not in (linuxcnc.INTERP_READING, linuxcnc.INTERP_WAITING):
            return {"error": "Machine already paused"}
        self.ensure_mode(linuxcnc.MODE_AUTO)
        self.c.auto(linuxcnc.AUTO_PAUSE)
        return {"success": "pausing"}

    def task_resume(self, *event):
        self.s.poll()
        if not self.s.paused:
            return {"error": "machine already running"}
        if self.s.task_mode not in (linuxcnc.MODE_AUTO, linuxcnc.MODE_MDI):
            return
        self.ensure_mode(linuxcnc.MODE_AUTO, linuxcnc.MODE_MDI)
        self.c.auto(linuxcnc.AUTO_RESUME)
        return {"success": "resuming"}

    def ensure_mode(self, m, *p):
        self.s.poll()
        if self.s.task_mode == m or self.s.task_mode in p:
            return True
        if self.running(do_poll=False):
            return False
        self.c.mode(m)
        self.c.wait_complete()
        return True

    def task_stop(self):
        self.c.abort()
        self.c.wait_complete()
        return {"success": "stopped"}

    def running(self, do_poll=True):
        if do_poll:
            self.s.poll()
        return self.s.task_mode == linuxcnc.MODE_AUTO and self.s.interp_state != linuxcnc.INTERP_IDLE
