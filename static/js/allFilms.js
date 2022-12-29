let closePopup = document.getElementById("crossPopup")
closePopup.addEventListener("click", function() {
    popup = document.getElementById("popup")
    popup.style.display = "none"

    document.body.style.overflow = "auto"

    let imagePopup = document.getElementsByClassName("coverPopup")[0]
    imagePopup.setAttribute("src", "");
    imagePopup.setAttribute("alt", "");
    imagePopup.setAttribute("title", "");

    let titlePopup = document.getElementsByClassName("titlePopup")[0]
    titlePopup.innerHTML = "";

    let descriptionPopup = document.getElementsByClassName("descriptionPopup")[0]
    descriptionPopup.innerHTML = "";

    let notePopup = document.getElementsByClassName("notePopup")[0]
    notePopup.innerHTML = "";

    let yearPopup = document.getElementsByClassName("yearPopup")[0]
    yearPopup.innerHTML = "";

    let genrePopup = document.getElementsByClassName("genrePopup")[0]
    genrePopup.innerHTML = "";

    let durationPopup = document.getElementsByClassName("durationPopup")[0]
    durationPopup.innerHTML = "";

    castPopup = document.getElementById("castPopup")
    castDivs = document.getElementsByClassName("castMember")
    image = document.getElementsByClassName("castImage")[0]
    while (castDivs.length > 0) {
        image.setAttribute("src", "")
        castPopup.removeChild(castDivs[0])
    }
    childs = document.getElementsByClassName("movie")
    while (childs.length > 0) {
        childs[0].remove()
    }
    let similar = document.getElementsByClassName("containerSimilar")[0]
    similar.style.gridTemplateColumns = "repeat(0, 1fr)"

    let trailerVideo = document.getElementById("trailerVideo")
    trailerVideo.setAttribute("src", "")
    trailerVideo.remove()

    let downloadMovie = document.getElementById("downloadMovieButton")
    downloadMovie.setAttribute("href", "")
})

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

function editMovie(title, library) {
    window.location.href = `/editMovie/${title}/${library}`
}

