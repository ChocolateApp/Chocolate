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

function goToSeason(id) {
    href = "/season/" + id
    window.location.href = href
}

function setPopup() {
    contents = document.getElementsByClassName("content")
    Array.from(contents).forEach(function(content) {
        content.addEventListener("click", function() {
            var mediaType = content.getAttribute("mediaType")
            popup = document.getElementById("popup")
            popup.style.display = "block"
            document.body.style.overflow = "hidden"
            image = content.children[0].children[0]
            movieTitle = image.title;
            movieId = image.getAttribute("data-id")
            if (mediaType == "movie") {
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
                    var movieTrailer = data.bandeAnnonce
                    var movieSimilar = data.similarMovies
                    containerSimilar = document.getElementsByClassName("containerSimilar")[0]

                    if (movieSimilar.length === 0) {
                        containerSimilar.style.display = "none"

                    } else {
                        containerSimilar.style.display = "inline-grid"
                    }

                    for (var i = 0; i < movieSimilar.length; i++) {
                        var movie = movieSimilar[i]
                        imageUrl = movie.cover
                        movieName = movie.realTitle
                        movieId = movie.id
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
            } else {
                fetch("/getSerieData/" + movieId).then(function(response) {
                    return response.json()
                }).then(function(data) {
                    var serieTitle = data.originalName
                    var serieCast = data.cast
                    var serieDescription = data.description
                    var serieDuration = data.duration
                    var serieGenre = data.genre
                    var serieNote = data.note
                    var seriePoster = data.serieCoverPath
                    var serieUrl = data.slug
                    var serieYear = data.date
                    var serieTrailer = data.bandeAnnonceUrl
                    var serieSimilar = data.similarSeries
                    var serieSeasons = data.seasons
                    containerSimilar = document.getElementsByClassName("containerSimilar")[0]
                    containerSeasons = document.getElementsByClassName("containerSeasons")[0]
    
                    if (serieSimilar == undefined || serieSimilar.length === 0) {
                        containerSimilar.style.display = "none"
    
                    } else {
                        containerSimilar.style.display = "inline-grid"
    
    
                        for (var i = 0; i < serieSimilar.length; i++) {
                            if (i < 4) {
                                var serie = serieSimilar[i]
                                imageUrl = serie.cover
                                serieName = serie.realTitle
                                var similar = document.getElementsByClassName("containerSimilar")[0]
                                var serie = document.createElement("div")
                                serie.setAttribute("class", "serie")
                                var image = document.createElement("img")
                                image.setAttribute("class", "serieImage")
                                image.setAttribute("src", imageUrl)
                                image.setAttribute("alt", serieName)
                                image.setAttribute("title", serieName)
                                var title = document.createElement("p")
                                title.setAttribute("class", "serieTitle")
                                title.innerHTML = serieName
    
                                serie.appendChild(image)
                                serie.appendChild(title)
                                similar.appendChild(serie)
                            }
                        }
                    }
                    serieSeasons = Object.values(serieSeasons)
                    for (season of serieSeasons) {
                        seasonCover = season.seasonCoverPath
                        seasonDescription = season.seasonDescription
                        seasonName = season.seasonName
                        seasonEpisodesNumber = season.episodesNumber
                        seasonNumber = season.seasonNumber
                        seasonUrl = "/serie/" + serieTitle + "/" + seasonNumber
                        seasonRelease = season.release
                        seasonId = season.seasonId
                        var seasonDiv = document.createElement("div")
                        seasonDiv.className = "season"
                        seasonDiv.setAttribute("id", seasonNumber)
                        seasonDiv.setAttribute("onclick", `goToSeason("${seasonId}")`)
    
                        var seasonCoverImage = document.createElement("img")
                        seasonCoverImage.className = "seasonCoverImage"
                        seasonCoverImage.setAttribute("src", seasonCover)
                        seasonCoverImage.setAttribute("alt", seasonName)
                        seasonCoverImage.setAttribute("title", seasonName)
                        seasonCoverImage.setAttribute("onclick", `goToSeason("${seasonId}")`)
    
                        var seasonNameP = document.createElement("p")
                        seasonNameP.className = "seasonTitle"
                        seasonNameP.innerHTML = seasonName
                        seasonNameP.setAttribute("onclick", `goToSeason("${seasonId}")`)
    
                        seasonDiv.appendChild(seasonCoverImage)
                        seasonDiv.appendChild(seasonNameP)
                        containerSeasons.appendChild(seasonDiv)
                    }
    
                    var childs = document.getElementsByClassName("serie")
                    var childsLength = childs.length
                    var similar = document.getElementsByClassName("containerSimilar")[0]
                    similar.style.gridTemplateColumns = "repeat(" + childsLength + ", 1fr)"
    
    
                    var imagePopup = document.getElementsByClassName("coverPopup")[0]
                    imagePopup.setAttribute("src", seriePoster);
                    if (imagePopup.src == "https://image.tmdb.org/t/p/originalNone") {
                        imagePopup.src = brokenPath
                    }
                    imagePopup.setAttribute("alt", serieTitle);
                    imagePopup.setAttribute("title", serieTitle);
    
                    var titlePopup = document.getElementsByClassName("titlePopup")[0]
                    titlePopup.innerHTML = serieTitle;
    
                    var descriptionPopup = document.getElementsByClassName("descriptionPopup")[0]
                    descriptionPopup.innerHTML = serieDescription;
    
                    var notePopup = document.getElementsByClassName("notePopup")[0]
                    notePopup.innerHTML = `Note : ${serieNote}/10`;
    
                    var yearPopup = document.getElementsByClassName("yearPopup")[0]
                    yearPopup.innerHTML = `Date : ${serieYear}`;
    
                    var genrePopup = document.getElementsByClassName("genrePopup")[0]
                    var genreList = JSON.parse(serieGenre)
                    genreString = genreList.join(", ")
                    genrePopup.innerHTML = `Genre : ${genreString}`;
    
                    var durationPopup = document.getElementsByClassName("durationPopup")[0]
                    durationPopup.innerHTML = `Durée : ${serieDuration}`;
    
                    serieCast = JSON.parse(serieCast)
                    for (var i = 0; i < serieCast.length; i++) {
                        cast = serieCast[i]
                        
                        castMember = document.createElement("div")
                        castMember.className = "castMember"
                        castImage = document.createElement("img")
                        castImage.className = "castImage"
                        castImageUrl = cast[2]
                        if (castImageUrl == "None") {
                            castImage.src = brokenPath
                        }
                        castRealName = cast[0]
                        castCharacterName = cast[1]
                        castImage.setAttribute("src", castImageUrl)
                        castImage.setAttribute("alt", cast[3])
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
                    if (serieTrailer == "") {
                        trailer.style.display = "none"
                    } else {
                        trailer.style.display = "block"
                        trailerVideo = document.createElement("iframe")
                        regex = /^(http|https):\/\//g
                        if (regex.test(serieTrailer)) {
                            serieTrailer.replace(regex, "")
                        }
                        trailerVideo.setAttribute("src", serieTrailer)
                        trailerVideo.setAttribute("class", "trailerVideo")
                        trailerVideo.setAttribute("id", "trailerVideo")
                        trailer.appendChild(trailerVideo)
                    }
    
                    var playButton = document.getElementsByClassName("playPopup")[0]
                    playButton.setAttribute("href", serieUrl);
                })
            }
        })
    })
    let moviesTitleH2 = document.getElementsByClassName("moviesTitle")[0]
    let seriesTitleH2 = document.getElementsByClassName("seriesTitle")[0]
    let actorMovieDiv = document.getElementsByClassName("actorMoviesList")[0]
    let actorSerieDiv = document.getElementsByClassName("actorSeriesList")[0]

    let numberOfMovies = actorMovieDiv.children.length
    let numberOfSeries = actorSerieDiv.children.length

    if (numberOfSeries == 0) {
        seriesTitleH2.style.display = "none"
        actorSerieDiv.style.display = "none"
    } else if (numberOfSeries <= 3) {
        seriesTitleH2.style.display = "block"
        actorSerieDiv.style.gridTemplateColumns = "repeat(" + numberOfSeries + ", 1fr)"
        actorSerieDiv.style.display = "grid"
    } else {
        seriesTitleH2.style.display = "block"
        actorSerieDiv.style.gridTemplateColumns = "repeat(3, 1fr)"
        actorSerieDiv.style.display = "grid"
    }
    
    if (numberOfMovies == 0) {
        moviesTitleH2.style.display = "none"
        actorMovieDiv.style.display = "none"
    } else if (numberOfMovies <= 3) {
        moviesTitleH2.style.display = "block"
        actorMovieDiv.style.gridTemplateColumns = "repeat(" + numberOfMovies + ", 1fr)"
        actorMovieDiv.style.display = "grid"
    } else {
        moviesTitleH2.style.display = "block"
        actorMovieDiv.style.gridTemplateColumns = "repeat(3, 1fr)"
        actorMovieDiv.style.display = "grid"
    }
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
        actorSeries = data.actorSeries

        actorNameTitle = document.getElementsByClassName("actorName")[0]
        actorNameTitle.innerHTML = actorName

        actorMovieDiv = document.getElementsByClassName("actorMoviesList")[0]
        actorSerieDiv = document.getElementsByClassName("actorSeriesList")[0]
        seriesTitleH2 = document.getElementsByClassName("seriesTitle")[0]

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
            realTitle = actorMovies[i].title
            cover = actorMovies[i].cover
            actorMovie = document.createElement("div")
            actorMovie.setAttribute("class", "actorMovie cover")
            actorMovie.setAttribute("id", "cover")

            actorMovieContent = document.createElement("div")
            actorMovieContent.setAttribute("class", "actorMovieContent content")
            actorMovieContent.setAttribute("mediaType", "movie")

            actorMoviePicture = document.createElement("img")
            actorMoviePicture.setAttribute("class", "actorMoviePicture cover_movie")
            actorMoviePicture.setAttribute("src", cover)
            actorMoviePicture.setAttribute("alt", realTitle)
            actorMoviePicture.setAttribute("title", realTitle)
            actorMoviePicture.setAttribute("data-id", actorMovies[i].id)
            actorMovieTitle = document.createElement("p")
            actorMovieTitle.setAttribute("class", "actorMovieTitle")
            actorMovieTitle.innerHTML = realTitle

            actorMovie.appendChild(actorMoviePicture)
            actorMovie.appendChild(actorMovieTitle)
            actorMovieContent.appendChild(actorMovie)
            actorMovieDiv.appendChild(actorMovieContent)
        }

        for (i = 0; i < actorSeries.length; i++) {
            realTitle = actorSeries[i].name
            cover = actorSeries[i].serieCoverPath
            actorSerie = document.createElement("div")
            actorSerie.setAttribute("class", "actorSerie cover")
            actorSerie.setAttribute("id", "cover")

            actorSerieContent = document.createElement("div")
            actorSerieContent.setAttribute("class", "actorSerieContent content")
            actorSerieContent.setAttribute("mediaType", "serie")

            actorSeriePicture = document.createElement("img")
            actorSeriePicture.setAttribute("class", "actorSeriePicture cover_movie")
            actorSeriePicture.setAttribute("src", cover)
            actorSeriePicture.setAttribute("alt", realTitle)
            actorSeriePicture.setAttribute("title", realTitle)
            actorSeriePicture.setAttribute("data-id", actorSeries[i].id)
            actorSerieTitle = document.createElement("p")
            actorSerieTitle.setAttribute("class", "actorSerieTitle")
            actorSerieTitle.innerHTML = realTitle

            actorSerie.appendChild(actorSeriePicture)
            actorSerie.appendChild(actorSerieTitle)
            actorSerieContent.appendChild(actorSerie)
            actorSerieDiv.appendChild(actorSerieContent)
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