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

            for (var key in data.current_position) {
                document.getElementById(key).innerHTML = data.current_position[key]
            }

            power = (machine_power_on !== true ? "power on" : "power off")
            document.getElementById("emergency_button_status").disabled = estop_active;
            document.getElementById("power_button_status").innerHTML = power;
        })
        .catch(function (err) {
            console.log(err)
        });

    let timeOutPromise = new Promise(function (resolve, reject) {
        setTimeout(resolve, 1000, "done")
    });

    Promise.all(
        [networkPromise, timeOutPromise]).then(function (values) {
        getAllAxesPosition();
    });

}

const emergencyStop = () => {}
getAllAxesPosition();