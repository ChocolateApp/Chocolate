function saveSettings(event) {
    event.preventDefault()
    language = document.getElementById("language").value
    document.cookie = "language=" + language + "; path=/";
    port = document.getElementById("port").value
    document.cookie = "port=" + port + "; path=/";

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
    portCookie = getCookie("port")
    document.getElementById("port").value = portCookie
}