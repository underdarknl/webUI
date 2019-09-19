const api = "http://192.168.1.224:5000";
let machinekit_state = {
  power: {
    enabled: true,
    estop: false
  }
};
let errors = [];
let displayedErrors = [];

const request = (url, data, type) => {
  if (type === "POST") {
    return fetch(url, {
        method: "POST",
        mode: "cors",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
      })
      .then(response => {
        return response.json();
      })
      .then(data => {
        return data;
      });
  } else {
    return fetch(url, {
        method: "GET"
      })
      .then(response => {
        return response.json();
      })
      .then(data => {
        if (data.errors == "Machinekit is not running please restart machinekit and then the server") {
          document.body.className = "error_machinekit";
          return;
        } else {
          return data;
        }
      })
      .catch(error => {
        if (error == "TypeError: Failed to fetch") {
          document.body.className = "error_server_down";
          return;
        }
      });
  }
};

const getMachineStatus = async () => {
  const status = await request("http://192.168.1.224:5000/status", {}, "GET");
  if (status == undefined) {
    return;
  }
  machinekit_state = status;
  render();
}

const render = () => {
  document.body.className = "success_no_errors";
  if (errors.length > 0) {
    document.body.classList.add("error_executing");
    errors.map((value, index) => {
      if (!displayedErrors.includes(value)) {
        document.getElementById("error_executing").innerHTML += value + "<br>";
        displayedErrors.push(value);
      }
    });
  }

  if (machinekit_state.power.enabled) {
    document.body.classList.remove("power_off");
    document.body.classList.add("power_on");
  } else {
    document.body.classList.remove("power_on");
    document.body.classList.add("power_off");

  }

  if (!machinekit_state.power.estop) {
    document.body.classList.remove("estop");
    document.body.classList.add("no_estop");

    document.getElementById("machine_power").classList.add("enabled");
  } else {
    document.body.classList.remove("no_estop");
    document.body.classList.add("estop");
    document.getElementById("machine_power").classList.remove("enabled");
  }

  // switch (machinekit_state.program.interp_state) {
  //   case "INTERP_IDLE":
  //     document.body.classList.add("INTERP_IDLE");
  //     console.log("idle");
  //     break;
  //   case "INTERP_READING":
  //     console.log("reading");
  //     break;
  //   case "INTERP_PAUSED":
  //     console.log("paused");
  //     break;
  //   case "INTERP_WAITING":
  //     console.log("waiting");
  //     break;
  // }

  // let myRe = /\INTERP_IDLE|\INTERP_WAITING|\INTERP_PAUSED|\INTERP_READING/;
  // let test = document.body.classList;
  // var result = myRe.exec(test.value);
  // console.log(test.value);
};

const toggleEstop = async () => {
  await request(api + "/set_machine_status", {
    command: "estop"
  }, "POST");
  getMachineStatus();

  document.getElementById("toggleEstopBtn").disabled = true;
  setTimeout(function () {
    document.getElementById("toggleEstopBtn").disabled = false;
  }, 750);
};

const togglePower = async () => {
  const result = await request(
    api + "/set_machine_status", {
      command: "power"
    },
    "POST"
  );
  if (result.errors) {
    errors.push(result.errors);
  }
  getMachineStatus();

  document.getElementById("togglePowerBtn").disabled = true;
  setTimeout(function () {
    document.getElementById("togglePowerBtn").disabled = false;
  }, 1000);
};

window.onload = () => {
  setInterval(() => {
    getMachineStatus();
  }, 4000);
  getMachineStatus();
};