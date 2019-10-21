import os
import sys
import json
import time
import logging
import configparser
from flask_cors import CORS
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
from flask import Flask, request, redirect, abort, escape, render_template

# halcmd setp hal_manualtoolchange.change_button true

config = configparser.ConfigParser()
config.read("default.ini")
app = Flask(__name__)
CORS(app)
app.config['MYSQL_HOST'] = config['mysql']['host']
app.config['MYSQL_USER'] = config['mysql']['user']
app.config['MYSQL_PASSWORD'] = config['mysql']['password']
app.config['MYSQL_DB'] = config['mysql']['database']
api_token = config['security']['token']
mysql = MySQL(app)

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

if config['server']['mockup']:
    print("Mockup")
    machinekit_running = True
    from mockup.machinekitController import MachinekitController
    controller = MachinekitController()
else:
    import linuxcnc
    from classes.machinekitController import MachinekitController
    try:
        controller = MachinekitController()
        machinekit_running = True
    except (linuxcnc.error) as e:
        print("Machinekit is down please start machinekit and then restart the server")
    except Exception as e:
        logger.critical(e)
        sys.exit({"errors": [e]})


def auth(f):
    """ Decorator that checks if the machine returned any errors."""
    def wrapper(*args, **kwargs):
        headers = request.headers
        if not "API_KEY" in headers:
            return {"errors": errorMessages['1']}, 403

        auth = headers.get("API_KEY")
        if auth != api_token:
            return {"errors": errorMessages['1']}, 403

        return f(*args, **kwargs)

    wrapper.__name__ = f.__name__
    return wrapper


def errors(f):
    def errorWrapper(*args, **kwargs):
        try:
            if request.method == "POST":
                if not request.json:
                    raise Exception(errorMessages['4'])

            if machinekit_running == False:
                return {"errors": errorMessages['0']}, 500
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
        except NameError as e:
            return {"errors": e.message}, 404
        except Exception as e:
            return {"errors": {"message": e.message}}

    errorWrapper.__name__ = f.__name__
    return errorWrapper


@app.route("/", methods=['GET'])
def home():
    """Landing page."""
    return render_template('/index.html')


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
        raise ValueError(errorMessages['2'])

    data = request.json
    command = escape(data['command'])
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
        logger.critical(e)
        return {"errors": errorMessages['9']}, 500


@app.route("/machinekit/axes/home", methods=["POST"])
@auth
@errors
def set_home_axes():
    if not "command" in request.json:
        raise ValueError(errorMessages['2'])

    data = request.json
    command = escape(data['command'])
    return controller.home_all_axes(command)


@app.route("/machinekit/program", methods=["POST"])
@auth
@errors
def control_program():
    if not "command" in request.json:
        raise ValueError(errorMessages['2'])

    data = request.json
    command = escape(data['command'])
    return controller.run_program(command)


@app.route("/machinekit/position/mdi", methods=["POST"])
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


@app.route("/machinekit/position/manual", methods=["POST"])
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


@app.route("/machinekit/spindle", methods=["POST"])
@auth
@errors
def set_machinekit_spindle():
    if not "command" in request.json:
        raise ValueError(['2'])
    data = request.json
    command = escape(data["command"])
    return controller.spindle(command)


@app.route("/machinekit/feed", methods=["POST"])
@auth
@errors
def set_machinekit_feedrate():
    if not "feedrate" in request.json:
        raise ValueError(errorMessages['2'])

    data = request.json
    command = float(escape(data["feedrate"]))
    return controller.feedoverride(command)


@app.route("/machinekit/maxvel", methods=["POST"])
@auth
@errors
def maxvel():
    if not "velocity" in request.json:
        raise ValueError(errorMessages['2'])

    data = request.json
    command = escape(data["velocity"])
    return controller.maxvel(float(command))


@app.route("/server/update_file_queue", methods=["POST"])
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
    new_queue = escape(data["new_queue"])
    for item in new_queue:
        if not os.path.isfile(UPLOAD_FOLDER + "/" + item):
            raise NameError(errorMessages['6'])
    file_queue = new_queue
    return {"success": "Queue updated"}


@app.route("/machinekit/toolchange", methods=["GET"])
@auth
@errors
def tool_changer():
    # Dirty fix to bypass toolchange prompt
    os.system("halcmd setp hal_manualtoolchange.change_button true")
    time.sleep(3)
    os.system("halcmd setp hal_manualtoolchange.change_button false")
    return {"success": "Command executed"}


@app.route("/machinekit/halcmd", methods=["POST"])
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


@app.route("/machinekit/open_file", methods=["POST"])
@auth
@errors
def open_file():
    if not "name" in request.json:
        raise ValueError(errorMessages['2'])

    global UPLOAD_FOLDER
    data = request.json
    name = escape(data["name"])
    return controller.open_file(os.path.join(UPLOAD_FOLDER + "/" + name))


@app.route("/server/file_upload", methods=["POST"])
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
    app.run(config['server']['host'], debug=True,
            port=config['server']['port'])
