const api = "http://192.168.1.224:5000/";

let state = {
    file: null,
    queue: [],
    buttons: {
        upload: {
            id: "uploadFile"
        }
    }
}

const test = async () => {
    if (state.file == null) {
        return console.log("No file selected");
    }
    let formData = new FormData();
    formData.append("file", state.file);

    const result = await fetch(api + "file_upload", {
            method: "POST",
            mode: "cors",
            body: formData
        })
        .then(response => {
            return response.json();
        })
        .then(data => {
            return data;
        });
    getFileList();
}

const getFileList = async () => {
    const result = await request(api + "return_files", {}, "GET");
    if (!"result" in result) {
        return console.log(result);
    }
    if (result.length == 0) {
        return console.log("No files on the server")
    }

    result.result.map((item, index) => {
        document.getElementById("files").innerHTML += "<figure>" + item[1] + "<figcaption><button>Select</button><figcaption></figure>";
    });
}

const getFileExt = (file) => {
    const lastDot = file.lastIndexOf(".");
    const ext = file.substring(lastDot + 1);
    return ext;
}

const getAllFiles = () => {
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

getFileList();