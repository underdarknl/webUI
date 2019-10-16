let machine_state = {};
let url = "192.168.1.116:5000";
let socket;
let firstConnect = true;
const auth = "test";

let appState = {
  errors: [],
  displayedErrors: [],
  speed: 1,
  distanceMultiplier: 1,
  selectedAxe: "x",
  ticks: 1,
  previousAxesPosition: {},
  previousExecState: "RCS_DONE",
  files: [],
  file_queue: [],
  file: ""
}

window.onload = async () => {
  const sortable = new Sortable.default(document.getElementById('tbody_queue'), {
    draggable: 'tr'
  });
  socket = io.connect(url);
  connectSockets();
};

const connectSockets = async () => {
  const result = await socket.on("connect", () => {
    socket.on("connected", () => {
      console.log("Connected!");
      //Call this to get the file_queue from the server
      listFilesFromServer();
      addToBody("server-running", true);

      //Initial render on connect
      socket.emit("vitals", {
        "auth": auth
      }, () => {
        //Start interval after first result
        if (firstConnect) {
          controlIntervalAndQueue();
          firstConnect = false;

        }
      });
    });

    //Listen to the error channel
    socket.on("errors", (message) => {
      appState.errors.push(message.errors);
    });
  });

  //On recieving vitals render page
  socket.on("vitals", vitals => {
    if (vitals.errors === "machinekit is not running") {
      return addToBody("machinekit-down server-running", true);
    }
    addToBody("server-running", true);
    addToBody("machinekit-running");

    /* 
     * Builds a history to check if machine started moving or if the rcs state changed 
     * we use this to determine if we need to poll more often on a shorter interval.
     * Also handles the file_queue
     */

    if (machine_state.program !== undefined) {
      appState.previousAxesPosition = machine_state.position;
      if (machine_state.program.rcs_state === "RCS_EXEC" && machine_state.program.task_mode === "MODE_AUTO") {
        appState.previousExecState = machine_state.program.rcs_state;
      }
    }
    //Set the new state
    machine_state = vitals;
    //Every time the app recieves 'vitals' update the page
    renderPage();
  });

  //Check if server is down
  if (result.disconnected) {
    addToBody("server-down", true);
  }
  //Keep checking if the server is down
  setInterval(() => {
    //Keep checking if the socket is running
    if (result.disconnected) {
      addToBody("server-down", true);
    }
  }, 2000);
}

//Controls interval rate
const controlIntervalAndQueue = () => {
  let interval = 200;
  if (!firstConnect) {
    //Compare axes positions to see if something moved. If something moved increase polling rate
    const old = JSON.stringify(appState.previousAxesPosition);
    const neww = JSON.stringify(machine_state.position);

    if (old === neww) {
      interval = 2000;
    }

    //If the state changes from RCS_EXECUTING to RCS_DONE remove first item from queue
    const oldExecState = appState.previousExecState;
    const newExecState = machine_state.program.rcs_state;
    if (oldExecState !== newExecState) {
      if (newExecState === "RCS_DONE") {
        removeFromQueue(0);
        getNewQueue();
        appState.previousExecState = "RCS_DONE";
      }
    }
  }
  //Every interval request new vitals
  socket.emit("vitals", {
    "auth": auth
  }, () => {});
  setTimeout(controlIntervalAndQueue, interval);
}

//Handle navigation
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

//Handle which page is rendered 
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
  //Check if there are any errors in the 'vitals' if so push them to the error array and render them with handleErrors
  if (errors.errors) {
    if (!appState.displayedErrors.includes(errors.errors)) {
      appState.errors.push(errors.errors);
    }
  }
  handleErrors();
};

//Checks if there are new errors in the error array. If there are check if unique and push to displayed errors
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
//Removes error onclick 
const removeError = (id) => {
  appState.displayedErrors.splice(id, 1);
  const elem = document.getElementById(id);
  elem.parentNode.remove()
}

//If the page 'controller' render page and execute functions in order
const renderController = () => {
  document.body.classList.remove("file-manager");
  addToBody("controller");
  addMachineStatusToBody();
  showSliderValues();
  renderTables();
};

//Give the html sliders values depending on what is in 'vitals' 
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

