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

function search() {
    var search = document.getElementById("search").value
    console.log("Fonction search()")
    window.location.href = "/search/" + search
}

searchForm = document.getElementById("searchForm")
searchForm.addEventListener("submit", function(event) {
    event.preventDefault()
    search()
})