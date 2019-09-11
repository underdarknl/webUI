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
# controller.set_home(0)
# controller.set_home(1)
# controller.set_home(2)
controller.home_all_axes()
# print("TEST", controller.mdi_command("G0 X1 Y2 Z-1"))
# print(controller.set_home(0))


@app.route("/status", methods=["GET"])
def get_axis():
    try:
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
    except Exception as e:
        return jsonify({
            "error": str(e)
        })


@app.route("/set_machine_status", methods=["POST"])
def set_status():
    try:
        data = request.json
        command = data['command']
        return jsonify(controller.e_stop(command))
    except (KeyError, Exception) as e:
        return jsonify({
            "error": str(e)
        })


@app.route("/send_command", methods=["POST"])
def send_command():
    try:
        data = request.json
        x = data['X']
        y = data['Y']
        z = data['Z']
        controller.mdi_command("G0" + "X" + x + "Y" + y + "Z" + z)

        return jsonify(data)
    except (KeyError, Exception) as e:
        return jsonify({
            "error": str(e)
        })


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
    except (KeyError, Exception) as e:
        return jsonify({
            "error": str(e)
        })


@app.route("file_upload", methods=["POST"])
def upload:
    return "test"


if __name__ == "__main__":
    app.run(debug=True, host='192.168.1.224', port=5000)
