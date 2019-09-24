window.onload = async () => {
  getMachineStatus();
  setInterval(() => {
    getMachineStatus();
  }, 1000);

};

const api = "http://192.168.1.224:5000";
let machinekit_state = {
  power: {
    enabled: true,
    estop: false
  }
};

let firstRender = true;
let errors, displayedErrors = [];
let selectedAxe = "x";
let distanceMultiplier = 1;

const request = (url, type, data = {}) => {
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
  const status = await request("http://192.168.1.224:5000/status", "GET");
  if (status == undefined) {
    return;
  }
  machinekit_state = status;
  render();
}

const handleErrors = () => {
  if (errors.length > 0) {
    document.body.classList.add("error_executing");
    errors.map((value, index) => {
      if (!displayedErrors.includes(value)) {
        document.getElementById("custom_errors").innerHTML += `<p class="error" id="error_executing">${value}</p>`
        //document.getElementById("error_executing").innerHTML += value + "<br>";
        displayedErrors.push(value);
      }
    });
  }
}

const checkAndAddClass = (condition, value) => {
  if (condition) {
    document.body.classList.add(value.true);
  } else {
    document.body.classList.add(value.false)
  }
}

const checkIfAxesAreHomedAndRenderTable = () => {
  const {
    position,
  } = machinekit_state;

  let totalAxes = 0;
  let axesHomed = 0;
  for (const key in position) {
    let homed = position[key].homed;
    if (homed) {
      axesHomed++;
    }
    totalAxes++;
  }

  if (totalAxes == 3) {
    document.body.classList.add("standard_xyz_table");
    document.getElementById("tbody_axes").innerHTML = "";
    for (const key in position) {
      let isHomed = "";
      if (position[key].homed) {
        isHomed = "(H)";
      }
      document.getElementById("tbody_axes").innerHTML += `<td>${position[key].pos}${isHomed}</td>`;
    }
  } else {
    document.body.classList.add("custom_table");
    const thead = document.getElementById("c_thead_axes");
    const tbody = document.getElementById("c_tbody_axes");
    const radio = document.getElementById("manual_control_radio_custom");

    thead.innerHTML = "";
    tbody.innerHTML = "";

    for (const key in position) {
      let isHomed = "";
      if (position[key].homed) {
        isHomed = "(H)";
      }
      if (key == "x") {
        thead.insertCell(0).innerHTML = key;
        tbody.insertCell(0).innerHTML = position[key].pos + isHomed;
      } else if (key == "y") {
        thead.insertCell(1).innerHTML = key;
        tbody.insertCell(1).innerHTML = position[key].pos + isHomed;
      } else if (key == "z") {
        thead.insertCell(2).innerHTML = key;
        tbody.insertCell(2).innerHTML = position[key].pos + isHomed;
      } else {
        thead.innerHTML += `<th>${key}</th>`;
        tbody.innerHTML += `<td>${position[key].pos}${isHomed}</td>`;
      }
      if (firstRender) {
        radio.innerHTML += `
        <li>
          <input type="radio" name="radio" id="radiox" data="${key}"
            onclick="manualControlSelector(this)" />
          <label for="radiox">${key}</label>
        </li>`;
      }
    }

  }
  checkAndAddClass(totalAxes === axesHomed, {
    true: "all_homed",
    false: "not_homed"
  });

  firstRender = false;
}

const setBodyClasses = () => {
  const {
    power,
    spindle,
  } = machinekit_state;
  checkAndAddClass(power.enabled, {
    true: "power_on",
    false: "power_off"
  });

  checkAndAddClass(power.estop, {
    true: "estop",
    false: "no_estop"
  });

  let value;

  switch (machinekit_state.program.interp_state) {
    case "INTERP_IDLE":
      value = "INTERP_IDLE";
      break;
    case "INTERP_READING":
      value = "INTERP_READING";
      break;
    case "INTERP_PAUSED":
      value = "INTERP_PAUSED";
      break;
    case "INTERP_WAITING":
      value = "INTERP_WAITING";
      break;
    default:
      break;
  }
  document.body.classList.add(value);


  switch (machinekit_state.program.task_mode) {
    case "MODE_MANUAL":
      value = "MODE_MANUAL";
      break;
    case "MODE_AUTO":
      value = "MODE_AUTO";
      break;
    case "MODE_MDI":
      value = "MODE_MDI";
      break;
    default:
      break;
  }
  document.body.classList.add(value);

  checkAndAddClass(spindle.spindle_brake, {
    true: "SPINDLE_BRAKE_ON",
    false: "SPINDLE_BRAKE_OFF"
  });

  if (spindle.spindle_direction == -1) {
    document.body.classList.add("SPINDLE_BACKWARD");
  } else {
    document.body.classList.add("SPINDLE_FORWARD");
  }

  checkAndAddClass(spindle.spindle_enabled, {
    true: "SPINDLE_ENABLED",
    false: "SPINDLE_DISABLED"
  });

  document.getElementById("feed_override").value = (machinekit_state.program.feedrate * 100);
  document.getElementById("feed_override_output").innerHTML = (machinekit_state.program.feedrate * 100);

  document.getElementById("spindle_override").value = (machinekit_state.spindle.spindlerate * 100);
  document.getElementById("spindle_override_output").innerHTML = (machinekit_state.spindle.spindlerate * 100);

  document.getElementById("max_velocity").value = (machinekit_state.values.max_velocity);
  document.getElementById("max_velocity_output").innerHTML = (machinekit_state.values.max_velocity);
  document.getElementById("file").innerHTML = machinekit_state.program.file;
}

