const api = "http://192.168.1.224:5000/";

let state = {
  machineStatus: {
    powerEnabled: false,
    eStopEnabled: false,
    homed: false,
    position: {}
  },
  generatedControls: false,
  errors: [],
  speed: 1
};

const getMachineValues = async () => {
  const result = await request(api + "status", {}, "get");
  if (handleErrors(result) == undefined) {
    return;
  }
  const machineStatus = result.machineStatus;
  state = {
    ...state,
    machineStatus
  };

  const { eStopEnabled, powerEnabled, position } = state.machineStatus;
  populateTable();
  if (position !== {} && !state.generatedControls) {
    generateControllers();
  }

  if (eStopEnabled) {
    document.getElementById("emergencyBtn").innerHTML =
      "DISABLE EMERGENCY STOP";
  } else {
    document.getElementById("emergencyBtn").innerHTML = "ENABLE EMERGENCY STOP";
  }

  if (powerEnabled) {
    document.getElementById("powerBtn").innerHTML = "turn power off";
  } else {
    document.getElementById("powerBtn").innerHTML = "turn power on";
  }
};

const handleErrors = result => {
  if (result.error || result === "Server is down please start the server") {
    state.errors = result;
    if (result.error == "emcStatusBuffer invalid err=3") {
      state.errors =
        "Machinekit is offline. Start machinekit with 'linuxcnc &'";
    }
  }

  if (state.errors) {
    if (state.errors.length > 0) {
      document.getElementById("error").innerHTML =
        "<p class='error'>" + state.errors + "</p>";
      state.errors = [];
      return;
    } else {
      document.getElementById("error").innerHTML = "";
      return false;
    }
  }
  return false;
};

const populateTable = () => {
  const position = state.machineStatus.position;
  const head = document.getElementById("thead_axes");
  const body = document.getElementById("tbody_axes");
  head.innerHTML = "";
  body.innerHTML = "";

  for (const key in position) {
    if (key == "x") {
      head.insertCell(0).innerHTML = key;
      body.insertCell(0).innerHTML = position[key];
    } else if (key == "y") {
      head.insertCell(1).innerHTML = key;
      body.insertCell(1).innerHTML = position[key];
    } else if (key == "z") {
      head.insertCell(2).innerHTML = key;
      body.insertCell(2).innerHTML = position[key];
    } else {
      head.insertCell(-1).innerHTML = key;
      body.insertCell(-1).innerHTML = position[key];
    }
  }
};

const update = () => {
  getMachineValues();
};

const eStopOnClick = async () => {
  const { eStopEnabled } = state.machineStatus;

  if (eStopEnabled) {
    const result = await request(
      api + "set_machine_status",
      {
        command: "E_STOP_RESET"
      },
      "POST"
    );
    if (result === 200) {
      getMachineValues();
    }
  } else {
    const result = await request(
      api + "set_machine_status",
      {
        command: "E_STOP"
      },
      "POST"
    );
    if (result === 200) {
      getMachineValues();
    } else {
      state.errors.push(result);
      console.log(state.errors);
    }
  }
};

const setPowerOnClick = async () => {
  const { powerEnabled } = state.machineStatus;

  if (powerEnabled) {
    const result = request(
      api + "set_machine_status",
      {
        command: "POWER_ON"
      },
      "POST"
    );
    if ((await result) === 200) {
      getMachineValues();
    }
  } else {
    const result = request(
      api + "set_machine_status",
      {
        command: "POWER_OFF"
      },
      "POST"
    );
    if ((await result) === 200) {
      getMachineValues();
    }
  }
};

const manualControl = async element => {
  const data = JSON.parse(element.dataset.object);
  const result = await request(
    api + "manual",
    {
      axes: data.axes,
      speed: 10,
      increment: data.increment * state.speed,
      command: ""
    },
    "POST"
  );

  if (result.errors) {
    state.errors.push(result.errors);
  }
};

const controlDistance = element => {
  state.speed = parseInt(element.options[element.selectedIndex].dataset.object);
};

const generateControllers = () => {
  console.log(state.machineStatus.position);
  const keyToInt = {
    x: 0,
    y: 1,
    z: 2,
    a: 3,
    b: 4,
    c: 5,
    d: 6,
    e: 7,
    f: 8
  };
  const movementOptions = [10, 5, 1, -1, -5, -10];
  for (const key in state.machineStatus.position) {
    let html =
      `
    <label>` +
      key +
      `</labe>
    <form onsubmit="event.preventDefault()">`;
    movementOptions.map((value, index) => {
      html +=
        `
      <button
            onclick="manualControl(this)"
            data-object='{"axes": ` +
        keyToInt[key] +
        `, "increment": ` +
        value +
        `}'
          >
            ` +
        value +
        `
          </button>
      `;
    });
    html += `</form>`;
    document.getElementById("controllers").innerHTML += html;
  }

  state.generatedControls = true;
  //document.getElementById("controllers").innerHTML = html;
};

getMachineValues();
setInterval(() => {
  update();
}, 3000);
