function saveSettings(event) {
    event.preventDefault()
    language = document.getElementById("language").value
    document.cookie = "language=" + language + "; path=/";
    port = document.getElementById("port").value

    if (port === "8000" || port === "8800") {
        alert("The port " + port + " is reserved for the web server. Please choose another port.")
        return
    }

    form = document.getElementById("saveSettingsForm")
    form.action = "/saveSettings"
    form.submit()
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

window.onload = function() {
    languageCookie = getCookie("language")
    document.getElementById("language").value = languageCookie
}