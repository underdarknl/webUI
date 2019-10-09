let machine_state = {};
let url = "192.168.1.116:5000";
let socket;
let firstConnect = true;

let appState = {
  errors: [],
  displayedErrors: [],
  speed: 1,
  distanceMultiplier: 1,
  selectedAxe: "x",
  ticks: 1,
  oldMachineState: {},
  files: [],
  file_queue: []
}
window.onload = async () => {
  const sortable = new Sortable.default(document.querySelectorAll('tbody'), {
    draggable: 'tr'
  });
  socket = io.connect(url);
  connectSockets();
};

const connectSockets = async () => {
  const result = await socket.on("connect", () => {
    socket.on("connected", () => {
      console.log("Connected!");

      addToBody("server-running", true);
      //Call once to render page
      socket.emit("vitals", () => {});

      //Only start polling once when connected
      if (firstConnect) {
        controlInterval();
        firstConnect = false;
      }
    });

    socket.on("get-files", (files => {
      appState.files = files.result;
      if (files.file_queue !== undefined) {
        appState.file_queue = files.file_queue;
      }
    }));

    socket.on("errors", (message) => {
      appState.errors.push(message.errors);
    });
  });

  //On recieving vitals render page
  socket.on("vitals", message => {
    if (message.errors === "machinekit is not running") {
      return addToBody("machinekit-down server-running", true);
    }
    document.body.className = "server-running";
    addToBody("machinekit-running");
    appState.oldMachineState = machine_state.position;
    machine_state = message;
    renderPage();
  });

  if (result.disconnected) {
    addToBody("server-down", true);
  }

  setInterval(() => {
    //Keep checking if the socket is running
    if (result.disconnected) {
      addToBody("server-down", true);
    }
  }, 2000);
}


const controlInterval = () => {
  let interval = 200;
  if (!firstConnect) {
    const old = JSON.stringify(appState.oldMachineState);
    const neww = JSON.stringify(machine_state.position);
    if (old === neww) {
      interval = 2000;
    }
  }

  socket.emit("vitals", () => {});
  setTimeout(controlInterval, interval);
}

const navigation = page => {
  localStorage.setItem("page", page);
  renderPage();
};

const addToBody = (className, onlyClass = false) => {
  if (onlyClass) {
    return (document.body.className = className);
  }
  document.body.classList.add(className);
};

const renderPage = () => {
  const {
    errors
  } = machine_state;
  const page = localStorage.getItem("page");
  if (page === "controller") {
    renderController();
  } else {
    renderFileManager();
  }

  if (errors.errors) {
    if (!appState.displayedErrors.includes(errors.errors)) {
      appState.errors.push(errors.errors);
    }
  }
  handleErrors();
};

const handleErrors = () => {
  const {
    displayedErrors
  } = appState;
  if (appState.errors.length > 0) {
    displayedErrors.push(appState.errors[0]);
    const index = displayedErrors.indexOf(appState.errors[0]);
    appState.errors = [];
    document.getElementById("custom-errors").innerHTML += `<p class="error" id="error-executing">${displayedErrors[index]}<button class="error" id=${index} onclick="removeError(this.id)">close</button></p>`
  }
}

const removeError = (id) => {
  appState.displayedErrors.splice(id, 1);
  const elem = document.getElementById(id);
  elem.parentNode.remove()
}

const renderController = () => {
  document.body.classList.remove("file-manager");
  addToBody("controller");
  addMachineStatusToBody();
  showSliderValues();
  renderTables();
};

const showSliderValues = () => {
  const {
    program: {
      feedrate,
      file
    },
    spindle: {
      spindlerate
    },
    values: {
      max_velocity
    }
  } = machine_state;

  document.getElementById("feed-override").value = Math.round((feedrate * 100));
  document.getElementById("feed-override-output").innerHTML = Math.round((feedrate * 100));

  document.getElementById("spindle-override").value = Math.round((spindlerate * 100));
  document.getElementById("spindle-override-output").innerHTML = Math.round((spindlerate * 100));

  document.getElementById("max-velocity").value = Math.round((max_velocity));
  document.getElementById("max-velocity-output").innerHTML = Math.round((max_velocity));
  document.getElementById("current-file").innerHTML = file;
}

const renderTables = () => {
  const position = machine_state.position;
  let axes = 0;
  let axesHomed = 0;
  for (const key in position) {
    let homed = position[key].homed;
    if (homed) {
      axesHomed++;
    }
    axes++;
  }

  if (axes === axesHomed) {
    addToBody("homed");
  } else {
    addToBody("unhomed");
  }

  //Render standard 3 axes table or render custom table
  if (axes === 3) {
    addToBody("xyz");
    document.getElementById("tbody_axes").innerHTML = "";
    for (const key in position) {
      let isHomed = "";
      let color = `error`;

      if (position[key].homed) {
        isHomed = "(H)";
        color = `success`;
      }
      const tbody = document.getElementById("tbody_axes");
      let newcell;
      if (key == "x") {
        newcell = tbody.insertCell(0);
        newcell.innerHTML = position[key].pos + isHomed;
        newcell.className = color;
      } else {
        document.getElementById(
          "tbody_axes"
        ).innerHTML += `<td class=${color}>${position[key].pos}${isHomed}</td>`;
      }
    }
  } else {
    addToBody("custom-table");
    const thead = document.getElementById("c_thead_axes");
    const tbody = document.getElementById("c_tbody_axes");

    thead.innerHTML = "";
    tbody.innerHTML = "";

    for (const key in position) {
      let isHomed = "";
      let color = `error`;
      if (position[key].homed) {
        isHomed = "(H)";
        color = `success`;
      }
      let newcell;
      if (key == "x") {
        thead.insertCell(0).innerHTML = key;
        newcell = tbody.insertCell(0);
        newcell.innerHTML = position[key].pos + isHomed;
        newcell.className = color;
      } else if (key == "y") {
        thead.insertCell(1).innerHTML = key;
        newcell = tbody.insertCell(1);
        newcell.innerHTML = position[key].pos + isHomed;
        newcell.className = color;
      } else if (key == "z") {
        thead.insertCell(2).innerHTML = key;
        newcell = tbody.insertCell(2);
        newcell.innerHTML = position[key].pos + isHomed;
        newcell.className = color;
      } else {
        thead.innerHTML += `<th>${key}</th>`;
        tbody.innerHTML += `<td  class="${color}">${position[key].pos}${isHomed}</td>`;
      }
    }
  }
}

