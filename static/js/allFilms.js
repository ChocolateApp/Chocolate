var closePopup = document.getElementById("crossPopup")
closePopup.addEventListener("click", function() {
    popup = document.getElementById("popup")
    popup.style.display = "none"

    document.body.style.overflow = "auto"

    var imagePopup = document.getElementsByClassName("coverPopup")[0]
    imagePopup.setAttribute("src", "");
    imagePopup.setAttribute("alt", "");
    imagePopup.setAttribute("title", "");

    var titlePopup = document.getElementsByClassName("titlePopup")[0]
    titlePopup.innerHTML = "";

    var descriptionPopup = document.getElementsByClassName("descriptionPopup")[0]
    descriptionPopup.innerHTML = "";

    var notePopup = document.getElementsByClassName("notePopup")[0]
    notePopup.innerHTML = "";

    var yearPopup = document.getElementsByClassName("yearPopup")[0]
    yearPopup.innerHTML = "";

    var genrePopup = document.getElementsByClassName("genrePopup")[0]
    genrePopup.innerHTML = "";

    var durationPopup = document.getElementsByClassName("durationPopup")[0]
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
    var similar = document.getElementsByClassName("containerSimilar")[0]
    similar.style.gridTemplateColumns = "repeat(0, 1fr)"

    var trailerVideo = document.getElementById("trailerVideo")
    trailerVideo.setAttribute("src", "")
    trailerVideo.remove()

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
    Array.from(contents).forEach(function(content) {
        content.addEventListener("click", function() {
            popup = document.getElementById("popup")
            popup.style.display = "block"

            document.body.style.overflow = "hidden !important"

            image = content.children[0]
            movieTitle = image.title;
            movieId = image.getAttribute("data-id")

            fetch("/getMovieData/" + movieId).then(function(response) {
                return response.json()
            }).then(function(data) {
                var movieTitle = data.realTitle
                var movieCast = JSON.parse(data.cast)
                var movieDescription = data.description
                var movieDuration = data.duration
                var movieGenre = JSON.parse(data.genre)
                var movieNote = data.note
                var moviePoster = data.cover
                var movieUrl = data.slug
                var movieID = data.id
                movieUrl = "/movie/" + movieID
                var movieYear = data.date
                var movieTrailer = data.bandeAnnonceUrl
                console.log(movieTrailer)
                var movieSimilar = data.similarMovies
                containerSimilar = document.getElementsByClassName("containerSimilar")[0]

                if (movieSimilar.length === 0) {
                    containerSimilar.style.display = "none"

                } else {
                    containerSimilar.style.display = "inline-grid"
                }

                for (var i = 0; i < movieSimilar.length; i++) {
                    if (i < 4) {
                        var movie = movieSimilar[i]
                        imageUrl = movie.cover
                        movieName = movie.realTitle
                        var similar = document.getElementsByClassName("containerSimilar")[0]
                        var movie = document.createElement("div")
                        movie.setAttribute("class", "movie")
                        var image = document.createElement("img")
                        image.setAttribute("class", "movieImage")
                        image.setAttribute("src", imageUrl)
                        image.setAttribute("alt", movieName)
                        image.setAttribute("title", movieName)
                        var title = document.createElement("p")
                        title.setAttribute("class", "movieTitle")
                        title.innerHTML = movieName

                        movie.appendChild(image)
                        movie.appendChild(title)
                        similar.appendChild(movie)
                    }
                }

                var childs = document.getElementsByClassName("movie")
                var childsLength = childs.length
                var similar = document.getElementsByClassName("containerSimilar")[0]
                similar.style.gridTemplateColumns = "repeat(" + childsLength + ", 1fr)"


                var imagePopup = document.getElementsByClassName("coverPopup")[0]
                imagePopup.setAttribute("src", moviePoster);
                if (imagePopup.src == "https://image.tmdb.org/t/p/originalNone") {
                    imagePopup.src = brokenPath
                }
                imagePopup.setAttribute("alt", movieTitle);
                imagePopup.setAttribute("title", movieTitle);

                var titlePopup = document.getElementsByClassName("titlePopup")[0]
                titlePopup.innerHTML = movieTitle;

                var descriptionPopup = document.getElementsByClassName("descriptionPopup")[0]
                descriptionPopup.innerHTML = movieDescription;

                var notePopup = document.getElementsByClassName("notePopup")[0]
                notePopup.innerHTML = `Note : ${movieNote}/10`;

                var yearPopup = document.getElementsByClassName("yearPopup")[0]
                yearPopup.innerHTML = `Date : ${movieYear}`;

                var genrePopup = document.getElementsByClassName("genrePopup")[0]
                var genreList = movieGenre
                var genreString = ""
                for (var i = 0; i < genreList.length; i++) {
                    genreString += genreList[i]
                    if (i != genreList.length - 1) {
                        genreString += ", "
                    }
                }
                genrePopup.innerHTML = `Genre : ${genreString}`;

                var durationPopup = document.getElementsByClassName("durationPopup")[0]
                durationPopup.innerHTML = `Durée : ${movieDuration}`;
                for (var i = 0; i < movieCast.length; i++) {
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
                for (var i = 0; i < castMembers.length; i++) {
                    castMembers[i].addEventListener("click", function() {
                        var castImage = this.children[0]
                        var castId = castImage.getAttribute("alt")
                        var castUrl = "/actor/" + castId
                        window.location.href = castUrl
                    })
                }

                var trailer = document.getElementsByClassName("containerTrailer")[0]
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

                var playButton = document.getElementsByClassName("playPopup")[0]
                playButton.setAttribute("href", movieUrl);
            })
        })
    })
}

const createObjectFromString = (str) => {
	return eval(`(function () { return ${str}; })()`);
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
            for (var i = 0; i < data.length; i++) {
                data[i]
                if (i > 0) {
                    movies = document.getElementsByClassName("movies")[0]
                    var movie = data[i]
                    let movieID = movie.id
                    var cover = document.createElement("div")
                    cover.className = "cover"
                    cover.style.marginBottom = "2vh"
                    var content = document.createElement("div")
                    content.className = "content"
                    var image = document.createElement("img")
                    image.className = "cover_movie"
                    image.src = movie.cover
                    if (image.src == "https://image.tmdb.org/t/p/originalNone") {
                        image.src = brokenPath
                    }
                    image.title = movie.title
                    image.alt = movie.realTitle
                    image.setAttribute("data-id", movieID)

                    vues = movie.vues
                    //vues is a string representing an array convert it to an array
                    vues = createObjectFromString(vues)
                    if (vues[username] !== undefined && vues[username] !== 0) {
                        timeCode = vues[username]
                        //convert the seconds to a timecode hh:mm:ss
                        timeCode = new Date(timeCode * 1000).toISOString().substr(11, 8)
                        timePopup = document.createElement("div")
                        timePopup.className = "timePopup"
                        timeP = document.createElement("p")
                        timeP.innerHTML = timeCode
                        timePopup.appendChild(timeP)
                        cover.appendChild(timePopup)
                    }
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
                    var id = movie.id
                    slug = "/movie/" + id
                    bannerImage = movie.banner
                    cssBigBanner = `background-image: linear-gradient(to bottom, rgb(255 255 255 / 0%), rgb(29 29 29)), url("${bannerImage}")`
                    imageBanner.setAttribute('style', cssBigBanner)


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

            if (data.length <= 1) {
                spinner = document.getElementsByClassName("spinner")[0]
                backgroundSpinner = document.getElementById("loaderBackground")
                spinner.style.opacity = "0"
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
                        backgroundSpinner.style.display = "none"
                    }
                })
            }}

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