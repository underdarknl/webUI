class Request {
    api = "http://192.168.1.116:5000";
    api_key = "test_secret";

    get(url, data = {}) {
        return fetch(this.api + url, {
                method: "GET",
                headers: {
                    "API_KEY": this.api_key
                }
            })
            .then((response) => response.json())
            .then((data) => data)
            .catch((err) => {
                console.log(err);
            });
    }
    post() {

    }
    update() {

    }
}

class Machinekit {
    state = {
        "position": {
            "x": {
                "homed": true,
                "pos": 0
            },
            "y": {
                "homed": true,
                "pos": 0
            },
            "z": {
                "homed": true,
                "pos": 0
            }
        },
        "power": {
            "enabled": true,
            "estop": false
        },
        "program": {
            "feedrate": 1.0,
            "file": "/usr/share/axis/images/axis.ngc",
            "interp_state": "INTERP_IDLE",
            "rcs_state": "RCS_DONE",
            "task_mode": "MODE_MANUAL",
            "tool_change": -1
        },
        "spindle": {
            "spindle_brake": 1,
            "spindle_direction": 0,
            "spindle_enabled": 0,
            "spindle_increasing": 0,
            "spindle_override_enabled": true,
            "spindle_speed": 0.0,
            "spindlerate": 1.0,
            "tool_in_spindle": 0
        },
        "values": {
            "max_acceleration": 508.0,
            "max_velocity": 3200.0,
            "velocity": 0.0
        }
    }
    displayedErrors = [];
    page = "controller";
    interval = 2000;
    isIntervalRunning = false;

    constructor() {
        this.request = new Request();
        this.controlInterval();
    }

    async getMachineVitals() {
        const result = await this.request.get("/machinekit/status");
        if ("errors" in result) {
            return this.errorHandler(result.errors);
        }
        this.state = result;

        this.buildControllerPage();
    }

    buildControllerPage() {
        const {
            power: {
                enabled,
                estop
            },
            program: {
                file,
                interp_state,
                task_mode
            },
            spindle: {
                spindle_speed,
                spindle_brake,
                spindle_direction
            },
            position
        } = this.state;
        document.body.className = "controller no-critical-errors";

        if (file) {
            document.getElementById("current-file").innerHTML = file;
            document.body.classList.add("file-selected");

        } else {
            document.body.classList.add("no-file-selected");
        }

        if (enabled) {
            document.body.classList.add("power-on");
        } else {
            document.body.classList.add("power-off");
        }

        if (estop) {
            document.body.classList.add("estop-enabled");
        } else {
            document.body.classList.add("estop-disabled");
        }

        switch (interp_state) {
            case "INTERP_IDLE":
                document.body.classList.add("interp-idle");
                break;
            case "INTERP_PAUSED":
                document.body.classList.add("interp-paused");
                break;
            case "INTERP_WAITING":
                document.body.classList.add("interp-waiting");
                break;
            case "INTERP_READING":
                document.body.classList.add("interp-reading");
                break;
        }

        switch (task_mode) {
            case "MODE_MDI":
                document.body.classList.add("mode-mdi");
                break;
            case "MODE_MANUAL":
                document.body.classList.add("mode-manual");
                break;
            case "MODE_AUTO":
                document.body.classList.add("mode-auto");
                break;
        }

        document.getElementById("spindle-speed").innerHTML = spindle_speed;
        let axesHomed = 0;
        const totalAxes = Object.keys(position).length;
        if (totalAxes === 3) {
            for (const axe in position) {
                let homed = "";
                let color = "error";
                if (position[axe].homed) {
                    homed = " (H)";
                    color = "success";
                    axesHomed++;
                }
                if (axe == "x") {
                    document.getElementById("x-axe").innerHTML = position[axe].pos + homed;
                    document.getElementById("x-axe").className = color;
                } else if (axe == "y") {
                    document.getElementById("y-axe").innerHTML = position[axe].pos + homed;
                    document.getElementById("y-axe").className = color;
                } else {
                    document.getElementById("z-axe").innerHTML = position[axe].pos + homed;
                    document.getElementById("z-axe").className = color;
                }
            }
        } else {
            console.log("render custom table for axes");
        }

        if (totalAxes === axesHomed) {
            document.body.classList.add("homed");
        } else {
            document.body.classList.add("unhomed");
        }

        if (spindle_brake) {
            document.body.classList.add("spindle-brake-engaged");
        } else {
            document.body.classList.add("spindle-brake-disengaged");
        }

        if (spindle_direction == 1) {
            document.body.classList.add("spindle-forward");
        } else if (spindle_direction == -1) {
            document.body.classList.add("spindle-reverse");
        } else {
            document.body.classList.add("spindle-not-moving");
        }

    }

    fileManager() {
        console.log("Render the file manager");
        document.body.className = "filemanager no-critical-errors";
    }

    errorHandler(error) {
        if (this.displayedErrors.includes(error.message)) {
            return;
        }
        if (error.message == "Machinekit is not running please restart machinekit and then the server!") {
            this.interval = 50000;
            document.body.className = "machinekit-down"
            return;
        }
        if (error.status == 403) {
            console.log("slowing interval. User not authorized");
            this.interval = 50000;
            document.body.className = "not-authorized"
            return;
        }

        this.displayedErrors.push(error.message);
        this.renderErrors();
    }

    renderErrors() {
        const errorElement = document.getElementById("runtime-errors");
        errorElement.innerHTML = "";
        this.displayedErrors.map((value, index) => {
            errorElement.innerHTML += `<p class="error" id="error_executing">${value}<button class="error" id="error-${index}" onclick="machinekit.deleteError(${index})">x</button></p>`;
        });
    }

    deleteError(index) {
        this.displayedErrors.splice(index, 1);
        this.renderErrors();
    }

    navigation(page) {
        console.log(page);
        localStorage.setItem("page", page);
        this.page = page;

        if (page == "controller") {
            this.getMachineVitals();
        } else {
            this.fileManager();
        }
    }

    controlInterval() {
        if (!this.isIntervalRunning) {
            this.isIntervalRunning = true;
        }
        if (this.page == "controller") {
            console.log("get vitals");
            this.getMachineVitals();
        }
        setTimeout(this.controlInterval.bind(this), this.interval)
    }
}

let machinekit = new Machinekit();