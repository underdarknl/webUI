let state = {
    file: null,
    queue: [],
    buttons: {
        upload: {
            id: "uploadFile"
        }
    }
}

const listFilesFromServer = async () => {
    document.getElementById("tbody_files").innerHTML = "";
    const result = await request(api + "/return_files", "GET");
    console.log(result);
    if (result === undefined) {
        return;
    }

    result.result.map((item, index) => {
        document.getElementById("tbody_files").innerHTML += `
        <td>${item[1]}</td>
        <td><button class="primary">Select</button></td>`;
    });
}



const getFile = () => {
    const fileList = document.getElementById(state.buttons.upload.id);
    if ("files" in fileList) {
        const file = fileList.files[0];

        if (file.length == 0) {
            return console.log("Select a file");
        }

        if (!file.name) {
            return console.log("File must have a name");
        }

        const ext = getFileExt(file.name);

        if (ext === "nc") {
            state.file = file;
            return;
        } else {
            return console.log("File not allowed");
        }
    }
}

const getFileExt = (file) => {
    const lastDot = file.lastIndexOf(".");
    const ext = file.substring(lastDot + 1);
    return ext;
}

const fUpload = async () => {
    if (state.file == null) {
        return console.log("No file selected");
    }
    let formData = new FormData();
    formData.append("file", state.file);
    const result = await request(api + "/file_upload", "UPLOAD", formData);
    if (result.errors) {
        errors.push(result.errors);
        handleErrors();
    }
    listFilesFromServer();
}