#!/usr/bin/python

import os
from flask import Flask, request, jsonify, flash, redirect, url_for, send_from_directory
from flask_cors import CORS
from flask_mysqldb import MySQL
import json
import linuxcnc
from classes.machinekitController import MachinekitController
from werkzeug.utils import secure_filename
from pprint import pprint

app = Flask(__name__)
CORS(app)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'machinekit'
app.config['MYSQL_DB'] = 'machinekit'

mysql = MySQL(app)

UPLOAD_FOLDER = '/home/machinekit/devel/webUI/files'
ALLOWED_EXTENSIONS = set(['nc'])

axes = {
    "x",
    "y",
    "z"
}
controller = MachinekitController()
# controller.set_home(0)
# controller.set_home(1)
# controller.set_home(2)
# controller.home_all_axes()
# print("TEST", controller.mdi_command("G0 X1 Y2 Z-1"))
# print(controller.set_home(0))


@app.route("/status", methods=["GET"])
def get_axis():
    try:
        return jsonify({
            "machineStatus": {
                "eStopEnabled": controller.emergency_status(),
                "powerEnabled": controller.power_status(),
                "homed": controller.homed_status(),
                "position": controller.axes_position(),
                "velocity": controller.velocity(),
                "spindle_speed": controller.spindle_speed()
            }
        })
    except Exception as e:
        return jsonify({
            "error": str(e)
        })


@app.route("/set_machine_status", methods=["POST"])
def set_status():
    try:
        data = request.json
        command = data['command']
        return jsonify(controller.e_stop(command))
    except (KeyError, Exception) as e:
        return jsonify({
            "error": str(e)
        })


@app.route("/send_command", methods=["POST"])
def send_command():
    try:
        data = request.json
        x = data['X']
        y = data['Y']
        z = data['Z']
        controller.mdi_command("G0" + "X" + x + "Y" + y + "Z" + z)

        return jsonify(data)
    except (KeyError, Exception) as e:
        return jsonify({
            "error": str(e)
        })


@app.route("/manual", methods=["POST"])
def manual():
    try:
        data = request.json
        axes = data['axes']
        speed = data['speed']
        increment = data['increment']
        command = data['command']

        controller.manual_control(axes, speed, increment, command)
        return jsonify({"data": data, "errors": controller.errors()})
    except (KeyError, Exception) as e:
        return jsonify({
            "error": str(e)
        })


@app.route("/file_upload", methods=["POST"])
def upload():
    try:
        # pprint(vars(request))
        if "file" not in request.files:
            return "No file found"

        print("test")
        file = request.files["file"]
        filename = secure_filename(file.filename)
        cur = mysql.connection.cursor()
        cur.execute(
            """
            SELECT * FROM files 
            WHERE file_name = '%s' """ % filename)

        result = cur.fetchall()

        if len(result) > 0:
            return jsonify({"error": "File with given name already on server"})

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
        return e


if __name__ == "__main__":
    app.run(debug=True, host='192.168.1.224', port=5000)
