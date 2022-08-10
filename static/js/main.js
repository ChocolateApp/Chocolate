homeButton = document.getElementById("goHome")
logo = document.getElementById("logo")

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