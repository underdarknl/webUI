#!/usr/bin/python
import linuxcnc

def checkerrors(f):
    """Decorator that checks if the user requesting the page is logged in."""
    def wrapper(*args, **kwargs):
        errors = f(*args, **kwargs)
        if 'errors' in errors:
            return errors
        else: 
            return {"success": "Command executed"}
    return wrapper


class MachinekitController():
    """The Machinekit python interface in a class"""

    def __init__(self):
        try: 
            self.s = linuxcnc.stat()
            self.c = linuxcnc.command()
            self.e = linuxcnc.error_channel()
            self.axes = self.set_axes()
            self.axes_with_cords = {}
        except linuxcnc.error, detail:
            print "[error]: ", detail

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
        modes = ["MODE_MANUAL","MODE_AUTO", "MODE_MDI"]
        state = self.s.task_mode
        return modes[state - 1]

    def axes_position(self):
        """ Loop over axes and return position in { x: 0, y: 0, z: 0 } format """
        self.s.poll()
        i = 0
        while i < len(self.axes):
            homed = bool(self.s.axis[i]["homed"])
            pos = round(self.s.axis[i]['input'], 3)
            self.axes_with_cords[self.axes[i]] = {"pos": pos, "homed": homed}
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

        if error is not None:
            return {"errors": error[1]}
        else:
            return {}

        

    def ready_for_mdi_commands(self):
        """ Returns bool that represents if the machine is ready for MDI commands """
        self.s.poll()
        return not self.s.estop and self.s.enabled and self.s.homed and (self.s.interp_state == linuxcnc.INTERP_IDLE)

    def get_all_vitals(self):
        self.s.poll()
        return {
            "power": {
                "enabled": self.s.enabled,
                "estop": bool(self.s.estop)
            },
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
                "file": self.s.file,
                "interp_state": self.interp_state(),
                "task_mode": self.task_mode(),
                "feedrate": self.s.feedrate
            },
            "values": {
                "velocity": self.s.velocity,
                "max_velocity": self.s.max_velocity * 60,
                "max_acceleration": self.s.max_acceleration
            }
        }

    # SETTERS
    @checkerrors
    def machine_status(self, command):
        """Toggle estop and power with command estop || power"""
        self.s.poll()
        if command == "estop":
            if self.s.estop == linuxcnc.STATE_ESTOP:
                self.c.state(linuxcnc.STATE_ESTOP_RESET)
            else: 
                self.c.state(linuxcnc.STATE_ESTOP)
                
            self.c.wait_complete()
            return self.errors()
            
      
        if command == "power":
            if self.s.estop == linuxcnc.STATE_ESTOP:
                return {"errors": "Can't turn on machine while it is in E_STOP modus"}
            if self.s.enabled:
                self.c.state(linuxcnc.STATE_OFF)
            else:
                self.c.state(linuxcnc.STATE_ON)
            self.c.wait_complete()
            return self.errors()
        

    @checkerrors
    def mdi_command(self, command):
        """Send a MDI movement command to the machine, example "G0 Y1 X1 Z-1" """
        # Check if the machine is ready for mdi commands
        self.s.poll()

        if not self.s.enabled and not self.s.estop:
            return {"errors": "Cannot execute command when machine is powered off or in E_STOP modus"}
    
        if self.s.interp_state is not linuxcnc.INTERP_IDLE:
            return {"errors": "Cannot execute command when machine interp state isn't idle"}
        #HOMED CHECK DOEN
        for axe in self.axes_with_cords:
            if not self.axes_with_cords[axe]["homed"]:
                return {"errors": "Cannot execute command when axes are not homed"}

        if not self.s.homed:
            return {"errors": "Cannot execute command while not homed"}

        self.ensure_mode(linuxcnc.MODE_MDI)
        self.c.mdi(command)

        return self.errors()

    def manual_control(self, axes, speed, increment):
        """ Manual control the CNC machine with continious transmission. axes=int speed=int in mm  increment=int in mm command=string"""
        self.s.poll()
        if not self.s.enabled and not self.s.estop:
            return {"errors": "Cannot execute command when machine is powered off or in E_STOP modus"}

        if self.s.interp_state is not linuxcnc.INTERP_IDLE:
            return {"errors": "Cannot execute command when machine interp state isn't idle"}

        self.ensure_mode(linuxcnc.MODE_MANUAL)
        self.c.jog(linuxcnc.JOG_INCREMENT, axes, speed, increment)

        return self.errors()

    def home_all_axes(self):
        """ Return all axes to their given home position """
        self.ensure_mode(linuxcnc.MODE_MANUAL)
        self.c.home(-1)
        self.c.wait_complete()
        return self.errors()

    @checkerrors
    def unhome_all_axes(self):
        self.ensure_mode(linuxcnc.MODE_MANUAL)
        self.c.unhome(-1)
        self.c.wait_complete()
        return self.errors()

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

    @checkerrors
    def task_run(self, start_line):
        self.s.poll()
        if self.s.task_mode not in (linuxcnc.MODE_AUTO, linuxcnc.MODE_MDI) or self.s.interp_state in (linuxcnc.INTERP_READING, linuxcnc.INTERP_WAITING, linuxcnc.INTERP_PAUSED):
            return {"errors": "Can't start machine because it is currently running or paused in a project"}
        self.ensure_mode(linuxcnc.MODE_AUTO)
        self.c.auto(linuxcnc.AUTO_RUN, 9)
    
        return self.errors()

    @checkerrors
    def task_pause(self):
        self.s.poll()
        if self.s.interp_state is linuxcnc.INTERP_PAUSED:
            return {"errors": "Machine is already paused."}
        if self.s.task_mode not in (linuxcnc.MODE_AUTO, linuxcnc.MODE_MDI) or self.s.interp_state not in (linuxcnc.INTERP_READING, linuxcnc.INTERP_WAITING):
            return {"errors": "Machine not ready to recieve pause command. Probably because its currently not working on a program"}
        self.ensure_mode(linuxcnc.MODE_AUTO)
        self.c.auto(linuxcnc.AUTO_PAUSE)

        return self.errors()
     

    @checkerrors
    def task_resume(self):
        self.s.poll()
        if self.s.task_mode not in (linuxcnc.MODE_AUTO, linuxcnc.MODE_MDI) or self.s.interp_state is not linuxcnc.INTERP_PAUSED:
            return {"errors": "Machine not ready to resume. Probably because the machine is not paused or not in auto modus"}
        self.ensure_mode(linuxcnc.MODE_AUTO)
        self.c.auto(linuxcnc.AUTO_RESUME)

        return self.errors()

    @checkerrors
    def task_stop(self):
        self.c.abort()
        self.c.wait_complete()

        return self.errors()

    def ensure_mode(self, m, *p):
        self.s.poll()
        if self.s.task_mode == m or self.s.task_mode in p:
            return True
        if self.running(do_poll=False):
            return False
        self.c.mode(m)
        self.c.wait_complete()
        return True


    def running(self, do_poll=True):
        if do_poll:
            self.s.poll()
        return self.s.task_mode == linuxcnc.MODE_AUTO and self.s.interp_state is not linuxcnc.INTERP_IDLE

    @checkerrors
    def spindle_brake(self, command):
        self.s.poll()
        if self.s.spindle_brake == command:
            return {"errors": "Command could not be executed because the spindle_brake is already in this state"}

        if not self.s.enabled and not self.s.estop:
            return {"errors": "Cannot execute command when machine is powered off or in E_STOP modus"}
        
        if self.s.interp_state is not linuxcnc.INTERP_IDLE:
            return {"errors": "Cannot execute command when machine interp state isn't idle"}

        self.ensure_mode(linuxcnc.MODE_MANUAL)
        self.c.brake(command)

        return self.errors()

    @checkerrors
    def spindle_direction(self, command):
        """command takes parameters: spindle_forward, spindle_reverse, spindle_off, spindle_increase, spindle_decrease, spindle_constant"""
        commands = {
            "spindle_forward": linuxcnc.SPINDLE_FORWARD, 
            "spindle_reverse": linuxcnc.SPINDLE_REVERSE, 
            "spindle_off": linuxcnc.SPINDLE_OFF, 
            "spindle_increase": linuxcnc.SPINDLE_INCREASE, 
            "spindle_decrease": linuxcnc.SPINDLE_DECREASE, 
            "spindle_constant": linuxcnc.SPINDLE_CONSTANT }

        self.s.poll()
        if not self.s.enabled and not self.s.estop:
            return {"errors": "Cannot execute command when machine is powered off or in E_STOP modus"}
       
        if self.s.interp_state is not linuxcnc.INTERP_IDLE:
            return {"errors": "Cannot execute command when machine interp state isn't idle"}

        if self.s.spindle_direction == commands[command]:
            return {"errors": "Command could not be executed because the spindle_direction is already in this state"}

        self.ensure_mode(linuxcnc.MODE_MANUAL)
        self.c.spindle(commands[command])

        return self.errors()

    @checkerrors
    def maxvel(self, maxvel):
        """Takes int of maxvel min"""
        self.c.maxvel(maxvel / 60.)
        self.c.wait_complete()

        return self.errors()
    
    @checkerrors
    def spindleoverride(self, value):
        """test"""  
        if value > 1 or value < 0:
            return {"errors": "Value outside of limits"}

        self.c.spindleoverride(value)
        self.c.wait_complete()

        return self.errors()

    @checkerrors
    def feedoverride(self, value):
        if value > 1.2 or value < 0:
            return {"errors": "Value outside of limits"}
        self.s.poll()

        self.c.feedrate(value)
        self.c.wait_complete()

        return self.errors()


