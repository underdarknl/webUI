state = {
    upload: {
        id: "uploadFile"
    }
}

const getFileExt = (file) => {
    const lastDot = file.lastIndexOf(".");
    const ext = file.substring(lastDot + 1);
    return ext;
}

const getAllFiles = () => {
    const fileList = document.getElementById(state.upload.id);
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
            console.log(file);
            return console.log("Upload file");
        } else {
            return console.log("File not allowed");
        }
    }
}