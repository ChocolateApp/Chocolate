homeButton = document.getElementById("goHome")
logo = document.getElementById("logo")
homeText = document.getElementsByClassName("title")[0]

homeText.addEventListener("click", function() {
    window.location.href = "/home"
})

logo.addEventListener("click", function() {
    window.location.href = "/home"
})

homeButton.addEventListener("click", function() {
    window.location.href = "/home"
})