const addMachineStatusToBody = () => {
  const {
    power,
    program: {
      tool_change,
      interp_state,
      task_mode
    },
    spindle: {
      spindle_brake,
      spindle_direction,
      spindle_enabled
    }
  } = machine_state;
  power.enabled ? addToBody("power-on") : addToBody("power-off");
  power.estop ? addToBody("estop-enabled") : addToBody("estop-disabled");

  if (tool_change === 0) {
    document.getElementById("modaltoggle-warning").checked = true;
  } else {
    document.getElementById("modaltoggle-warning").checked = false;
  }

  if (interp_state === "INTERP_IDLE") {
    addToBody("interp-idle");
  } else if (interp_state === "INTERP_PAUSED") {
    addToBody("interp-paused");
  } else if (interp_state === "INTERP_WAITNG") {
    addToBody("interp-waiting");
  } else {
    addToBody("interp-reading");
  }

  if (task_mode === "MODE_MANUAL") {
    addToBody("task-manual");
  } else if (task_mode === "MODE_AUTO") {
    addToBody("task-auto");
  } else {
    addToBody("task-mdi");
  }
  if (spindle_brake) {
    addToBody("spindle-brake-on");
  } else {
    addToBody("spindle-brake-off");
  }

  if (spindle_direction == -1) {
    addToBody("spindle-backward");
  } else {
    addToBody("spindle-forward");
  }

  if (spindle_enabled) {
    addToBody("spindle-enabled");
  } else {
    addToBody("spindle-disabled");
  }
};

const renderFileManager = () => {
  document.body.classList.remove("controller");
  addToBody("file-manager");
  listFilesFromServer();
};

//Button functions

function toggleStatus(command) {
  socket.emit("set-status", command, () => {});
  if (command === "estop") {
    document.getElementById("toggleEstopBtn").disabled = true;
    setTimeout(function () {
      document.getElementById("toggleEstopBtn").disabled = false;
    }, 1000);
  } else {
    document.getElementById("togglePowerBtn").disabled = true;
    setTimeout(function () {
      document.getElementById("togglePowerBtn").disabled = false;
    }, 1000);
  }
}

function homeAxes(command) {
  socket.emit("set-home", command, () => {});
}

function manualControlDistance(element, option) {
  const value = element.value;
  const target = element.id;
  if (option === "distance") {
    appState.distanceMultiplier = value;
    document.getElementById(target + "-output").innerHTML = value;
  } else {
    appState.speed = value;
    document.getElementById(target + "-output").innerHTML = value;
  }
}

function manualControlSelector(element) {
  appState.selectedAxe = element.getAttribute("data");
}

function manualControl(input, increment) {
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
  const axeNumber = axeWithNumber[appState.selectedAxe];
  let command = {
    "axes": axeNumber,
    "speed": parseFloat(appState.speed),
    "increment": 0
  }
  if (input == "increment") {
    command.increment = increment * appState.distanceMultiplier;
  } else {
    command.increment = increment * appState.distanceMultiplier;
  }

  socket.emit("manual-control", command, () => {});
}

function programControl(input) {
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

  socket.emit("program-control", command.command, () => {});
}

function spindleControl(input) {
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
      if (machine_state.spindle.spindle_brake == 0) {
        command.command.spindle_brake = 1;
      } else {
        command.command.spindle_brake = 0;
      }
      break;

    default:
      break;
  }
  socket.emit("spindle-control", command.command, () => {});
}

function spindleSpeedControl(input) {
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
  console.log(command.command);
  socket.emit("spindle-control", command.command, () => {});
}

function controlFeedOverride(element) {
  const value = (element.value / 100);
  const target = element.id;

  document.getElementById(target + "-output").innerHTML = element.value;

  if (target == "feed-override") {
    socket.emit("feed-override", value, () => {});
  } else if (target == "spindle-override") {
    socket.emit("spindle-control", {
      "spindle_override": value
    }, () => {});
  } else {
    socket.emit("maxvel", (value * 100), () => {});
  }
}

function sendMdiCommand() {
  const command = document.getElementById("mdi-command-input").value.toUpperCase();
  socket.emit("send-command", command, () => {});
}

const toolChanged = async () => {
  socket.emit("tool-changed", () => {});
}