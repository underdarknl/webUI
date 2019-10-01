from flask import Flask, jsonify
from flask_socketio import SocketIO, send, emit
import eventlet
import linuxcnc
from classes.machinekitController import MachinekitController


eventlet.monkey_patch()
app = Flask(__name__)
app.config["SECRET_KEY"] = "very-secret"
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")


try:
    controller = MachinekitController()
except Exception as e:
    print("Machinekit is not running")


@socketio.on("connect")
def client_connect():
    print("Client connected")


@socketio.on('message')
def handle_message(message):
    print('received message: ')
    print(message)


@socketio.on("vitals")
def vitals():
    emit("vitals", {"success": controller.get_all_vitals()})


if __name__ == "__main__":
    app.debug = True
    socketio.run(app, host="192.168.1.224")