const toggleEstop = async () => {
  document.getElementById("toggleEstopBtn").disabled = true;
  setTimeout(function () {
    document.getElementById("toggleEstopBtn").disabled = false;
  }, 1000);

  await request(
    api + "/set_machine_status",
    "POST", {
      command: "estop"
    }
  );
  getMachineStatus();
};

const togglePower = async () => {
  document.getElementById("togglePowerBtn").disabled = true;
  setTimeout(function () {
    document.getElementById("togglePowerBtn").disabled = false;
  }, 1000);

  const result = await request(
    api + "/set_machine_status",
    "POST", {
      command: "power"
    },
  );
  if (result.errors) {
    errors.push(result.errors);
  }
  getMachineStatus();
};

const homeAllAxes = async (data) => {
  let command = {
    "command": "home"
  }
  if (data) {
    command = {
      "command": "unhome"
    }
  }
  const result = await request(api + "/set_home", "POST", command);
  if (result.errors) {
    errors.push(result.errors);
  }
  getMachineStatus();
}

const manualControlSelector = (element) => {
  selectedAxe = element.getAttribute("data");
}

const manualControlDistance = (element) => {
  const value = element.value;
  const target = element.id;
  distanceMultiplier = value;
  document.getElementById(target + "_output").innerHTML = value;
}

const manualControl = async (input, increment) => {
  const axeWithNumber = {
    x: 0,
    y: 1,
    z: 2,
    a: 3,
    b: 4,
    c: 5,
    u: 6,
    v: 7,
    w: 8
  }
  const axeNumber = axeWithNumber[selectedAxe];

  let command = {
    "axes": axeNumber,
    "speed": 10,
    "increment": 0
  }

  if (input == "increment") {
    command.increment = increment * distanceMultiplier;
  } else {
    command.increment = increment * distanceMultiplier;
  }

  const result = await request(api + "/manual", "POST", command);
  if (result.errors) {
    errors.push(result.errors);
  }
  setTimeout(() => {
    getMachineStatus();
  }, 750);
}

const programControl = async (input) => {
  let command = {
    "command": ""
  }
  switch (input) {
    case "start":
      command.command = "start";
      break;
    case "pause":
      command.command = "pause";
      break;
    case "resume":
      command.command = "resume";
      break;
    case "stop":
      command.command = "stop";
      break;
    default:
      break;
  }

  const result = await request(api + "/control_program", "POST", command);
  if (result.errors) {
    errors.push(result.errors);
  }
  getMachineStatus();
}

const spindleControl = async (input) => {
  let command = {
    "command": {
      "spindle_direction": ""
    }
  }
  switch (input) {
    case "forward":
      command.command.spindle_direction = "spindle_forward"
      break;
    case "off":
      command.command.spindle_direction = "spindle_off"
      break;
    case "reverse":
      command.command.spindle_direction = "spindle_reverse"
      break;
    case "brake":
      command = {
        "command": {
          "spindle_brake": ""
        }
      }
      if (machinekit_state.spindle.spindle_brake == 0) {
        command.command.spindle_brake = 1;
      } else {
        command.command.spindle_brake = 0;
      }
      break;
    default:
      break;
  }
  const result = await request(api + "/spindle", "POST", command);
  if (result.errors) {
    errors.push(result.errors);
  }
  getMachineStatus();
}

const spindleSpeedControl = async (input) => {
  let command = {
    "command": {
      "spindle_direction": ""
    }
  }
  if (input == "increment") {
    command.command.spindle_direction = "spindle_increase";
  } else {
    command.command.spindle_direction = "spindle_decrease";
  }
  const result = await request(api + "/spindle", "POST", command);
  if (result.errors) {
    errors.push(result.errors);
  }
  getMachineStatus();
}

const controlFeedOverride = async (element) => {
  const value = (element.value / 100);
  const target = element.id;
  document.getElementById(target + "_output").innerHTML = element.value;
  if (target == "feed_override") {
    const result = await request(api + "/feed", "POST", {
      "feedrate": value
    });
    if (result.errors) {
      errors.push(result.errors);
    }
  } else if (target == "spindle_override") {
    const result = await request(api + "/spindle", "POST", {
      "command": {
        "spindle_override": value
      }
    });
    if (result.errors) {
      errors.push(result.errors);
    }
  } else {
    const result = await request(api + "/maxvel", "POST", {
      "velocity": value * 100
    });
    if (result.errors) {
      errors.push(result.errors);
    }
  }

  getMachineStatus();
}

const sendMdiCommand = async () => {
  const command = document.getElementById("mdi_command_input").value.toUpperCase();

  const result = await request(api + "/send_command", "POST", {
    "mdi_command": command
  });

  if (result.errors) {
    errors.push(result.errors);
  }

  setTimeout(() => {
    getMachineStatus();
  }, 750);
}

const render = () => {
  document.body.className = "success_no_errors";
  handleErrors();
  setBodyClasses();
  checkIfAxesAreHomedAndRenderTable();
};