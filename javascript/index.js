let machine_state = {};
let url = "192.168.1.116:5000";
const socket = io.connect(url);

window.onload = async () => {
  let firstConnect = true;

  const result = await socket.on("connect", () => {
    socket.on("connected", () => {
      console.log("Connected!");
      addToBody("server-running", true);
      //Call once to render page
      socket.emit("vitals", () => {});

      //Only start polling once when connected
      if (firstConnect) {
        firstConnect = false;
        //Call every *ms*
        setInterval(() => {
          socket.emit("vitals", () => {});
        }, 400);
      }
    });
  });

  //On recieving vitals render page
  socket.on("vitals", message => {
    if (message.errors === "machinekit is not running") {
      return addToBody("machinekit-down server-running", true);
    }
    document.body.className = "server-running";
    addToBody("machinekit-running");
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
  }, 1000);
};

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
  const page = localStorage.getItem("page");
  if (page === "controller") {
    renderController();
  } else {
    renderFileManager();
  }
};

const renderController = () => {
  document.body.classList.remove("file-manager");
  addToBody("controller");
  addMachineStatusToBody();
  showSliderValues();
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

  document.getElementById("max-velocity").value = (max_velocity);
  document.getElementById("max-velocity-output").innerHTML = (max_velocity);
  document.getElementById("current-file").innerHTML = file;
}

const addMachineStatusToBody = () => {
  const {
    position,
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
      let color = `class="error"`;
      if (position[key].homed) {
        isHomed = "(H)";
        color = `class="success"`;
      }
      document.getElementById(
        "tbody_axes"
      ).innerHTML += `<td ${color}>${position[key].pos}${isHomed}</td>`;
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
};

const renderFileManager = () => {
  document.body.classList.remove("controller");
  addToBody("file-manager");
};

function toggleEstop() {
  console.log("Toggle");
  socket.emit("toggle-estop", () => {});
}