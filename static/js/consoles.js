function hideLoader() {
    spinner = document.getElementById("spinner")
    backgroundSpinner = document.getElementById("loaderBackground")
    spinner.style.visibility = "hidden"
    backgroundSpinner.style.display = "none"
}

function getAllConsoles() {
    var url = window.location.href
    var library = url.split("/")[4]
    fetch(`/getAllConsoles/${library}`).then(function(response) {
        return response.json();
    }).then(function(json) {
        var systems = json;
        systems = systems.sort()
        var systemList = document.getElementById("systemList");
        for (system of systems) {
            fetch("/getConsoleData/" + system).then(function(response) {
                return response.json();
            }).then(function(json) {
                var system = json;
                var systemDiv = document.createElement("div");
                systemDiv.className = "systemDiv";
                var systemNameDiv = document.createElement("div");
                systemNameDiv.className = "systemNameDiv";
                var systemImageDiv = document.createElement("div");
                systemImageDiv.className = "systemImageDiv";
                var systemImage = document.createElement("img");
                systemImage.className = "systemImage";
                systemImage.src = system.image;
                var systemName = document.createElement("p");
                systemName.className = "systemName";
                systemName.innerHTML = system.name;
                systemImageDiv.appendChild(systemImage);
                systemNameDiv.appendChild(systemName);
                systemDiv.appendChild(systemImageDiv);
                systemDiv.appendChild(systemNameDiv);
                systemDiv.addEventListener("click", function() {
                    window.location.href = `/console/${library}/${system.name}`;
                });
                systemList.appendChild(systemDiv);
            })
        }
    })
}
getAllConsoles()
hideLoader()