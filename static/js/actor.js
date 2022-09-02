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

    trailerVideo = document.getElementsByClassName("containerTrailer")[0]
    while (trailerVideo.firstChild) {
        trailerVideo.removeChild(trailerVideo.firstChild)
    }
})

function setPopup() {
    contents = document.getElementsByClassName("content")
    Array.from(contents).forEach(function(content) {
        content.addEventListener("click", function() {
            popup = document.getElementById("popup")
            popup.style.display = "block"

            document.body.style.overflow = "hidden"

            image = content.children[0].children[0]
            movieTitle = image.title;

            fetch("/getMovieData/" + movieTitle).then(function(response) {
                return response.json()
            }).then(function(data) {
                var movieTitle = data.realTitle

                var movieCast = data.cast
                var movieDescription = data.description
                var movieDuration = data.duration
                var movieGenre = data.genre
                var movieNote = data.note
                var moviePoster = data.cover
                var movieUrl = data.slug
                movieUrl = "/movie/" + movieUrl
                var movieYear = data.date
                var movieTrailer = data.bandeAnnonce
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
                    castCharacterName = movieCast[i][1]
                    castImage.setAttribute("src", castImageUrl)
                    castImage.setAttribute("alt", castRealName)
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
                        var castRealName = castImage.getAttribute("alt")
                        var castUrl = "/actor/" + castRealName
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

function getActorMovies() {
    route = document.getElementById("routeToUse")
    routeToUse = route.getAttribute("class")
    route.parentNode.removeChild(route)
    fetch(routeToUse).then(function(response) {
        return response.json()
    }).then(function(data) {

        actorName = data.actorName
        actorImageLink = data.actorImage
        actorDescriptionText = data.actorDescription
        actorBirthday = data.actorBirthday
        actorBirthplace = data.actorBirthplace
        actorMovies = data.actorMovies

        actorNameTitle = document.getElementsByClassName("actorName")[0]
        actorNameTitle.innerHTML = actorName

        actorMovieDiv = document.getElementsByClassName("actorMoviesList")[0]
        moviesTitleH2 = document.getElementsByClassName("moviesTitle")[0]

        actorImage = document.getElementsByClassName("actorPicture")[0]
        actorImage.setAttribute("src", actorImageLink)
        actorImage.setAttribute("alt", actorName)
        actorImage.setAttribute("title", actorName)

        actorDescription = document.getElementsByClassName("actorBiography")[0]
        actorDescription.innerHTML = actorDescriptionText
        if (actorDescription.length > 1100) {
            actorDescription.innerHTML = actorDescription.innerHTML.substring(0, 1100) + "..."
            actorDescription.innerHTML += " <a id='lireLaSuite' href='#'>Lire la suite</a>"
            lireLaSuite = document.getElementById("lireLaSuite")
            lireLaSuite.addEventListener("click", function() {
                actorDescription.innerHTML = actorDescriptionText
                actorInformation = document.getElementById("actorInformations")
                actorInformation.style.overflow = "scroll"
            })
        }



        for (i = 0; i < actorMovies.length; i++) {
            realTitle = actorMovies[i].realTitle
            cover = actorMovies[i].cover
            actorMovie = document.createElement("div")
            actorMovie.setAttribute("class", "actorMovie cover")
            actorMovie.setAttribute("id", "cover")

            actorMovieContent = document.createElement("div")
            actorMovieContent.setAttribute("class", "actorMovieContent content")

            actorMoviePicture = document.createElement("img")
            actorMoviePicture.setAttribute("class", "actorMoviePicture cover_movie")
            actorMoviePicture.setAttribute("src", cover)
            actorMoviePicture.setAttribute("alt", realTitle)
            actorMoviePicture.setAttribute("title", realTitle)

            actorMovieTitle = document.createElement("p")
            actorMovieTitle.setAttribute("class", "actorMovieTitle")
            actorMovieTitle.innerHTML = realTitle

            actorMovie.appendChild(actorMoviePicture)
            actorMovie.appendChild(actorMovieTitle)
            actorMovieContent.appendChild(actorMovie)
            actorMovieDiv.appendChild(actorMovieContent)

        }

        if (actorMovies.length === 1) {
            actorMovieDiv.style.gridTemplateColumns = "repeat(1, 1fr)"
            actorMovieDiv.style.display = "inline-grid"
            moviesTitleH2.style.display = "block"
        } else if (actorMovies.length === 2) {
            actorMovieDiv.style.gridTemplateColumns = "repeat(2, 1fr)"
            actorMovieDiv.style.display = "inline-grid"
            moviesTitleH2.style.display = "block"
        } else if (actorMovies.length >= 3) {
            actorMovieDiv.style.gridTemplateColumns = "repeat(3, 1fr)"
            actorMovieDiv.style.display = "inline-grid"
            moviesTitleH2.style.display = "block"
        } else {
            moviesTitleH2.style.display = "none"
            actorMovieDiv.style.display = "none"
        }
        setPopup()
    })
}


window.onload = function() {
    brokenPathDiv = document.getElementsByClassName("brokenPath")[0]
    brokenPath = brokenPathDiv.getAttribute("id")
    brokenPathDiv.parentNode.removeChild(brokenPathDiv)
    getActorMovies()
}