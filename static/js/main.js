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
    libraryName = actualHref.split("/")[4]
    if (search != "" && actualHref.split("/").length >= 5) {
        window.location.href = `/search/${libraryName}/${search}`
    }
}

searchForm = document.getElementById("searchForm")
searchForm.addEventListener("submit", function(event) {
    event.preventDefault()
    search()
})
//try to get .cardsIndex if it exists get the number of childrens, if it's higher than 5, block the value at 5, and edit the grid-template-columns
let cardsIndex = document.getElementsByClassName("cardsIndex")[0]
if (cardsIndex) {
    let cardsIndexChildren = cardsIndex.children
    if (cardsIndexChildren.length > 5) {
        cardsIndex.style.gridTemplateColumns = "repeat(5, 1fr)"
    } else {
        cardsIndex.style.gridTemplateColumns = "repeat(" + cardsIndexChildren.length + ", 1fr)"
    }
}