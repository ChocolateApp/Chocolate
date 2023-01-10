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
    libraryName = actualHref.split("/")[4].replace("#", "")
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
// Register Service Worker
if ('serviceWorker' in navigator) {
    navigator.serviceWorker
    .register('/service-worker.js')
    .then(function(registration) {
        console.log('Service Worker Registered');
        return registration;
    })
    .catch(function(err) {
        console.error('Unable to register service worker.', err);
    });
}

window.addEventListener('online', function(e) {
    console.log("You are online");
}, false);

function rescanLib() {
    button = document.getElementById("rescanButton")
    url = button.getAttribute("data-url")
    texts = ["Scanning", "Scanning.", "Scanning..", "Scanning..."]
    button.disabled = true

    //setInterval
    var i = 0
    var interval = setInterval(function() {
        i++
        if (i == 4) {
            i = 0
        }
        button.innerHTML = `<ion-icon name="refresh-outline"></ion-icon>${texts[i]}`
    }, 500)

    //fetch with get
    fetch(url, {
        method: "GET",
        headers: {
            "Content-Type": "application/json"
        }}).then(function(response) {
            return response.json()
        }).then(function(data) {
            console.log(data)
            if (data == true) {
                clearInterval(interval)
                button.innerHTML = '<ion-icon name="refresh-outline"></ion-icon>Done'
                //wait 2 seconds and reload the page
                setTimeout(function() {
                    window.location.reload()
                }, 2000)
            } else {
                clearInterval(interval)
                button.innerHTML = '<ion-icon name="refresh-outline"></ion-icon>Error'
                button.classList.add("error")
            }
        })
}