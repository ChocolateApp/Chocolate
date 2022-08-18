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

window.onload = function() {
    if (document.cookie.includes("language=")) {
        language = document.cookie.split(";")[0].split("=")[1]
        document.getElementById("language").value = language
    }

}