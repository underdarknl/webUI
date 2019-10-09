let machine_state = {};
let url = "192.168.1.116:5000";

window.onload = async () => {
  let firstConnect = true;
  const socket = io.connect(url);

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
};

const addMachineStatusToBody = () => {
  const {
    position,
    power,
    program,
    spindle,
    values
  } = machine_state;
  power.enabled ? addToBody("power-on") : addToBody("power-off");
  power.estop ? addToBody("estop-enabled") : addToBody("estop-disabled");

  if (program.interp_state === "INTERP_IDLE") {
    addToBody("interp-idle");
  } else if (program.interp_state === "INTERP_PAUSED") {
    addToBody("interp-paused");
  } else if (program.interp_state === "INTERP_WAITNG") {
    addToBody("interp-waiting");
  } else {
    addToBody("interp-reading");
  }

  if (program.task_mode === "MODE_MANUAL") {
    addToBody("task-manual");
  } else if (program.task_mode === "MODE_AUTO") {
    addToBody("task-auto");
  } else {
    addToBody("task-mdi");
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