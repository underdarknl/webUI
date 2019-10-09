import time
import random
import logging
import eventlet
import linuxcnc
from flask_mysqldb import MySQL
from flask import Flask, jsonify
from flask_socketio import SocketIO, send, emit
from classes.machinekitController import MachinekitController
# halcmd setp hal_manualtoolchange.change_button true

host = "192.168.1.116"
eventlet.monkey_patch()
app = Flask(__name__)

app.config["SECRET_KEY"] = "very-secret"
api_token = "test_secret"

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'machinekit'
app.config['MYSQL_DB'] = 'machinekit'

mysql = MySQL(app)

UPLOAD_FOLDER = '/home/machinekit/devel/webUI/files'
ALLOWED_EXTENSIONS = set(['nc'])

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
file_handler = logging.FileHandler('logfile.log')
formatter = logging.Formatter(
    '%(asctime)s : %(levelname)s : %(name)s : %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

file_queue = []

socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

machinekit_down = False
try:
    controller = MachinekitController()
except Exception as e:
    machinekit_down = True
    print("Machinekit is not running")


@socketio.on("connect")
def client_connect():
    print("Client connected")
    emit("connected", {"success": "test"})


@socketio.on('message')
def handle_message(message):
    print('received message:')
    print(message)


@socketio.on('set-status')
def toggle_estop(command):
    controller.machine_status(command)
    emit("vitals", controller.get_all_vitals())


@socketio.on('set-home')
def toggle_estop(command):
    if command == "home":
        controller.home_all_axes()
    else:
        controller.unhome_all_axes()

    emit("vitals", controller.get_all_vitals())


@socketio.on("vitals")
def vitals():
    if machinekit_down:
        emit("vitals", {"errors": "machinekit is not running"})
    else:
        emit("vitals", controller.get_all_vitals())


if __name__ == "__main__":
    app.debug = True
    socketio.run(app, host=host)
