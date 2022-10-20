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

function createAccount(event) {
    form = document.getElementById("createAccount")
    form.action = "/createAccount"
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

    typeInputList = document.getElementById("type")
    typeInputList.addEventListener("change", function() {
        if (typeInputList.value == "Kid") {
            passwordAccountCreator = document.getElementsByClassName("passwordAccountCreator")[0]
            passwordAccountCreator.style.display = "none"
        } else {
            passwordAccountCreator = document.getElementsByClassName("passwordAccountCreator")[0]
            passwordAccountCreator.style.display = "block"
        }
    })

}