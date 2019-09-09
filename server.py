#!/usr/bin/python

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
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
controller = MachinekitController()
# print("power on: ", controller.power_status())
# print("emergency button pressed: ", controller.emergency_status())
# print("homed: ", controller.homed_status())
# print("ready for mdi commands: ", controller.ready_for_mdi_commands())
# print("axes: ", controller.axes_position())
# controller.e_stop("E_STOP_RESET")
#print("TEST", controller.mdi_command("G0 X1 Y2 Z-1"))
#print("HOME AXES", controller.home_all_axes())


@app.route("/get_current_position", methods=["GET"])
def get_axis():
    return jsonify({
        "current_position": controller.axes_position(),
        "estop_active": controller.emergency_status(),
        "machine_power_on": controller.power_status(),
        "homed": controller.homed_status()
    })


@app.route("/set_machine_status", methods=["POST"])
def set_status():
    try:
        data = request.json
        command = data['command']
        return controller.e_stop(command)
    except KeyError:
        return "Unknow key"


@app.route("/send_command", methods=["POST"])
def send_command():
    try:
        data = request.json
        x = data['X']
        y = data['Y']
        z = data['Z']
        controller.mdi_command("G0" + "X" + x + "Y" + y + "Z" + z)
        return jsonify(data)
    except KeyError:
        return "Unknow key"


if __name__ == "__main__":
    app.run(debug=True, host='192.168.1.224', port=5000)
