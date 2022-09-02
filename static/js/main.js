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
    actualHref = window.location.href
    if (actualHref.includes("serie")) {
        attribute = "series/"
    } else {
        attribute = "movies/"
    }
    if (search != "") {
        window.location.href = "/search/" + attribute + search
    }
}

searchForm = document.getElementById("searchForm")
searchForm.addEventListener("submit", function(event) {
    event.preventDefault()
    search()
})