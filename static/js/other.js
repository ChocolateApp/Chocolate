function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

function editMovie(title, library) {
    window.location.href = `/editMovie/${title}/${library}`
}

const createObjectFromString = (str) => {
	return eval(`(function () { return ${str}; })()`);
}

function svgEl(name, attrs) {
    const el = document.createElementNS("http://www.w3.org/2000/svg", name)
    for ( const [ k, v ] of Object.entries(attrs) ){
        el.setAttribute(k, v);
    }
    return el
}

function removeLoader(){
    const imgs = document.images
    const imgsArray = Array.prototype.slice.call(document.images)
    imgs.length = 32
    imgsArray.splice(36, imgsArray.length - 1)
    imgsArray.splice(0, 4)
    if (imgsArray.length == 0) {
        spinner = document.getElementsByClassName("spinner")[0]
        backgroundSpinner = document.getElementById("loaderBackground")
        spinner.style.opacity = "0"
        spinner.style.display = "none"
        backgroundSpinner.style.display = "none"
    }

    for (img of imgsArray) {
        const acutalIndex = imgsArray.indexOf(img)
        img = imgs.item(acutalIndex)
        img.addEventListener("load", function() {
            const imagesLenght = imgsArray.length - 1
            console.log(`${acutalIndex}/${imagesLenght-4}`)
            if (acutalIndex == (imagesLenght-4)) {
                spinner = document.getElementsByClassName("spinner")[0]
                backgroundSpinner = document.getElementById("loaderBackground")
                spinner.style.opacity = "0"
                spinner.style.display = "none"
                backgroundSpinner.style.display = "none"
            }
        })
    }
}

function getFirstMovies() {
    movies = document.getElementsByClassName("movies")[0]
    routeToUse = movies.getAttribute("id")
    movies.id = "movies"
    let username = ""
    fetch("/whoami").then(function(response) {
        return response.json()
    }).then(function(data) {
        username = data.name
        accountType = data.accountType
    }).then(function() {
        fetch(routeToUse).then(function(response) {
            return response.json()
        }).then(function(data) {
            for (let i = 0; i < data.length; i++) {
                data[i]
                if (i > 0) {
                    movies = document.getElementsByClassName("movies")[0]
                    let movie = data[i]
                    let movieID = movie.videoHash
                    let cover = document.createElement("div")
                    cover.className = "cover"
                    cover.style.marginBottom = "2vh"
                    let content = document.createElement("div")
                    content.className = "content"
                    let image = document.createElement("img")
                    image.className = "cover_movie"
                    image.src = movie.banner
                    if (image.src == "https://image.tmdb.org/t/p/originalNone") {
                        image.src = brokenPath
                    }
                    image.title = movie.title
                    image.alt = movie.title
                    image.setAttribute("data-id", movieID)
                    image.setAttribute("loading", "lazy")

                    vues = movie.vues
                    

                    vues = createObjectFromString(vues)
                    timeCode = vues[username]
                    let timeLineBackground = document.createElement("div")
                    timeLineBackground.className = "timeLineBackground"
                    let timeLine = document.createElement("div")
                    timeLine.className = "timeLine"
                    let watchedTime = vues[username]
                    let movieDuration = movie.duration
                    //it's a timecode, convert it to seconds
                    movieDuration = movieDuration.split(":")
                    movieDuration = parseInt(movieDuration[0]) * 3600 + parseInt(movieDuration[1]) * 60 + parseInt(movieDuration[2])
                    if ((watchedTime / movieDuration) * 100 <= 100) {
                        timeLine.style.width = `${(watchedTime / movieDuration) * 100}%`
                    } else if ((watchedTime / movieDuration) * 100 > 100) {
                        timeLine.style.width = "100%"
                    } else {
                        timeLine.style.width = "0%"
                    }
                    timeLineBackground.appendChild(timeLine)
                    content.appendChild(timeLineBackground)
                    
                    cover.addEventListener("click", function() {
                        window.location.href = "/otherVideo/" + movieID
                    })
                    
                    content.appendChild(image)
                    cover.appendChild(content)
                    movies.appendChild(cover)

                } else {
                    bigBanner = document.getElementsByClassName("bigBanner")[0]
                    imageBanner = document.getElementsByClassName("bannerCover")[0]
                    titleBanner = document.getElementsByClassName("bannerTitle")[0]
                    watchNow = document.getElementsByClassName("watchNowA")[0]
                    movie = data[i]
                    let id = movie.videoHash
                    slug = "/otherVideo/" + id
                    bannerImage = movie.banner
                    cssBigBanner = `background-image: linear-gradient(180deg, rgba(0, 0, 0, 0) 0%, rgba(24, 24, 24, 0.85) 77.08%, #1D1D1D 100%), linear-gradient(95.97deg, #000000 0%, rgba(0, 0, 0, 0.25) 100%, #000000 100%), url("${bannerImage}")`
                    imageBanner.setAttribute('style', cssBigBanner)
                    
                    titleBanner.innerHTML = movie.title
                    
                    movieUrl = slug
                    watchNow.setAttribute("href", movieUrl)
                }
            }

            removeLoader(data)

            if (data.length == 1) {
                let bigBackground = document.getElementsByClassName("bannerCover")[0]
                bigBackground.style.height = "100vh"

                let bannerTitle = document.getElementsByClassName("bannerTitle")[0]
                let bannerDescription = document.getElementsByClassName("bannerDescription")[0]
                let watchNow = document.getElementsByClassName("watchNowA")[0]

                bannerGenre.style.top = "46vh"
                bannerTitle.style.top = "47.5vh"
                bannerDescription.style.top = "55vh"
                watchNow.style.top = "65vh"
            }
        })
    })
}

window.onload = function() {
    brokenPathDiv = document.getElementsByClassName("brokenPath")[0]
    brokenPath = brokenPathDiv.getAttribute("id")
    brokenPathDiv.parentNode.removeChild(brokenPathDiv)
    getFirstMovies()
    removeLoader()
}