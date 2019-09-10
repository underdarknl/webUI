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
#print("TEST", controller.mdi_command("G0 X1 Y2 Z-1"))
# print(controller.set_home(0))


@app.route("/get_current_position", methods=["GET"])
def get_axis():
    return jsonify({
        "machineStatus": {
            "eStopEnabled": controller.emergency_status(),
            "powerEnabled": controller.power_status(),
            "homed": controller.homed_status(),
            "position": controller.axes_position(),
            "velocity": controller.velocity(),
            "spindle_speed": controller.spindle_speed()
        }
    })


@app.route("/set_machine_status", methods=["POST"])
def set_status():
    try:
        data = request.json
        command = data['command']
        return jsonify(controller.e_stop(command))
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


@app.route("/manual", methods=["POST"])
def manual():
    try:
        data = request.json
        axes = data['axes']
        speed = data['speed']
        increment = data['increment']
        command = data['command']

        controller.manual_control(axes, speed, increment, command)
        return jsonify({"data": data, "errors": controller.errors()})
    except KeyError:
        return "error"


if __name__ == "__main__":
    app.run(debug=True, host='192.168.1.224', port=5000)
