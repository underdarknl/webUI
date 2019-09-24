window.onload = async () => {
    listFilesFromServer();
    const sortable = new Sortable.default(document.querySelectorAll('tbody'), {
        draggable: 'tr'
    });

    sortable.on('sortable:start', () => console.log('sortable:start'));
    sortable.on('sortable:sort', () => console.log('sortable:sort'));
    sortable.on('sortable:sorted', () => console.log('sortable:sorted'));
    sortable.on('sortable:stop', () => console.log('sortable:stop'));
};
const api = "http://192.168.1.224:5000";
let state = {
    file: null,
    queue: [],
    buttons: {
        upload: {
            id: "uploadFile"
        }
    }
}
const request = (url, type, data = {}) => {
    if (type === "POST") {
        return fetch(url, {
                method: "POST",
                mode: "cors",
                body: data
            })
            .then(response => {
                return response.json();
            })
            .then(data => {
                return data;
            });
    } else {
        return fetch(url, {
                method: "GET"
            })
            .then(response => {
                return response.json();
            })
            .then(data => {
                return data;

            })
            .catch(error => {
                if (error == "TypeError: Failed to fetch") {
                    document.body.className = "error_server_down";
                    return;
                }
            });
    }
};

const listFilesFromServer = async () => {
    document.getElementById("tbody_files").innerHTML = "";
    const result = await request(api + "/return_files", "GET");

    if (!"result" in result) {
        return console.log(result);
    }

    result.result.map((item, index) => {
        //document.getElementById("files").innerHTML += "<figure>" + item[1] + "<figcaption><button>Select</button><figcaption></figure>";
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
    const result = await request(api + "/file_upload", "POST", formData);
    if (result.errors) {
        console.log(result.errors);
    }
    listFilesFromServer();
}