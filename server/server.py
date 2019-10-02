from flask import Flask, jsonify
from flask_socketio import SocketIO, send, emit
import eventlet
import random
# import linuxcnc
# from classes.machinekitController import MachinekitController


eventlet.monkey_patch()
app = Flask(__name__)
app.config["SECRET_KEY"] = "very-secret"
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

machinekit_down = False
# try:
#     controller = MachinekitController()
# except Exception as e:
#     print("Machinekit is not running")


def test():
    return {
        "power": {
            "enabled": True,
            "estop": False,
        },
        "position": {"x": {"pos": random.randint(0, 100), "homed": True}, "y": {"pos": random.randint(0, 100), "homed": True}, "z": {"pos": random.randint(0, 100), "homed": True}, "z2": {"pos": random.randint(0, 100), "homed": True}},
        "spindle": {
            "spindle_speed": random.randint(0, 100),
            "spindle_enabled": random.randint(0, 1),
            "spindle_brake": random.randint(0, 1),
            "spindle_direction": random.randint(0, 1),
            "spindle_increasing": random.randint(0, 1),
            "spindle_override_enabled": random.randint(0, 1),
            "spindlerate": random.randint(0, 100),
            "tool_in_spindle": random.randint(0, 1)
        },
        "program": {
            "file": "axis.ngc",
            "interp_state": "INTERP_IDLE",
            "task_mode":  "task_mode",
            "feedrate": random.randint(0, 120),
            "rcs_state": "RCS_WAITING"
        },
        "values": {
            "velocity": random.randint(0, 100),
            "max_velocity": random.randint(0, 100) * 60,
            "max_acceleration": random.randint(0, 100)
        }
    }


@socketio.on("connect")
def client_connect():
    print("Client connected")
    emit("connected", {"success": "test"})


@socketio.on('message')
def handle_message(message):
    print('received message: ')
    print(message)


@socketio.on("vitals")
def vitals():
    if machinekit_down:
        emit("vitals", {"errors": "machinekit is not running"})
    else:
        emit("vitals", test())
    #emit("vitals", {"success": controller.get_all_vitals()})


if __name__ == "__main__":
    app.debug = True
    socketio.run(app, host="127.0.0.1")
