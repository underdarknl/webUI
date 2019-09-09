#!/usr/bin/python

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import sys
import linuxcnc
from classes.machinekitController import MachinekitController

app = Flask(__name__)
CORS(app)

s = linuxcnc.stat()
c = linuxcnc.command()

axes = {
    "x",
    "y",
    "z"
}
controller = MachinekitController(axes)
print("power on: ", controller.power_status())
print("emergency button pressed: ", controller.emergency_status())
print("homed: ", controller.homed_status())
print("ready for mdi commands: ", controller.ready_for_mdi_commands())
print("axes: ", controller.axes_position())
controller.e_stop("E_STOP_RESET")
#print("TEST", controller.mdi_command("G0 X1 Y2 Z-1"))
print("HOME AXES", controller.home_all_axes())


@app.route("/", methods=["GET"])
def get_customer():
    return "Hello world"


@app.route("/status", methods=["GET"])
def machine_status():
    s.poll()
    status = jsonify({"estop_active": bool(s.estop),
                      "machine_power_on": s.enabled, "homed": s.homed})
    return status


@app.route("/get_current_position", methods=["GET"])
def get_axis():
    try:
        s = linuxcnc.stat()
        s.poll()
        axes = {
            "x": s.actual_position[0],
            "y": s.actual_position[1],
            "z": s.actual_position[2]
        }
        response = json.dumps({"current_position": axes,  "axis": s.axes, "estop_active": bool(
            s.estop), "machine_power_on": s.enabled, "homed": s.homed})
        return response
    except linuxcnc.error, detail:
        response = json.dumps({"error": detail})
        sys.exit(1)
        return response


if __name__ == "__main__":
    app.run(debug=True, host='192.168.1.224', port=5000)