function setPopup() {
    contents = document.getElementsByClassName("content")
    canDownloadDiv = document.getElementById("canDownloadDiv")
    canDownload = canDownloadDiv.getAttribute("data-candownload") == "True"
    Array.from(contents).forEach(function(content) {
        let image = content.children[2]
        let movieId = image.getAttribute("data-id")
        content.addEventListener("click", function() {
            popup = document.getElementById("popup")
            popup.style.display = "block"

            document.body.style.overflow = "hidden !important"
            fetch("/getMovieData/" + movieId).then(function(response) {
                return response.json()
            }).then(function(data) {
                let movieTitle = data.realTitle
                let movieCast = JSON.parse(data.cast)
                let movieDescription = data.description
                let movieDuration = data.duration
                let movieGenre = JSON.parse(data.genre)
                let movieNote = data.note
                let moviePoster = data.cover
                let movieUrl = data.slug
                let movieID = data.id
                movieUrl = "/movie/" + movieID
                let movieYear = data.date
                let movieTrailer = data.bandeAnnonceUrl
                let movieSimilar = data.similarMovies
                containerSimilar = document.getElementsByClassName("containerSimilar")[0]

                if (movieSimilar.length === 0) {
                    containerSimilar.style.display = "none"

                } else {
                    containerSimilar.style.display = "inline-grid"
                }

                for (let i = 0; i < movieSimilar.length; i++) {
                    if (i < 4) {
                        let movie = movieSimilar[i]
                        imageUrl = movie.cover
                        movieName = movie.realTitle
                        let similar = document.getElementsByClassName("containerSimilar")[0]
                        movie = document.createElement("div")
                        movie.setAttribute("class", "movie")
                        let image = document.createElement("img")
                        image.setAttribute("class", "movieImage")
                        image.setAttribute("src", imageUrl)
                        image.setAttribute("alt", movieName)
                        image.setAttribute("title", movieName)
                        let title = document.createElement("p")
                        title.setAttribute("class", "movieTitle")
                        title.innerHTML = movieName

                        movie.appendChild(image)
                        movie.appendChild(title)
                        similar.appendChild(movie)
                    }
                }

                let childs = document.getElementsByClassName("movie")
                let childsLength = childs.length
                let similar = document.getElementsByClassName("containerSimilar")[0]
                similar.style.gridTemplateColumns = "repeat(" + childsLength + ", 1fr)"


                let imagePopup = document.getElementsByClassName("coverPopup")[0]
                imagePopup.setAttribute("src", moviePoster);
                if (imagePopup.src == "https://image.tmdb.org/t/p/originalNone") {
                    imagePopup.src = brokenPath
                }
                imagePopup.setAttribute("alt", movieTitle);
                imagePopup.setAttribute("title", movieTitle);

                let titlePopup = document.getElementsByClassName("titlePopup")[0]
                titlePopup.innerHTML = movieTitle;

                let descriptionPopup = document.getElementsByClassName("descriptionPopup")[0]
                descriptionPopup.innerHTML = movieDescription;

                let notePopup = document.getElementsByClassName("notePopup")[0]
                notePopup.innerHTML = `Note : ${movieNote}/10`;

                let yearPopup = document.getElementsByClassName("yearPopup")[0]
                yearPopup.innerHTML = `Date : ${movieYear}`;

                let genrePopup = document.getElementsByClassName("genrePopup")[0]
                let genreList = movieGenre
                let genreString = ""
                for (let i = 0; i < genreList.length; i++) {
                    genreString += genreList[i]
                    if (i != genreList.length - 1) {
                        genreString += ", "
                    }
                }
                genrePopup.innerHTML = `Genre : ${genreString}`;

                let durationPopup = document.getElementsByClassName("durationPopup")[0]
                durationPopup.innerHTML = `Durée : ${movieDuration}`;
                for (let i = 0; i < movieCast.length; i++) {
                    castMember = document.createElement("div")
                    castMember.className = "castMember"
                    castImage = document.createElement("img")
                    castImage.className = "castImage"
                    castImageUrl = movieCast[i][2]
                    castRealName = movieCast[i][0]
                    castId = movieCast[i][3]
                    castCharacterName = movieCast[i][1]
                    castImage.setAttribute("src", castImageUrl)
                    castImage.setAttribute("alt", castId)
                    castImage.setAttribute("title", castRealName)
                    castMember.appendChild(castImage)
                    castName = document.createElement("p")
                    castName.className = "castName"
                    castName.innerHTML = castRealName
                    castMember.appendChild(castName)
                    castCharacter = document.createElement("p")
                    castCharacter.className = "castCharacter"
                    castCharacter.innerHTML = castCharacterName
                    castMember.appendChild(castCharacter)
                    castPopup.appendChild(castMember)
                }

                castMembers = document.getElementsByClassName("castMember")
                for (let i = 0; i < castMembers.length; i++) {
                    castMembers[i].addEventListener("click", function() {
                        let castImage = this.children[0]
                        let castId = castImage.getAttribute("alt")
                        let castUrl = "/actor/" + castId
                        window.location.href = castUrl
                    })
                }

                let trailer = document.getElementsByClassName("containerTrailer")[0]
                if (movieTrailer == "") {
                    trailer.style.display = "none"
                } else {
                    trailer.style.display = "block"
                    trailerVideo = document.createElement("iframe")
                    regex = /^(http|https):\/\//g
                    if (regex.test(movieTrailer)) {
                        movieTrailer.replace(regex, "")
                    }
                    trailerVideo.setAttribute("src", movieTrailer)
                    trailerVideo.setAttribute("class", "trailerVideo")
                    trailerVideo.setAttribute("id", "trailerVideo")
                    trailer.appendChild(trailerVideo)
                }

                if (canDownload === true) {
                    downloadButton = document.getElementById("downloadMovieButton")
                    downloadButton.setAttribute("class", "downloadMovieButton")
                    downloadButton.href= "/downloadMovie/" + movieId
                }

                let playButton = document.getElementsByClassName("playPopup")[0]
                playButton.setAttribute("href", movieUrl);
            })
        })
    })
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

function removeLoader(data){
    if (data.length <= 1) {
        spinner = document.getElementsByClassName("spinner")[0]
        backgroundSpinner = document.getElementById("loaderBackground")
        spinner.style.opacity = "0"
        spinner.style.display = "none"
        backgroundSpinner.style.display = "none"
    } else {

    const imgs = document.images
    const imgsArray = Array.prototype.slice.call(document.images)

    for (img of imgsArray) {
        const acutalIndex = imgsArray.indexOf(img)
        img = imgs.item(acutalIndex)
        img.addEventListener("load", function() {
            const imagesLenght = imgs.length - 1
            if (acutalIndex == imagesLenght) {
                spinner = document.getElementsByClassName("spinner")[0]
                backgroundSpinner = document.getElementById("loaderBackground")
                spinner.style.opacity = "0"
                spinner.style.display = "none"
                backgroundSpinner.style.display = "none"
            }
        })
    }}
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
                    let movieID = movie.id
                    let cover = document.createElement("div")
                    cover.className = "cover"
                    cover.style.marginBottom = "2vh"
                    let content = document.createElement("div")
                    content.className = "content"
                    let image = document.createElement("img")
                    image.className = "cover_movie"
                    image.src = movie.cover
                    if (image.src == "https://image.tmdb.org/t/p/originalNone") {
                        image.src = brokenPath
                    }
                    image.title = movie.title
                    image.alt = movie.realTitle
                    image.setAttribute("data-id", movieID)

                    vues = movie.vues
                    duration = movie.duration
                    note = Math.round(movie.note * 10)
                    //create a circle to display the note
                    let noteCircleFront = document.createElement("div")
                    noteCircleFront.className = "noteCircleFront"
                    noteCircleFront.innerHTML = ` ${note}%`
                    
                    
                    //if note is 0, noteColor is red, if note is 100, noteColor is green
                    if (note < 50) {
                        hue = note * 1.2; // Teinte allant de 0 à 60
                      } else {
                        hue = (note - 50) * 1.2 + 60; // Teinte allant de 60 à 120
                      }

                    let noteColor = `hsl(${hue}deg, 100%, 50%)`
                                        
                    noteSVG = svgEl("svg",    {viewBox: "0 0 110 110", style: `--dash: ${1-note/100}; --color: ${noteColor}`, class: "noteSVG"});
                    circleSVG = svgEl("circle", {cx: "55", cy: "55", r: "50", fill: "transparent" });
                    circleSVGBackground = svgEl("circle", {cx: "55", cy: "55", r: "50", fill: "grey" });
                    textSVG = svgEl("text",   {x:  "55", y:  "57", "dominant-baseline": "middle", "text-anchor": "middle"});
                    noteSVG.appendChild(circleSVGBackground)
                    noteSVG.appendChild(circleSVG)
                    noteSVG.appendChild(textSVG)
                    content.appendChild(noteSVG)
                    textSVG.textContent = note+"%"
                    

                    

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
                
                    
                    content.appendChild(image)
                    cover.appendChild(content)
                    if (accountType == "Admin") {
                        pencilIcon = document.createElement("ion-icon")
                        pencilIcon.setAttribute("name", "pencil-outline")
                        pencilIcon.setAttribute("class", "md hydrated pencilIcon")
                        pencilIcon.setAttribute("title", "Edit metadata")
                        pencilIcon.setAttribute("alt", "Edit metadata")
                        pencilIcon.setAttribute("id", movie.realTitle)
                        pencilIcon.setAttribute("aria-label", "pencil outline")
                        pencilIcon.setAttribute("role", "img")
                        let theMovieName = movie.title
                        let library = movie.libraryName
                        pencilIcon.addEventListener("click", function() {
                            editMovie(theMovieName, library)
                        })
                        cover.appendChild(pencilIcon)
                    }
                    movies.appendChild(cover)

                } else {
                    bigBanner = document.getElementsByClassName("bigBanner")[0]
                    imageBanner = document.getElementsByClassName("bannerCover")[0]
                    genreBanner = document.getElementsByClassName("bannerGenre")[0]
                    titleBanner = document.getElementsByClassName("bannerTitle")[0]
                    descriptionBanner = document.getElementsByClassName("bannerDescription")[0]
                    watchNow = document.getElementsByClassName("watchNowA")[0]
                    movie = data[i]
                    let id = movie.id
                    slug = "/movie/" + id
                    bannerImage = movie.banner
                    cssBigBanner = `background-image: linear-gradient(180deg, rgba(0, 0, 0, 0) 0%, rgba(24, 24, 24, 0.85) 77.08%, #1D1D1D 100%), linear-gradient(95.97deg, #000000 0%, rgba(0, 0, 0, 0.25) 100%, #000000 100%), url("${bannerImage}")`
                    imageBanner.setAttribute('style', cssBigBanner)
                    let downloadNowA = document.getElementById("downloadNowA")
                    canDownloadDiv = document.getElementById("canDownloadDiv")
                    canDownload = canDownloadDiv.getAttribute("data-candownload") == "True"
                    if (canDownload) {
                        downloadNowA.setAttribute("href", "/downloadMovie/" + id)
                    } else {
                        downloadNowA.remove()
                    }

                    titleBanner.innerHTML = movie.realTitle
                    description = movie.description
                    descriptionBanner.innerHTML = description
                    descriptionBanner.innerHTML = descriptionBanner.innerHTML.substring(0, 200) + "..."
                    descriptionBanner.innerHTML += " <a id='lireLaSuite' href='#'>Lire la suite</a>"

                    lireLaSuite = document.getElementById("lireLaSuite")
                    lireLaSuite.addEventListener("click", function() {
                        descriptionBanner.innerHTML = description
                    })

                    genreBanner.innerHTML = JSON.parse(movie.genre).join(", ")
                    movieUrl = slug
                    watchNow.setAttribute("href", movieUrl)
                }
            }

            removeLoader(data)

            if (data.length == 1) {
                let bigBackground = document.getElementsByClassName("bannerCover")[0]
                bigBackground.style.height = "100vh"

                let bannerGenre = document.getElementsByClassName("bannerGenre")[0]
                let bannerTitle = document.getElementsByClassName("bannerTitle")[0]
                let bannerDescription = document.getElementsByClassName("bannerDescription")[0]
                let watchNow = document.getElementsByClassName("watchNowA")[0]

                bannerGenre.style.top = "46vh"
                bannerTitle.style.top = "47.5vh"
                bannerDescription.style.top = "55vh"
                watchNow.style.top = "65vh"
            }

            setPopup()
        })
    })
}

window.onload = function() {
    brokenPathDiv = document.getElementsByClassName("brokenPath")[0]
    brokenPath = brokenPathDiv.getAttribute("id")
    brokenPathDiv.parentNode.removeChild(brokenPathDiv)
    getFirstMovies()
    containerSeasons = document.getElementsByClassName("containerSeasons")[0]
    containerSeasons.style.display = "none"
}