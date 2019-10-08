#!/usr/bin/python3

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
from flask import Flask, request, jsonify, flash, redirect, url_for, send_from_directory

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

try:
    controller = MachinekitController()
except Exception as e:
    print("Machinekit is not running")
    logger.critical(e)
    sys.exit(1)


@app.route("/status", methods=["GET"])
def get_axis():
    try:
        headers = request.headers
        auth = headers.get("API_KEY")
        if auth == api_token:
            return jsonify(controller.get_all_vitals())
        else:
            return jsonify({"errors": "Not authorized"})
    except (Exception) as e:
        if str(e) == "emcStatusBuffer invalid err=3":
            logger.critical(e)
            return jsonify(
                {"errors": "Machinekit is not running please restart machinekit and then the server"})
        logger.critical(e)
        return jsonify({
            "errors": str(e)
        })


@app.route("/return_files", methods=["GET"])
def return_files():
    try:
        headers = request.headers
        auth = headers.get("API_KEY")
        if auth == api_token:
            cur = mysql.connection.cursor()
            cur.execute("""
            SELECT * FROM files
            """)
            result = cur.fetchall()
            return jsonify({"result": result, "file_queue": file_queue})
        else:
            return jsonify({"errors": "Not authorized"})
    except Exception as e:
        return jsonify({"errors": str(e)})


@app.route("/set_machine_status", methods=["POST"])
def set_status():
    try:
        headers = request.headers
        auth = headers.get("API_KEY")
        if auth == api_token:
            data = request.json
            command = data['command']
            return jsonify(controller.machine_status(command))
        else:
            return jsonify({"errors": "Not authorized"})
    except (KeyError, Exception) as e:
        return jsonify({
            "errors": str(e)
        })


@app.route("/set_home", methods=["POST"])
def set_home_axes():
    try:
        headers = request.headers
        auth = headers.get("API_KEY")
        if auth == api_token:
            data = request.json
            command = data['command']
            if command == "home":
                return jsonify(controller.home_all_axes())
            else:
                return jsonify(controller.unhome_all_axes())
        else:
            return jsonify({"errors": "Not authorized"})
    except Exception as e:
        return jsonify({
            "errors": str(e)
        })


@app.route("/control_program", methods=["POST"])
def control_program():
    try:
        headers = request.headers
        auth = headers.get("API_KEY")
        if auth == api_token:
            data = request.json
            command = data['command']
            return jsonify(controller.run_program(command))
        else:
            return jsonify({"errors": "Not authorized"})
    except Exception as e:
        return jsonify({
            "errors": str(e)
        })


@app.route("/send_command", methods=["POST"])
def send_command():
    try:
        headers = request.headers
        auth = headers.get("API_KEY")
        if auth == api_token:
            data = request.json
            command = data["mdi_command"]
            return jsonify(controller.mdi_command(command))
        else:
            return jsonify({"errors": "Not authorized"})
    except (KeyError, Exception) as e:
        return jsonify({
            "errors": str(e)
        })


@app.route("/manual", methods=["POST"])
def manual():
    try:
        headers = request.headers
        auth = headers.get("API_KEY")
        if auth == api_token:
            data = request.json
            axes = data['axes']
            speed = data['speed']
            increment = data['increment']
            return jsonify(controller.manual_control(axes, speed, increment))
        else:
            return jsonify({"errors": "Not authorized"})
    except (KeyError, Exception) as e:
        return jsonify({
            "errors": str(e)
        })


@app.route("/spindle", methods=["POST"])
def spindle():
    try:
        headers = request.headers
        auth = headers.get("API_KEY")
        if auth == api_token:
            data = request.json
            command = data["command"]
            if "spindle_brake" in command:
                return jsonify(controller.spindle_brake(command["spindle_brake"]))
            elif "spindle_direction" in command:
                return jsonify(controller.spindle_direction(command["spindle_direction"]))
            elif "spindle_override" in command:
                return jsonify(controller.spindleoverride(command["spindle_override"]))
            else:
                return jsonify({"error": "Unknown command"})
        else:
            return jsonify({"errors": "Not authorized"})

    except(KeyError, Exception) as e:
        return jsonify({
            "errors": str(e)
        })


@app.route("/feed", methods=["POST"])
def feed():
    try:
        headers = request.headers
        auth = headers.get("API_KEY")
        if auth == api_token:
            data = request.json
            command = data["feedrate"]
            return jsonify(controller.feedoverride(command))
        else:
            return jsonify({"errors": "Not authorized"})

    except(KeyError, Exception) as e:
        return jsonify({
            "errors": str(e)
        })


@app.route("/maxvel", methods=["POST"])
def maxvel():
    try:
        headers = request.headers
        auth = headers.get("API_KEY")
        if auth == api_token:
            data = request.json
            command = data["velocity"]
            return jsonify(controller.maxvel(command))
        else:
            return jsonify({"errors": "Not authorized"})
    except(KeyError, Exception) as e:
        return jsonify({
            "errors": str(e)
        })


@app.route("/update_file_queue", methods=["POST"])
def update_file_queue():
    try:
        headers = request.headers
        auth = headers.get("API_KEY")
        if auth == api_token:
            global file_queue
            data = request.json
            new_queue = data["new_queue"]
            file_queue = new_queue
            return jsonify({"success": "Queue updated"})
        else:
            return jsonify({"errors": "Not authorized"})
    except Exception as e:
        return jsonify({"errors": e})


@app.route("/tool_change", methods=["GET"])
def test():
    try:
        headers = request.headers
        auth = headers.get("API_KEY")
        if auth == api_token:
            # Dirty fix to bypass toolchange prompt
            os.system("halcmd setp hal_manualtoolchange.change_button true")
            time.sleep(1)
            os.system("halcmd setp hal_manualtoolchange.change_button false")
            return jsonify({"success": "Command executed"})
        else:
            return jsonify({"errors": "Not authorized"})
    except Exception as e:
        return jsonify({"errors": e})


@app.route("/open_file", methods=["POST"])
def open_file():
    try:
        headers = request.headers
        auth = headers.get("API_KEY")
        if auth == api_token:
            data = request.json
            path = data["path"]
            return jsonify(controller.open_file("/home/machinekit/devel/webUI/files/" + path))
        else:
            return jsonify({"errors": "Not authorized"})
    except Exception as e:
        return jsonify({"errors": e})


@app.route("/file_upload", methods=["POST"])
def upload():
    try:
        headers = request.headers
        auth = headers.get("API_KEY")
        if auth == api_token:
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
                return jsonify({"errors": "File with given name already on server"})

            cur.execute("""
                INSERT INTO files (file_name, file_location)
                VALUES (%s, %s)
                """, (filename, UPLOAD_FOLDER)
            )
            mysql.connection.commit()
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            return jsonify("File added to database and saved to folder")
        else:
            return jsonify({"errors": "Not authorized"})

    except Exception as e:
        return jsonify({"errors": e})


if __name__ == "__main__":
    app.run(debug=True, host='192.168.1.116', port=5000)
