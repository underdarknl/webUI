const request = (url, data, type) => {
    if (type === "POST") {
        return fetch(url, {
                method: "POST",
                mode: "cors",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(data)
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
                    return (state.errors = "Server is down please start the server");
                }
                return console.log(error);
            });
    }
};