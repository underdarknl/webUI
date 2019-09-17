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

    def interp_state(self):
        self.s.poll()
        modes = ["INTERP_IDLE", "INTERP_READING", "INTERP_PAUSED", "INTERP_WAITING"]
        state = self.s.interp_state
        return modes[state - 1]
        
        if state is 1:
            return "INTERP_IDLE"
        elif state is 2:
            return "INTERP_READING"
        elif state is 3:
            return "INTERP_PAUSED"
        elif state is 4:
            return "INTERP_WAITING"

    def task_mode(self):
        self.s.poll()
        #Only god knows why this isnt in line with the docs
        modes = ["MODE_MANUAL","MODE_AUTO", "MODE_MDI"]
        state = self.s.task_mode
        return modes[state - 1]

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
        return {"errors": error}

    def ready_for_mdi_commands(self):
        """ Returns bool that represents if the machine is ready for MDI commands """
        self.s.poll()
        return not self.s.estop and self.s.enabled and self.s.homed and (self.s.interp_state == linuxcnc.INTERP_IDLE)

    def get_all_vitals(self):
        self.s.poll()
        return {"status": {
            "power": {
                "enabled": self.s.enabled,
                "estop": bool(self.s.estop)
            },
            "homed": self.s.homed,
            "position": self.axes_position(),
            "spindle": {
               "spindle_speed": self.s.spindle_speed,
               "spindle_enabled": self.s.spindle_enabled,
               "spindle_brake": self.s.spindle_brake,
               "spindle_direction": self.s.spindle_direction,
               "spindle_increasing": self.s.spindle_increasing,
               "spindle_override_enabled": self.s.spindle_override_enabled,
               "spindlerate": self.s.spindlerate,
               "tool_in_spindle": self.s.tool_in_spindle
            },
            "program": {
                "interp_state": self.interp_state(),
                "task_mode": self.task_mode()
            },
            "velocity": self.s.velocity
        }}

    # SETTERS
    def e_stop(self, command):
        """Send a command to the machine. E_STOP, E_STOP_RESET, POWER_ON, POWER_OFF"""
        self.s.poll()
        if command == "E_STOP":
            self.c.state(1)
            self.c.wait_complete()
            if self.s.estop:
                return {"success": "completed"}
            else:
                return {"errors": "Command executed but machine still not in E_STOP modus"}
        if command == "E_STOP_RESET":
            self.c.state(2)
            self.c.wait_complete()
            if not self.s.estop:
                return {"success": "completed"}
            else:
                return {"errors": "Command executed but machine still in E_STOP modus"}
        if command == "POWER_ON":
            self.c.state(4)
            self.c.wait_complete()
            if self.s.enabled:
                return {"success": "200"}
            else:
                return {"errors": "Command executed but machine still not powered on"}
        if command == "POWER_OFF":
            self.c.state(3)
            self.c.wait_complete()
            if not self.s.enabled():
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

    def manual_control(self, axes, speed, increment):
        """ Manual control the CNC machine with continious transmission. axes=int speed=int in mm  increment=int in mm command=string"""
        if not self.power_status() and not self.emergency_status():
            return {"errors": "Cannot execute command when machine is powered off or in E_STOP modus"}

        self.s.poll()
        if self.s.interp_state is not linuxcnc.INTERP_IDLE:
            return {"errors": "Cannot execute command when machine interp state isn't idle"}

        self.ensure_mode(linuxcnc.MODE_MANUAL)
        self.c.jog(linuxcnc.JOG_INCREMENT, axes, speed, increment)

        return {"success": "moving axes"}

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
        errors = self.errors()
        if errors['errors']:
            return errors
        return {"success": "homing in progress"}

    def run_program(self, command):
        if not self.ensure_mode(linuxcnc.MODE_AUTO, linuxcnc.MODE_MDI):
            return {"error": "machine is running or in wrong mode"}

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
            return {"errors": "Can't start machine because it is currently running or paused in a project"}
        self.ensure_mode(linuxcnc.MODE_AUTO)
        self.c.auto(linuxcnc.AUTO_RUN, 9)

        errors = self.errors()
        if errors['errors']:
            return errors
        return {"success": "resuming"}

    def task_pause(self, *event):
        self.s.poll()
        if self.s.interp_state is linuxcnc.INTERP_PAUSED:
            return {"errors": "Machine is already paused."}
        if self.s.task_mode is not linuxcnc.MODE_AUTO or self.s.interp_state not in (linuxcnc.INTERP_READING, linuxcnc.INTERP_WAITING):
            return {"errors": "Machine not ready to recieve pause command. Probably because its currently not working on a program"}
        self.ensure_mode(linuxcnc.MODE_AUTO)
        self.c.auto(linuxcnc.AUTO_PAUSE)

        errors = self.errors()
        if errors['errors']:
            return errors
        return {"success": "pausing"}

    def task_resume(self, *event):
        self.s.poll()
        if self.s.task_mode is not linuxcnc.MODE_AUTO or self.s.interp_state is not linuxcnc.INTERP_PAUSED:
            return {"errors": "Machine not ready to resume. Probably because the machine is not paused or not in auto modus"}
        self.ensure_mode(linuxcnc.MODE_AUTO)
        self.c.auto(linuxcnc.AUTO_RESUME)

        errors = self.errors()
        if errors['errors']:
            return errors
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

        errors = self.errors()
        if errors['errors']:
            return errors
        return {"success": "stopped"}

    def running(self, do_poll=True):
        if do_poll:
            self.s.poll()
        return self.s.task_mode == linuxcnc.MODE_AUTO and self.s.interp_state != linuxcnc.INTERP_IDLE
