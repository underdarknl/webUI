const api = "http://192.168.1.224:5000";
let state = {
  status: {
    position: {
      x: {
        homed: true,
        pos: 118.874
      },
      y: {
        homed: true,
        pos: 13.65
      },
      z: {
        homed: true,
        pos: -2.0
      }
    },
    power: {
      enabled: true,
      estop: false
    },
    program: {
      file: "/usr/share/axis/images/axis.ngc",
      interp_state: "INTERP_IDLE",
      task_mode: "MODE_MANUAL"
    },
    spindle: {
      spindle_brake: 1,
      spindle_direction: 0,
      spindle_enabled: 0,
      spindle_increasing: 0,
      spindle_override_enabled: true,
      spindle_speed: 0.0,
      spindlerate: 1.0,
      tool_in_spindle: 0
    },
    velocity: 0.0
  },
  errors: ""
};

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
        return data;
      })
      .catch(error => {
        if (error == "TypeError: Failed to fetch") {
          return {
            errors: "Server is down please start the server"
          };
        }
        return console.log(error);
      });
  }
};

const getMachineVitals = async () => {
  const result = await request("http://192.168.1.224:5000/status", {}, "GET");
  if (result.errors) {
    handleErrors(result);

    state = {
      ...state,
      errors: result.errors
    };
    return;
  } else {
    let status = result.status;
    state = {
      ...state,
      status
    };
  }
  generateHtml();
};

const handleErrors = result => {
  document.getElementById("error").innerHTML =
    "<p class='error'>" + result.errors + "</p>";
};

const generateHtml = () => {
  const { position, power } = state.status;
  let thead = document.getElementById("thead_axes");
  let tbody = document.getElementById("tbody_axes");
  thead.innerHTML = "";
  tbody.innerHTML = "";

  document.getElementById(
    "error"
  ).innerHTML = `<p class="success">No errors found</p>`;

  if (power.enabled) {
    document.getElementById(
      "power"
    ).innerHTML = `<div id="power"><label>POWER: </label><p class="success"> ON</p>`;
  } else {
    document.getElementById(
      "power"
    ).innerHTML = `<div id="power"><label>POWER: </label><p class="error"> OFF</p>`;
  }

  document.getElementById(
    "estop"
  ).innerHTML = `<div id="power"><label>ESTOP: </label>${
    power.estop
      ? `<p class="error"> ENABLED<p>`
      : `<p class="success"> DISABLED</p>`
  }</div>`;

  for (const key in position) {
    const { pos, homed } = position[key];
    !homed
      ? (thead.innerHTML = thead.innerHTML += `<th>` + key + `</th>`)
      : (thead.innerHTML += `<th>` + key + ` (H) </th>`);

    tbody.innerHTML += `<tr><td>` + pos + `</td></tr>`;
  }
};

window.onload = function() {
  getMachineVitals();
  setInterval(() => {
    getMachineVitals();
  }, 5000);
};

const toggleEstop = async () => {
  const current_status_estop = state.status.power.estop;
  if (current_status_estop) {
    console.log("RESET");
    const result = await request(
      api + "/set_machine_status",
      { command: "E_STOP_RESET" },
      "POST"
    );
  } else {
    console.log("ESTOP");
    const result = await request(
      api + "/set_machine_status",
      { command: "E_STOP" },
      "POST"
    );
  }
  getMachineVitals();
};
