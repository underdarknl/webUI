const post = (url, data) => {
    return fetch(url, {
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
}

const getAllAxesPosition = () => {
    const networkPromise = fetch("http://192.168.1.224:5000/get_current_position", {
            method: "get"
        })
        .then(response => {
            return response.json();
        })
        .then(data => {
            const {
                machine_power_on,
                estop_active,
                axis
            } = data;

            let eBtn = document.getElementById("emergency_button_status");
            let pBtn = document.getElementById("power_button_status");

            for (var key in data.current_position) {
                document.getElementById(key).innerHTML = data.current_position[key]
            }

            if (estop_active) {
                eBtn.innerHTML = "REMOVE EMERGENCRY STOP"
                eBtn.setAttribute("estop", "active")
            }
            if (machine_power_on) {
                pBtn.innerHTML = "power off"
                pBtn.setAttribute("power", "off")
            } else {
                pBtn.innerHTML = "power on"
                pBtn.setAttribute("power", "on")
            }

        })
        .catch(function (err) {
            console.log(err)
        });

    let timeOutPromise = new Promise(function (resolve, reject) {
        setTimeout(resolve, 3000, "done")
    });

    Promise.all(
        [networkPromise, timeOutPromise]).then(function (values) {
        getAllAxesPosition();
    });

}

const emergencyBtn = (element) => {
    let btn = document.getElementById("emergency_button_status");
    if (btn.getAttribute("estop")) {
        return fetch("http://192.168.1.224:5000/set_machine_status", {
                method: "POST",
                mode: "cors",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    "command": "E_STOP_RESET"
                })
            })
            .then(response => {
                return response.json()
            })
            .then(data => {
                if (data === 200) {

                    btn.setAttribute("estop", "");
                    btn.innerHTML = "EMERGENCRY STOP"

                }
            })
    } else {
        fetch("http://192.168.1.224:5000/set_machine_status", {
                method: "POST",
                mode: "cors",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    "command": "E_STOP"
                })
            })
            .then(response => {
                return response.json()
            })
            .then(data => {
                if (data === 200) {
                    let btn = document.getElementById("emergency_button_status");
                    btn.setAttribute("estop", "active")
                    btn.innerHTML = "REMOVE EMERGENCRY STOP"
                    btn.disabled = true;
                    setTimeout(() => {
                        btn.disabled = false;
                    }, 2500);
                }
            })
    }
}

const powerBtn = (element) => {

}

getAllAxesPosition();