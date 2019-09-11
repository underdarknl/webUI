const api = "http://192.168.1.224:5000/"

let state = {
    machineStatus: {
        powerEnabled: false,
        eStopEnabled: false,
        position: {
            "x": 0,
            "y": 0,
            "z": 0
        },
    },
    buttons: {
        emergency: {
            element: "emergencyBtn",
            enabled: "DISABLE EMERGENCY STOP",
            disabled: "ENABLE EMERGENCY STOP",
            timedOut: false
        },
        power: {
            element: "powerBtn",
            enabled: "power off",
            disabled: "power on",
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
    }
}

const getAllAxesPosition = async () => {
    const networkPromise = request(api + "get_current_position", "GET");
    // const networkPromise = fetch(api + "get_current_position", {
    //         method: "get"
    //     })
    //     .then(response => {
    //         return response.json();
    //     })
    //     .then(data => {
    //         const {
    //             machine_power_on,
    //             estop_active,
    //         } = data;

    //         let eBtn = document.getElementById("emergency_button_status");
    //         let pBtn = document.getElementById("power_button_status");

    //         for (var key in data.current_position) {
    //             document.getElementById(key).innerHTML = data.current_position[key]
    //         }

    //         if (estop_active) {
    //             eBtn.innerHTML = "REMOVE EMERGENCRY STOP"
    //             eBtn.setAttribute("estop", "active")
    //         }
    //         if (machine_power_on) {
    //             pBtn.innerHTML = "power off"
    //             pBtn.setAttribute("power", "")
    //         } else {
    //             pBtn.innerHTML = "power on"
    //             pBtn.setAttribute("power", "on")
    //         }

    //     })
    //     .catch(function (err) {
    //         console.log(err)
    //     });

    // let timeOutPromise = new Promise(function (resolve, reject) {
    //     setTimeout(resolve, 3000, "done")
    // });

    // Promise.all(
    //     [networkPromise, timeOutPromise]).then(function (values) {
    //     getAllAxesPosition();
    // });

}

// const emergencyBtnClick = async (element) => {
//     let btn = document.getElementById("emergency_button_status");
//     if (btn.getAttribute("estop")) {
//         const result = post("set_machine_status", {
//             "command": "E_STOP_RESET"
//         });
//         if (await result === 200) {
//             btn.setAttribute("estop", "");
//             btn.innerHTML = "EMERGENCRY STOP"
//         }
//     } else {
//         const result = post("set_machine_status", {
//             "command": "E_STOP"
//         });
//         if (await result === 200) {
//             btn.setAttribute("estop", "active")
//             btn.innerHTML = "REMOVE EMERGENCRY STOP"
//             btn.disabled = true;
//             setTimeout(() => {
//                 btn.disabled = false;
//             }, 2500);
//         }

//     }
// }

// const powerBtnClick = async (element) => {
//     let btn = document.getElementById("power_button_status");
//     if (btn.getAttribute("power")) {
//         const result = post("set_machine_status", {
//             "command": "POWER_OFF"
//         });

//         if (await result === 200) {
//             btn.setAttribute("power", "");
//             btn.innerHTML = "power on"
//         }
//     } else {
//         const result = post("set_machine_status", {
//             "command": "POWER_ON"
//         });

//         if (await result === 200) {
//             btn.setAttribute("power", "on");
//             btn.innerHTML = "power off"
//             btn.disabled = true;
//             setTimeout(() => {
//                 btn.disabled = false;
//             }, 2500);
//         }
//     }
// }

//getAllAxesPosition();