let firstFileManagerRender = true;
let test = true;

const listFilesFromServer = async () => {
    if (firstFileManagerRender) {
        socket.emit("get-files", () => {});
        firstFileManagerRender = false;
    }
    if (appState.file_queue.length > 0) {
        addToBody("files-in-queue");
        if (test) {
            renderQueue();
            test = false;
        }
    }

    document.getElementById("tbody_files").innerHTML = "";
    appState.files.map((item, index) => {
        // <td><button class="primary" onclick="selectFile('${item[2] + "/" + item[1]}')">Select</button></td>
        document.getElementById("tbody_files").innerHTML += `
        <tr><td>${item[1]}</td>
        <td><button class="warning" onclick="addToQueue('${item[1]}')">Add to queue</button></td></tr>`;
    });
}

const addToQueue = (file) => {
    document.body.classList.add("files-in-queue");
    appState.file_queue.push(file);
    renderQueue();
}

const removeFromQueue = (index) => {
    appState.file_queue.splice(index, 1);
    renderQueue();
}

const renderQueue = () => {
    document.getElementById("tbody_queue").innerHTML = "";
    appState.file_queue.map((value, index) => {
        document.getElementById("tbody_queue").innerHTML += `<tr id="${value}" class="test"><td>${value}</td><td><button class="error" onclick="removeFromQueue(${index})">remove</button></td></tr>`;
    });
}

const getNewQueue = async () => {
    appState.file_queue = [];
    let elements = document.getElementsByClassName("test");

    for (let i = 0; i < elements.length; i++) {
        appState.file_queue.push(elements.item(i).id);
    }

    socket.emit("update-file-queue", appState.file_queue, () => {});
    listFilesFromServer();
}