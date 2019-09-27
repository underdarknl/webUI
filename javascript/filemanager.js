let state = {
    file: null,
    queue: [],
}

const listFilesFromServer = async () => {
    document.getElementById("tbody_files").innerHTML = "";
    const result = await request(api + "/return_files", "GET");
    if (result === undefined) {
        return;
    }
    document.body.className = `success_no_errors file_manager`;

    result.result.map((item, index) => {
        document.getElementById("tbody_files").innerHTML += `
        <td>${item[1]}</td>
        <td><button class="primary" onclick="selectFile('${item[2] + "/" + item[1]}')">Select</button></td>`;
    });
}

const getFile = () => {
    const fileList = document.getElementById("uploadFile");
    if ("files" in fileList) {
        const file = fileList.files[0];

        if (file.length == 0) {
            appState.errors.push("Please select a file");
            handleErrors();
            return;
        }

        if (!file.name) {
            appState.errors.push("File must have a name.");
            return handleErrors();
        }

        const ext = getFileExt(file.name);

        if (ext === "nc") {
            state.file = file;
            return;
        } else {
            appState.errors.push("Filetype is not allowed. Please select a file with the type '.nc' ");
            return handleErrors();
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
        appState.errors.push("Please select a file");
        return handleErrors();
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

const selectFile = async (path) => {
    const result = await request(api + "/open_file", "POST", {
        "path": path
    });
    if (result.errors) {
        appState.errors.push(result.errors);
        return handleErrors();
    }
    console.log(result);
}