#!/usr/bin/python3

import os
import json
import linuxcnc
from pprint import pprint
from flask_cors import CORS
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
from classes.machinekitController import MachinekitController
from flask import Flask, request, jsonify, flash, redirect, url_for, send_from_directory

app = Flask(__name__)
CORS(app)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'machinekit'
app.config['MYSQL_DB'] = 'machinekit'

mysql = MySQL(app)

UPLOAD_FOLDER = '/home/machinekit/devel/webUI/files'
ALLOWED_EXTENSIONS = set(['nc'])

try:
    controller = MachinekitController()
except Exception as e:
    print(e)


@app.route("/status", methods=["GET"])
def get_axis():
    try:
        return jsonify(controller.get_all_vitals())
    except (Exception) as e:
        if str(e) == "emcStatusBuffer invalid err=3":
            return jsonify({"errors": "Machinekit is not running please restart machinekit and then the server"})
        return jsonify({
            "errors": str(e)
        })


@app.route("/return_files", methods=["GET"])
def return_files():
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
        SELECT * FROM files
        """)
        result = cur.fetchall()
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"errors": str(e)})


@app.route("/set_machine_status", methods=["POST"])
def set_status():
    try:
        data = request.json
        command = data['command']
        return jsonify(controller.machine_status(command))
    except (KeyError, Exception) as e:
        return jsonify({
            "errors": str(e)
        })


@app.route("/set_home", methods=["POST"])
def set_home_axes():
    try:
        data = request.json
        command = data['command']
        if command == "home":
            return jsonify(controller.home_all_axes())
        else:
            return jsonify(controller.unhome_all_axes())
    except Exception as e:
        return jsonify({
            "errors": str(e)
        })


@app.route("/control_program", methods=["POST"])
def control_program():
    try:
        data = request.json
        command = data['command']
        return jsonify(controller.run_program(command))
    except Exception as e:
        return jsonify({
            "errors": str(e)
        })


@app.route("/send_command", methods=["POST"])
def send_command():
    try:
        data = request.json
        x = data['X']
        y = data['Y']
        z = data['Z']
        return jsonify(controller.mdi_command("G0" + "X" + x + "Y" + y + "Z" + z))
    except (KeyError, Exception) as e:
        return jsonify({
            "errors": str(e)
        })


@app.route("/manual", methods=["POST"])
def manual():
    try:
        data = request.json
        axes = data['axes']
        speed = data['speed']
        increment = data['increment']

        return jsonify(controller.manual_control(axes, speed, increment))
    except (KeyError, Exception) as e:
        return jsonify({
            "errors": str(e)
        })


@app.route("/spindle", methods=["POST"])
def spindle():
    try:
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

    except(KeyError, Exception) as e:
        return jsonify({
            "errors": str(e)
        })


@app.route("/feed", methods=["POST"])
def feed():
    try:
        data = request.json
        command = data["feedrate"]
        return jsonify(controller.feedoverride(command))

    except(KeyError, Exception) as e:
        return jsonify({
            "errors": str(e)
        })


@app.route("/maxvel", methods=["POST"])
def maxvel():
    try:
        data = request.json
        command = data["velocity"]
        return jsonify(controller.maxvel(command))
    except(KeyError, Exception) as e:
        return jsonify({
            "errors": str(e)
        })


@app.route("/file_upload", methods=["POST"])
def upload():
    try:
        # pprint(vars(request))
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

    except Exception as e:
        return jsonify({"errors": e})


if __name__ == "__main__":
    app.run(debug=True, host='192.168.1.224', port=5000)