//Render standard XYZ table if axes = 3 else render custom table
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
  document.getElementById("spindle-speed").innerHTML = machine_state.spindle.spindle_speed;

  //Render standard XYZ or custom table
  if (axes === 3) {
    addToBody("xyz");
    //Because we are on an interval we need to empty the table every time
    document.getElementById("tbody_axes").innerHTML = "";
    for (const key in position) {
      let isHomed = "";
      let color = `error`;
      //If the axe is homed make it green and add (h) to the html
      if (position[key].homed) {
        isHomed = "(H)";
        color = `success`;
      }
      const tbody = document.getElementById("tbody_axes");
      let newcell;
      //For some reason the object xyz gets resorted to yxz so we need to turn around the 2 values
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

//Every time there is a 'vitals' update add everything to the body so the page is displayed
const addMachineStatusToBody = () => {
  const {
    power,
    program: {
      tool_change,
      interp_state,
      task_mode,
      file,
      rcs_state
    },
    spindle: {
      spindle_brake,
      spindle_direction,
      spindle_enabled,
    }
  } = machine_state;

  power.enabled ? addToBody("power-on") : addToBody("power-off");
  power.estop ? addToBody("estop-enabled") : addToBody("estop-disabled");

  addToBody(rcs_state);

  if (file == "") {
    addToBody("no-file");
  } else {
    addToBody("file-selected");
  }

  if (tool_change === 0) {
    document.getElementById("modaltoggle-warning").checked = true;
    addToBody("toolchange");
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

//Handles every function we call for rendering file-manager
const renderFileManager = () => {
  document.body.classList.remove("controller");
  addToBody("file-manager");
};

//Most on click events are down here

//Toggle estop/power
function toggleStatus(command) {
  socket.emit("set-status", {
    "command": command,
    "auth": auth
  }, () => {});
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

//Home our unhome axes
function homeAxes(command) {
  socket.emit("set-home", {
    "command": command,
    "auth": auth
  }, () => {});
}

//Set the value to which the manual control distance multiplier slider is set
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

//Handles which axe is selected in the radio buttons
function manualControlSelector(element) {
  appState.selectedAxe = element.getAttribute("data");
}

//Fires when a manual control movement button is pressed
function manualControl(input, increment, selectedAxe = null) {
  //Convert axename to number
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
  let axeNumber;
  if (selectedAxe === null) {
    axeNumber = axeWithNumber[appState.selectedAxe];
  } else {
    axeNumber = axeWithNumber[selectedAxe]
  }


  //Object that contains the axenumber, the speed at which it should move and the incrementation.
  let command = {
    "axes": axeNumber,
    "speed": parseFloat(appState.speed),
    "increment": 0,
    "auth": auth
  }
  if (input == "increment") {
    command.increment = increment * appState.distanceMultiplier;
  } else {
    command.increment = increment * appState.distanceMultiplier;
  }

  socket.emit("manual-control", command, () => {});
}

//Handles the start/pause/resume/stop of a program
function programControl(input) {
  let command = {
    "command": "",
    "auth": auth
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
  socket.emit("program-control", command, () => {});
}

//Controlls spindle direction and brake/on/off
function spindleControl(input) {
  let command = {
    "command": {
      "spindle_direction": "",
      "auth": auth
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
//Controlls the speed. increase/decrease
function spindleSpeedControl(input) {
  let command = {
    "command": {
      "spindle_direction": "",
      "auth": auth
    }
  }
  if (input == "increment") {
    command.command.spindle_direction = "spindle_increase";
  } else {
    command.command.spindle_direction = "spindle_decrease";
  }
  socket.emit("spindle-control", command.command, () => {});
}

//Controls feed/spindle override and max vel
function controlOverrides(element) {
  const value = (element.value / 100);
  const target = element.id;

  document.getElementById(target + "-output").innerHTML = element.value;

  if (target == "feed-override") {
    socket.emit("feed-override", {
      "command": value,
      "auth": auth
    }, () => {});
  } else if (target == "spindle-override") {
    socket.emit("spindle-control", {
      "spindle_override": value,
      "auth": auth
    }, () => {});
  } else {
    socket.emit("maxvel", {
      "command": (value * 100),
      "auth": auth
    }, () => {});
  }
}

function sendMdiCommand() {
  const command = document.getElementById("mdi-command-input").value.toUpperCase();
  socket.emit("send-command", {
    "command": command,
    "auth": auth
  }, () => {});
}

const toolChanged = () => {
  socket.emit("tool-changed", {
    "auth": auth
  }, () => {});
}

const offset = () => {
  socket.emit("offset", {
    "auth": auth
  }, () => {});
}