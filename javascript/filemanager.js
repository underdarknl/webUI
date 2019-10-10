let queueNotRendered = true;

const listFilesFromServer = async () => {
    socket.emit("get-files", () => {});
    firstFileManagerRender = false;

    socket.on("get-files", (files => {
        appState.files = files.result;
        if (files.file_queue !== undefined) {
            appState.file_queue = files.file_queue;
        }
        if (appState.file_queue.length > 0) {
            addToBody("files-in-queue");
            if (queueNotRendered) {
                renderQueue();
                queueNotRendered = false;
            }
            if (appState.file_queue[0] !== machine_state.program.file) {
                socket.emit("open-file");
            }
        }

        document.getElementById("tbody_files").innerHTML = "";
        appState.files.map((item, index) => {
            // <td><button class="primary" onclick="selectFile('${item[2] + "/" + item[1]}')">Select</button></td>
            document.getElementById("tbody_files").innerHTML += `
        <tr><td>${item[1]}</td>
        <td><button class="warning" onclick="addToQueue('${item[1]}')">Add to queue</button></td></tr>`;
        });
    }));
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
}

const getFile = () => {
    const fileList = document.getElementById("uploadFile");
    if ("files" in fileList) {
        const file = fileList.files[0];

        if (file.length == 0) {
            appState.errors.push("Please select a file");
            return;
        }

        if (!file.name) {
            appState.errors.push("File must have a name.");
            return;
        }

        const ext = getFileExt(file.name);

        if (ext === "nc") {
            appState.file = file;
            return;
        } else {
            appState.errors.push("Filetype is not allowed. Please select a file with the type '.nc' ");
            return;
        }
    }
}

const getFileExt = (file) => {
    const lastDot = file.lastIndexOf(".");
    const ext = file.substring(lastDot + 1);
    return ext;
}

const fUpload = async () => {
    if (appState.file == null) {
        appState.errors.push("Please select a file");
        return handleErrors();
    }

    const reader = new FileReader();
    reader.onload = function (e) {
        const result = e.target.result;
        socket.emit("file-upload", {
            "file": result,
            "name": appState.file.name
        }, () => {
            listFilesFromServer();
        });
    }

    reader.readAsBinaryString(appState.file);;

}