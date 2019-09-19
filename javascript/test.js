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
  firstRender: true
};

let applicationErrors = [];
let frontEndState = {};

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
    if (!applicationErrors.includes(result.errors)) {
      applicationErrors.push(result.errors);
    }
  } else {
    let status = result.status;
    state = {
      ...state,
      status
    };
    applicationErrors = [];
  }
  generateHtml();
  handleErrors();
};

const handleErrors = result => {
  const e = document.getElementById("error");
  if (applicationErrors.length == 0) {
    return (e.innerHTML = `<p class="success">No errors found</p>`);
  }
  e.innerHTML = "";
  applicationErrors.map((value, index) => {
    e.innerHTML += `<p class='error'>${value}</p>`;
  });
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
      ? (thead.innerHTML = thead.innerHTML += `<th> ${key} </th>`)
      : (thead.innerHTML += `<th>${key} (H)</th>`);

    tbody.innerHTML += `<tr><td>` + pos + `</td></tr>`;
    if (state.firstRender) {
      document.getElementById("manual_control_radio").innerHTML += ` <li>
      <input
        type="radio"
        name="radio"
        id="radio${key}"
        data="${key}"
        checked="if()"
        onclick="setAxesForControl(this)"
      />
      <label for="radio${key}">${key}</label>
    </li>`;
    }
  }
  state.firstRender = false;
};

window.onload = function() {
  getMachineVitals();
  setInterval(() => {
    getMachineVitals();
  }, 3000);
};

const toggleEstop = async () => {
  await request(api + "/set_machine_status", { command: "estop" }, "POST");
  getMachineVitals();
};

const togglePower = async () => {
  const result = await request(
    api + "/set_machine_status",
    { command: "power" },
    "POST"
  );
  if (result.errors) {
    state.errors = result.errors;
    applicationErrors.push(result.errors);
  }
  getMachineVitals();
};

const homeAxes = async () => {
  const result = await request(api + "/set_home", {}, "GET");
  console.log(result);
};

const setAxesForControl = element => {
  console.log(element.getAttribute("data"));
};
