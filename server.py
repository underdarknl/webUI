import os
import sys
import json
import logging
import linuxcnc
import time
from flask_cors import CORS
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
from classes.machinekitController import MachinekitController
from flask import Flask, request, flash, redirect, url_for, send_from_directory, abort
# halcmd setp hal_manualtoolchange.change_button true

app = Flask(__name__)
CORS(app)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'machinekit'
app.config['MYSQL_DB'] = 'machinekit'
api_token = "test_secret"

mysql = MySQL(app)

UPLOAD_FOLDER = '/home/machinekit/devel/webUI/files'
ALLOWED_EXTENSIONS = set(['nc'])

port = 12345

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
file_handler = logging.FileHandler('logfile.log')
formatter = logging.Formatter(
    '%(asctime)s : %(levelname)s : %(name)s : %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

file_queue = []
machinekit_running = False

try:
    controller = MachinekitController()
    machinekit_running = True
except Exception as e:
    logger.critical(e)

errorMessages = {
    0: {"message": "Machinekit is not running please restart machinekit and then the server!", "status": 500, "type": "InternalServerError"},
    1: {"message": "Not authorized", "status": 403, "type": "AuthorizationError"},
    2: {"message": "Unknown key", "status": 400, "type": "ValueError"},
    3: {"message": "Request cannot be empty", "status": 400, "type": "ValueError"},
    4: {"message": "Request can only be Content-Type: application/json", "status": 400, "type": "ValueError"}
}


def auth(f):
    """ Decorator that checks if the machine returned any errors."""
    def wrapper(*args, **kwargs):
        headers = request.headers
        if not "API_KEY" in headers:
            return {"errors": errorMessages[1]}, 403

        auth = headers.get("API_KEY")
        if auth != api_token:
            return {"errors": errorMessages[1]}, 403

        return f(*args, **kwargs)

    wrapper.__name__ = f.__name__
    return wrapper


def errors(f):
    def errorWrapper(*args, **kwargs):
        try:
            if request.method == "POST":
                if not request.json:
                    raise Exception(errorMessages[4])
            if machinekit_running == False:
                return {"errors": errorMessages[0]}, 500
            return f(*args, **kwargs)

        except ValueError as e:
            if type(e.message) == str:
                return {"errors": {"message": e.message, "status": 400, "type": "ValueError"}}, 400
            else:
                return {"errors": e.message}, 400
        except RuntimeError as e:
            return {"errors": e.message}, 400
        except KeyError as e:
            return {"errors": {"message": "Unknown key expected: " + e.message, "status": 400, "type": "KeyError"}}, 400
        except Exception as e:
            return {"errors": {"message": e.message}}

    errorWrapper.__name__ = f.__name__
    return errorWrapper


@app.route("/machinekit/status", methods=["GET"])
@auth
@errors
def get_machinekit_status():
    return controller.get_all_vitals()


@app.route("/machinekit/position", methods=["GET"])
@auth
@errors
def get_machinekit_position():
    return controller.axes_position()


@app.route("/machinekit/status", methods=["POST"])
@auth
@errors
def set_machinekit_status():
    if not "command" in request.json:
        raise ValueError(errorMessages[2])

    data = request.json
    command = data['command']
    return controller.machine_status(command)


@app.route("/server/files", methods=["GET"])
@auth
@errors
def return_files():
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
                    SELECT * FROM files
                    """)
        result = cur.fetchall()
        return {"result": result, "file_queue": file_queue}

    except Exception as e:
        return {"errors": {"message": e.message, "status": 500}}, 500


@app.route("/machinekit/axes/home", methods=["POST"])
@auth
@errors
def set_home_axes():
    if not "command" in request.json:
        raise ValueError(errorMessages[2])

    data = request.json
    command = data['command']
    return controller.home_all_axes(command)


@app.route("/machinekit/program", methods=["POST"])
@auth
@errors
def control_program():
    if not "command" in request.json:
        raise ValueError(errorMessages[2])

    data = request.json
    command = data['command']
    return controller.run_program(command)


@app.route("/machinekit/position/mdi", methods=["POST"])
@auth
@errors
def send_command():
    if not "mdi_command" in request.json:
        raise ValueError(errorMessages[2])

    if len(request.json["mdi_command"]) == 0:
        raise ValueError(errorMessages[3])

    data = request.json
    command = data["mdi_command"]
    return controller.mdi_command(command)


@app.route("/machinekit/position/manual", methods=["POST"])
@auth
@errors
def manual():
    if not "axes" in request.json or not "speed" in request.json or not "increment" in request.json:
        raise ValueError(errorMessages[2])

    data = request.json
    axes = data['axes']
    speed = data['speed']
    increment = data['increment']
    return controller.manual_control(axes, speed, increment)


@app.route("/machinekit/spindle", methods=["POST"])
@auth
@errors
def set_machinekit_spindle():
    if not "command" in request.json:
        raise ValueError(errorMessages[2])
    data = request.json
    command = data["command"]
    return controller.spindle(command)


@app.route("/machinekit/feed", methods=["POST"])
@auth
@errors
def set_machinekit_feedrate():
    if not "feedrate" in request.json:
        raise ValueError(errorMessages[2])

    data = request.json
    command = float(data["feedrate"])
    return controller.feedoverride(command)


@app.route("/machinekit/maxvel", methods=["POST"])
@auth
@errors
def maxvel():
    if not "velocity" in request.json:
        raise ValueError(errorMessages[2])

    data = request.json
    command = data["velocity"]
    return controller.maxvel(float(command))


@app.route("/server/update_file_queue", methods=["POST"])
@auth
@errors
def update_file_queue():
    if not "new_queue" in request.json:
        raise ValueError(errorMessages[2])

    global file_queue
    data = request.json
    new_queue = data["new_queue"]
    file_queue = new_queue
    return {"success": "Queue updated"}


@app.route("/tool_change", methods=["GET"])
@auth
@errors
def tool_changer():
    try:
        # Dirty fix to bypass toolchange prompt
        os.system("halcmd setp hal_manualtoolchange.change_button true")
        time.sleep(1)
        os.system("halcmd setp hal_manualtoolchange.change_button false")
        return {"success": "Command executed"}
    except Exception as e:
        return {"errors": e}, 400


@app.route("/open_file", methods=["POST"])
@auth
@errors
def open_file():
    if not "path" in request.json:
        raise ValueError(errorMessages[2])

    data = request.json
    path = data["path"]
    return controller.open_file("/home/machinekit/devel/webUI/files/" + path)


@app.route("/file_upload", methods=["POST"])
@auth
def upload():
    try:
        if "file" not in request.files:
            return "No file found"

        file = request.files["file"]
        filename = secure_filename(file.filename)
        cur = mysql.connection.cursor()
        cur.execute(
            """
            SELECT * FROM files
            WHERE file_name = '%s' """ % filename)

        result = cur.fetchall()

        if len(result) > 0:
            return {"errors": "File with given name already on server"}, 400

        cur.execute("""
            INSERT INTO files (file_name, file_location)
            VALUES (%s, %s)
            """, (filename, UPLOAD_FOLDER)
        )
        mysql.connection.commit()
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        return {"success": "file added"}
    except Exception as e:
        return {"errors": e}, 400


if __name__ == "__main__":
    app.run(debug=True, host='192.168.1.116', port=5000)
