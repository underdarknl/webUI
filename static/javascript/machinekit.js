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

        document.body.className = "controller no-critical-errors";
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