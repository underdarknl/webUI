import os
import sys
import json
import time
import logging
import configparser
from flask_cors import CORS
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
from flask import Flask, request, redirect, abort, escape, render_template, jsonify
from routes.status.status import status
from decorators.auth import auth
from decorators.errors import errors
import settings
settings.init()

# halcmd setp hal_manualtoolchange.change_button true

config = configparser.ConfigParser()
config.read("default.ini")
app = Flask(__name__)
CORS(app)
app.config['MYSQL_HOST'] = config['mysql']['host']
app.config['MYSQL_USER'] = config['mysql']['user']
app.config['MYSQL_PASSWORD'] = config['mysql']['password']
app.config['MYSQL_DB'] = config['mysql']['database']
mysql = MySQL(app)

app.register_blueprint(status)

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
file_handler = logging.FileHandler('logfile.log')
formatter = logging.Formatter(
    '%(asctime)s : %(levelname)s : %(name)s : %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

file_queue = []
machinekit_running = False
UPLOAD_FOLDER = '/home/machinekit/devel/webUI/files'

with open("./jsonFiles/errorMessages.json") as f:
    errorMessages = json.load(f)
with open("./jsonFiles/halCommands.json") as f:
    halCommands = json.load(f)

if config['server']['mockup'] == 'true':
    print("Mockup")
    from mockup.machinekitController import MachinekitController
    controller = MachinekitController()
    settings.machinekit_running = True
else:
    import linuxcnc
    from classes.machinekitController import MachinekitController
    try:
        settings.controller = MachinekitController()
        settings.machinekit_running = True
    except (linuxcnc.error) as e:
        print("Machinekit is down please start machinekit and then restart the server")
    except Exception as e:
        logger.critical(e)
        sys.exit({"errors": [e]})


@app.route("/", methods=['GET'])
def home():
    """Landing page."""
    return render_template('/index.html')


# @app.route("/machinekit/position", endpoint='get_machinekit_position', methods=["GET"])
# @auth
# @errors
# def get_machinekit_position():
#     return controller.axes_position()


@app.route("/machinekit/status", endpoint='set_machinekit_status', methods=["POST"])
@auth
@errors
def set_machinekit_status():
    if not "command" in request.json:
        raise ValueError(errorMessages['2'])

    data = request.json
    command = escape(data['command'])
    return controller.machine_status(command)


@app.route("/server/files", endpoint='return_files', methods=["GET"])
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
        logger.critical(e)
        return {"errors": errorMessages['9']}, 500


@app.route("/machinekit/axes/home", endpoint='set_home_axes', methods=["POST"])
@auth
@errors
def set_home_axes():
    if not "command" in request.json:
        raise ValueError(errorMessages['2'])

    data = request.json
    command = escape(data['command'])
    return controller.home_all_axes(command)


@app.route("/machinekit/program", endpoint='control_program', methods=["POST"])
@auth
@errors
def control_program():
    if not "command" in request.json:
        raise ValueError(errorMessages['2'])

    data = request.json
    command = escape(data['command'])
    return controller.run_program(command)


@app.route("/machinekit/position/mdi", endpoint='send_command', methods=["POST"])
@auth
@errors
def send_command():
    if not "mdi_command" in request.json:
        raise ValueError(errorMessages['2'])

    if len(request.json["mdi_command"]) == 0:
        raise ValueError(errorMessages['3'])

    data = request.json
    command = escape(data["mdi_command"])
    return controller.mdi_command(command)


@app.route("/machinekit/position/manual", endpoint='manual', methods=["POST"])
@auth
@errors
def manual():
    if not "axes" in request.json or not "speed" in request.json or not "increment" in request.json:
        raise ValueError(errorMessages['2'])

    data = request.json
    axes = escape(data['axes'])
    speed = escape(data['speed'])
    increment = escape(data['increment'])
    return controller.manual_control(axes, speed, increment)


@app.route("/machinekit/spindle/speed", endpoint='set_machinekit_spindle_speed', methods=["POST"])
@auth
@errors
def set_machinekit_spindle_speed():
    if not "spindle_speed" in request.json:
        raise ValueError(errorMessages['2'])

    data = request.json
    command = escape(data["spindle_speed"])
    return controller.spindle_speed(command)


@app.route("/machinekit/spindle/brake", endpoint='set_machinekit_spindle_brake', methods=["POST"])
@auth
@errors
def set_machinekit_spindle_brake():
    if not "spindle_brake" in request.json:
        raise ValueError(errorMessages['2'])

    data = request.json
    command = escape(data["spindle_brake"])
    return controller.spindle_brake(command)


@app.route("/machinekit/spindle/direction", endpoint='get_machinekit_spindle_direction', methods=["POST"])
@auth
@errors
def set_machinekit_spindle_direction():
    if not "spindle_direction" in request.json:
        raise ValueError(errorMessages['2'])

    data = request.json
    command = escape(data['spindle_direction'])
    return controller.spindle_direction(command)


@app.route("/machinekit/spindle/enabled", endpoint='set_spindle_enabled', methods=["POST"])
@auth
@errors
def set_spindle_enabled():
    if not "spindle_enabled" in request.json:
        raise ValueError(errorMessages['2'])

    data = request.json
    command = escape(data["spindle_enabled"])
    return controller.spindle_enabled(command)


@app.route("/machinekit/spindle/override", endpoint='set_machinekit_spindle_override', methods=["POST"])
@auth
@errors
def set_machinekit_spindle_override():
    if not "spindle_override" in request.json:
        raise ValueError(errorMessages['2'])

    data = request.json
    command = escape(data["spindle_override"])
    return controller.spindleoverride(float(command))


@app.route("/machinekit/feed", endpoint='set_machinekit_feedrate', methods=["POST"])
@auth
@errors
def set_machinekit_feedrate():
    if not "feedrate" in request.json:
        raise ValueError(errorMessages['2'])

    data = request.json
    command = float(escape(data["feedrate"]))
    return controller.feedoverride(command)


@app.route("/machinekit/maxvel", endpoint='maxvel', methods=["POST"])
@auth
@errors
def maxvel():
    if not "velocity" in request.json:
        raise ValueError(errorMessages['2'])

    data = request.json
    command = escape(data["velocity"])
    return controller.maxvel(float(command))


@app.route("/server/update_file_queue", endpoint='update_file_queue', methods=["POST"])
@auth
@errors
def update_file_queue():
    global file_queue
    global UPLOAD_FOLDER

    if not "new_queue" in request.json:
        raise ValueError(errorMessages['2'])
    if not type(file_queue) == list:
        raise ValueError(errorMessages['5'])

    data = request.json
    new_queue = data["new_queue"]

    for item in new_queue:
        if not os.path.isfile(UPLOAD_FOLDER + "/" + escape(item)):
            raise NameError(errorMessages['6'])

    file_queue = new_queue
    return {"success": "Queue updated"}


@app.route("/machinekit/toolchange", endpoint='tool_changer', methods=["GET"])
@auth
@errors
def tool_changer():
    if config['server']['mockup'] == 'true':
        return {"success": "Command executed"}
    else:
        # Dirty fix to bypass toolchange prompt
        os.system("halcmd setp hal_manualtoolchange.change_button true")
        time.sleep(3)
        os.system("halcmd setp hal_manualtoolchange.change_button false")
        return {"success": "Command executed"}


@app.route("/machinekit/halcmd", endpoint='halcmd', methods=["POST"])
@auth
@errors
def halcmd():
    if not "halcmd" in request.json:
        raise ValueError(errorMessages['2'])
    command = request.json["halcmd"]
    i_command = command.split(' ', 1)[0]

    isInList = False
    for item in halCommands:
        if item['command'] == i_command:
            isInList = True
            break
    if not isInList:
        raise ValueError(errorMessages['8'])

    os.system('halcmd ' + command + " > output.txt")
    f = open("output.txt", "r")
    return {"success": f.read()}


@app.route("/machinekit/open_file", endpoint='open_file', methods=["POST"])
@auth
@errors
def open_file():
    if not "name" in request.json:
        raise ValueError(errorMessages['2'])

    global UPLOAD_FOLDER
    data = request.json
    name = escape(data["name"])
    return controller.open_file(os.path.join(UPLOAD_FOLDER + "/" + name))


@app.route("/server/file_upload", endpoint='upload', methods=["POST"])
@auth
@errors
def upload():
    try:
        global UPLOAD_FOLDER

        if "file" not in request.files:
            raise ValueError(errorMessages['5'])

        file = request.files["file"]
        filename = secure_filename(file.filename)
        cur = mysql.connection.cursor()
        cur.execute(
            """
            SELECT * FROM files
            WHERE file_name = '%s' """ % filename)

        result = cur.fetchall()

        if len(result) > 0:
            raise ValueError(errorMessages['7'])

        cur.execute("""
            INSERT INTO files (file_name, file_location)
            VALUES (%s, %s)
            """, (filename, UPLOAD_FOLDER)
        )
        mysql.connection.commit()
        file.save(os.path.join(UPLOAD_FOLDER + "/" + filename))
        return {"success": "file added"}
    except Exception as e:
        logger.critical(e)
        return {"errors": errorMessages['9']}, 500


if __name__ == "__main__":
    app.run('0.0.0.0', debug=True,
            port=5000)
