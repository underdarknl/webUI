#!/usr/bin/python

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import sys
import linuxcnc 

app = Flask(__name__)
CORS(app)

s = linuxcnc.stat()
c = linuxcnc.command()

# def ok_for_mdi():
#     #Function that checks if the machine is ready to recieve commands
#     s.poll()
#     return not s.estop and s.enabled and s.homed and (s.interp_state == linuxcnc.INTERP_IDLE)

# print(ok_for_mdi())
# if(ok_for_mdi()):
#     c = linuxcnc.command()
#     s.poll()
#     c.set_home_parameters(0, 0, 0, 0, 0, 0, 0, 0, 0, 0,0 ,0)
#     print("Homed: ", s.axis[0]["homed"])
#     print(c.serial)

@app.route("/", methods=["GET"])
def get_customer():
    return "Hello world"

@app.route("/status", methods=["GET"])
def machine_status():
    s.poll()
    status = jsonify({"estop_active": bool(s.estop), "machine_power_on": s.enabled, "homed": s.homed})
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
        response = json.dumps({"current_position": axes,  "axis": s.axes, "estop_active": bool(s.estop), "machine_power_on": s.enabled, "homed": s.homed })
        return response
    except linuxcnc.error, detail:
        response = json.dumps({"error": detail} )
        sys.exit(1)
        return response


if __name__ == "__main__":
    app.run(debug=True, host = '192.168.1.224', port=5000)