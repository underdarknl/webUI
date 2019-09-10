const api = "http://192.168.1.224:5000/"

let state = {
    machineStatus: {
        powerEnabled: false,
        eStopEnabled: false,
        homed: false,
        position: {
            "x": 0,
            "y": 0,
            "z": 0
        },
    },
    buttons: {
        emergency: {
            enabled: {
                "emergencyBtn": "DISABLE EMERGENCY STOP"
            },
            disabled: {
                "emergencyBtn": "ENABLE EMERGENCY STOP"
            },
            timedOut: false
        },
        power: {
            enabled: {
                "powerBtn": "turn power off"
            },
            disabled: {
                "powerBtn": "turn power on"
            },
            timeOut: false
        }
    }
}

const request = (url, data, type) => {
    if (type === "POST") {
        return fetch(api + url, {
                method: "POST",
                mode: "cors",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(data)
            })
            .then(response => {
                return response.json()
            })
            .then(data => {
                return data;
            })
    } else {
        return fetch(api + url, {
                method: "GET"
            })
            .then(response => {
                return response.json()
            })
            .then(data => {
                return data

            })
            .catch(error => {
                return {
                    "error": error
                }
            })
    }
}

const getMachineValues = async () => {
    const result = await request("get_current_position", {}, "get");
    if (result.error) {
        return console.log(result.error)
    }

    //Set all data to the current state
    const {
        machineStatus
    } = result

    state = {
        ...state,
        machineStatus
    }

    const {
        eStopEnabled,
        powerEnabled,
        position
    } = state.machineStatus

    const {
        emergency,
        power
    } = state.buttons

    changeHtmlValues(position);

    (eStopEnabled) ? changeHtmlValues(emergency.enabled): changeHtmlValues(emergency.disabled);
    (powerEnabled) ? changeHtmlValues(power.enabled): changeHtmlValues(power.disabled);
}

const update = () => {
    getMachineValues();
}

const changeHtmlValues = (object) => {
    for (const key in object) {
        document.getElementById(key).innerHTML = object[key]
    }
}

const eStopOnClick = async () => {
    const {
        eStopEnabled
    } = state.machineStatus;

    if (eStopEnabled) {
        const result = request("set_machine_status", {
            "command": "E_STOP_RESET"
        }, "POST");
        if (await result === 200) {
            getMachineValues();
        }
    } else {
        const result = request("set_machine_status", {
            "command": "E_STOP"
        }, "POST");
        if (await result === 200) {
            getMachineValues();
        }
    }
}

const setPowerOnClick = async () => {
    const {
        powerEnabled
    } = state.machineStatus;

    if (powerEnabled) {
        console.log(powerEnabled)
        const result = request("set_machine_status", {
            "command": "POWER_ON"
        }, "POST");
        if (await result === 200) {
            getMachineValues();
        }
    } else {
        const result = request("set_machine_status", {
            "command": "POWER_OFF"
        }, "POST");
        if (await result === 200) {
            getMachineValues();
        }
    }
}

getMachineValues();
setInterval(() => {
    update();
}, 3000);