import os
import sys
import time
import random
import logging
import eventlet
import linuxcnc
from flask_mysqldb import MySQL
from flask import Flask, jsonify
from flask_socketio import SocketIO, send, emit
from werkzeug.utils import secure_filename
from classes.machinekitController import MachinekitController

# halcmd setp hal_manualtoolchange.change_button true

host = "192.168.1.116"

eventlet.monkey_patch()
app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'machinekit'
app.config['MYSQL_DB'] = 'machinekit'

authKey = "test"
mysql = MySQL(app)

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
file_handler = logging.FileHandler('logfile.log')
formatter = logging.Formatter(
    '%(asctime)s : %(levelname)s : %(name)s : %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

file_queue = []
machinekit_down = False
UPLOAD_FOLDER = '/home/machinekit/devel/webUI/files'

try:
    controller = MachinekitController()
except Exception as e:
    logger.critical(e)
    machinekit_down = True


def auth(f):
    def wrapper(*args, **kwargs):
        if args[0]['auth'] == authKey:
            return f(*args, **kwargs)
        else:
            return emit("errors", {"errors": "Not authorized"})
    wrapper.__name__ = f.__name__
    return wrapper


@socketio.on("connect")
def client_connect():
    print("Client connected")
    emit("connected", {"success": "test"})


@socketio.on("vitals")
@auth
def vitals(command):
    if machinekit_down:
        emit("vitals", {"errors": "machinekit is not running"})
    else:
        emit("vitals", controller.get_all_vitals())


@socketio.on('set-status')
@auth
def toggle_estop(command):
    result = controller.machine_status(command['command'])
    if result is not None:
        emit("errors", result)
    vitals({"auth": authKey})


@socketio.on('set-home')
@auth
def toggle_estop(command):
    if command['command'] == "home":
        result = controller.home_all_axes()
    else:
        result = controller.unhome_all_axes()

    if result is not None:
        emit("errors", result)

    vitals({"auth": authKey})


@socketio.on("manual-control")
@auth
def manual_control(command):
    result = controller.manual_control(
        command['axes'], command['speed'], command['increment'])
    if result is not None:
        emit("errors", result)
    vitals({"auth": authKey})


@socketio.on("program-control")
@auth
def program_control(command):
    result = controller.run_program(command['command'])
    if result is not None:
        emit("errors", result)
    vitals({"auth": authKey})


@socketio.on("spindle-control")
@auth
def spindle_control(command):
    if "spindle_brake" in command:
        result = controller.spindle_brake(command["spindle_brake"])
    elif "spindle_direction" in command:
        result = controller.spindle_direction(command["spindle_direction"])
    elif "spindle_override" in command:
        result = controller.spindleoverride(command["spindle_override"])

    if result is not None:
        emit("errors", result)
    vitals({"auth": authKey})


@socketio.on("feed-override")
@auth
def feed_override(command):
    result = controller.feedoverride(command['command'])
    if result is not None:
        emit("errors", result)
    vitals({"auth": authKey})


@socketio.on("maxvel")
@auth
def maxvel(command):
    result = controller.maxvel(command['command'])
    if result is not None:
        emit("errors", result)
    vitals({"auth": authKey})


@socketio.on("send-command")
@auth
def send_command(command):
    result = controller.mdi_command(command['command'])
    if result is not None:
        emit("errors", result)
    vitals({"auth": authKey})


@socketio.on("get-files")
def get_files():
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
        SELECT * FROM files
        """)
        result = cur.fetchall()
        files_on_server = []
        for res in result:
            my_file = res[2] + "/" + res[1]
            if(os.path.isfile(my_file)):
                files_on_server.append(res)
            else:
                cur.execute("""
                            DELETE FROM files WHERE file_id = %s
                """ % res[0])
                cur.connection.commit()

        emit("get-files", {"result": tuple(files_on_server),
                           "file_queue": file_queue})
        vitals({"auth": authKey})
    except Exception as e:
        emit("errors", {"errors": str(e)})
        logger.critical(e)


@socketio.on("update-file-queue")
@auth
def update_file_queue(command):
    global file_queue
    file_queue = command['new_queue']
    get_files()


@socketio.on("tool-changed")
@auth
def tool_changed(command):
    os.system("halcmd setp hal_manualtoolchange.change_button true")
    time.sleep(2)
    os.system("halcmd setp hal_manualtoolchange.change_button false")
    vitals({"auth": authKey})


@socketio.on("open-file")
def open_file():
    try:
        if len(file_queue) == 0:
            controller.open_file("")
        else:
            controller.open_file(UPLOAD_FOLDER + "/" + file_queue[0])
        vitals({"auth": authKey})
    except Exception as e:
        emit("errors", {"errors": str(e)})
        logger.critical(e)


@socketio.on("offset")
def offset(command):
    try:
        controller.set_offset()
    except Exception as e:
        emit("errors", {"errors": str(e)})


@socketio.on("file-upload")
@auth
def upload(data):
    try:
        f = open(os.path.join("./files/" + data['name']), "w")
        f.write(data['file'].encode("utf8"))
        f.close()

        filename = secure_filename(data['name'])
        cur = mysql.connection.cursor()
        cur.execute(
            """
            SELECT * FROM files
            WHERE file_name = '%s' """ % filename)

        result = cur.fetchall()

        if len(result) > 0:
            return emit("errors", {"errors": "File with given name already on server"})

        cur.execute("""
            INSERT INTO files (file_name, file_location)
            VALUES (%s, %s)
            """, (filename, UPLOAD_FOLDER)
        )
        mysql.connection.commit()
        vitals({"auth": authKey})
    except Exception as e:
        emit("errors", {"errors": str(e)})
        logger.critical(e)


if __name__ == "__main__":
    app.debug = True
    socketio.run(app, host=host)
