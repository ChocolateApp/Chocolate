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
    childs = document.getElementsByClassName("serie")
    while (childs.length > 0) {
        childs[0].remove()
    }
    var similar = document.getElementsByClassName("containerSimilar")[0]
    similar.style.gridTemplateColumns = "repeat(0, 1fr)"
    similar.innerHTML = ""

    const seasons = document.getElementsByClassName("containerSeasons")[0]
    seasons.innerHTML = ""

    var trailerVideo = document.getElementById("trailerVideo")
    try {
        trailerVideo.setAttribute("src", "")
        trailerVideo.remove()
    } catch (error) {
        console.log("Don't find trailerVideo")
    }

})

function goToSeason(id) {
    href = "/season/" + id
    window.location.href = href
}

function setPopup() {
    covers = document.getElementsByClassName("cover")
    for (var i = 0; i < covers.length; i++) {
        covers[i].addEventListener("click", function() {

            popup = document.getElementById("popup")
            popup.style.display = "block"

            document.body.style.overflow = "hidden !important"

            var image = this.children[0].children[0]
            var serieTitle = image.getAttribute("title");
            let serieId = image.getAttribute("serieid")
            fetch("/getSerieData/" + serieId).then(function(response) {
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
        })
    }
    const watchNowA = document.getElementsByClassName("watchNowA")[0]
    watchNowA.addEventListener("click", function() {

        popup = document.getElementById("popup")
        popup.style.display = "block"

        document.body.style.overflow = "hidden !important"

        var imageBanner = document.getElementsByClassName("bannerCover")[0]
        serieId = imageBanner.getAttribute("serieId")

        fetch("/getSerieData/" + serieId).then(function(response) {
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
            var serieTrailer = data.bandeAnnonce
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
                        imageUrl = serie.serieCoverPath
                        serieName = serie.originalName
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
            serieSeasonsKeys = Object.keys(serieSeasons)
            for (keys of serieSeasonsKeys) {
                season = serieSeasons[keys]
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

            serieSeasonsLength = serieSeasons.length
            containerSeasons = document.getElementsByClassName("containerSeasons")[0]
            if (serieSeasonsLength >= 4) {
                containerSeasons.style.gridTemplateColumns = "repeat(4, 1fr)"
            } else if (serieSeasonsLength == 0) {
                containerSeasons.style.display = "none"
            } else {
                containerSeasons.style.gridTemplateColumns = "repeat(" + serieSeasonsLength + ", 1fr)"
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
            var genreString = genreList.join(", ")

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
                castId = cast[3]
                castImage.setAttribute("src", castImageUrl)
                castImage.setAttribute("alt", cast[4])
                castImage.setAttribute("title", castId)
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
                    var castId = castImage.getAttribute("title")
                    var castUrl = "/actor/" + castId
                    window.location.href = castUrl
                })
            }

            var trailer = document.getElementsByClassName("containerTrailer")[0]
            if (serieTrailer == undefined || serieTrailer == "") {
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
    })
}

let expanded = false;

function showCheckboxes() {
    var checkboxes = document.getElementById("checkboxes");
    if (!expanded) {
      checkboxes.style.display = "block";
      expanded = true;
    } else {
      checkboxes.style.display = "none";
      expanded = false;
    }
  }


function getFirstSeries() {
    series = document.getElementsByClassName("series")[0]
    routeToUse = series.getAttribute("id")
    series.id = "series"
    let allGenres = []

    fetch(routeToUse).then(function(response) {
        return response.json()
    }).then(function(data) {
        data = Object.entries(data)
        for (serie of data) {
            index = data.indexOf(serie)
            if (index === 0) {
                bigBanner = document.getElementsByClassName("bigBanner")[0]
                imageBanner = document.getElementsByClassName("bannerCover")[0]
                genreBanner = document.getElementsByClassName("bannerGenre")[0]
                titleBanner = document.getElementsByClassName("bannerTitle")[0]
                descriptionBanner = document.getElementsByClassName("bannerDescription")[0]
                watchNow = document.getElementsByClassName("watchNowA")[0]

                bannerImage = serie[1]['banniere']
                cssBigBanner = `background-image: linear-gradient(to bottom, rgb(255 255 255 / 0%), rgb(29 29 29)), url("${bannerImage}");`
                imageBanner.setAttribute('style', cssBigBanner)
                imageBanner.setAttribute('serieid', serie[1]['id'])

                titleBanner.innerHTML = serie[1]['name']
                fullDescription = serie[1]['description']
                if (fullDescription.length > 200) {
                    descriptionBanner.innerHTML = fullDescription.substring(0, 200) + "..."
                    descriptionBanner.innerHTML += " <a id='lireLaSuite' href='#'>Lire la suite</a>"

                    lireLaSuite = document.getElementById("lireLaSuite")
                    lireLaSuite.addEventListener("click", function() {
                        descriptionBanner.innerHTML = fullDescription
                    })
                } else {
                    descriptionBanner.innerHTML = fullDescription
                }

                genres = serie[1]['genre']
                genre = JSON.parse(genres)
                genres = genre.join(", ")
                genreBanner.innerHTML += genres
            } else {
                series = document.getElementsByClassName("series")[0]
                var cover = document.createElement("div")
                cover.className = "cover"

                let genres = serie[1]["genre"]
                genres = JSON.parse(genres)
                for (let genre of genres) {
                    if (cover.getAttribute("data-genre") !== null) {
                        cover.setAttribute("data-genre", `${cover.getAttribute("data-genre")} ${genre}`)

                    } else {
                        cover.setAttribute("data-genre", `${genre}`)
                    }

                    if (allGenres.includes(genre) === false) {
                        allGenres.push(genre)
                    }
                }
                
                cover.setAttribute("data-title", serie[1]["name"])
                cover.setAttribute("data-rating", serie[1]["note"])
                let dateString = serie[1]["date"];
                const dateParts = dateString.split("-");
                const day = parseInt(dateParts[2], 10);
                const month = parseInt(dateParts[1], 10);
                const year = parseInt(dateParts[0], 10);
                const daysInMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
                let daysSinceStartOfYear = 0;
                
                for (let i = 0; i < month - 1; i++) {
                  daysSinceStartOfYear += daysInMonth[i];
                }
                
                daysSinceStartOfYear += day;
                const daysSinceStartOfTime = (year * 365) + daysSinceStartOfYear;

                cover.setAttribute("data-date", daysSinceStartOfTime)


                var content = document.createElement("div")
                content.className = "content"
                var image = document.createElement("img")
                image.className = "cover_serie"
                if (serie[1]['serieCoverPath'] == "https://image.tmdb.org/t/p/originalNone" || serie[1]['serieCoverPath'] == undefined || serie[1]['serieCoverPath'] == "undefined" || serie[1]['serieCoverPath'] == "") {
                    image.src = brokenPath
                } else {
                    image.src = serie[1]['serieCoverPath']
                }
                image.title = serie[0]
                image.alt = serie[0]
                image.setAttribute("serieId", serie[1]['id'].toString())
                image.setAttribute("loading", "lazy");

                content.appendChild(image)
                cover.appendChild(content)
                series.appendChild(cover)
            }
        }

        

        if (data.length == 1) {
            let bigBackground = document.getElementsByClassName("bannerCover")[0]
            bigBackground.style.height = "100vh"

            let bannerGenre = document.getElementsByClassName("bannerGenre")[0]
            let bannerTitle = document.getElementsByClassName("bannerTitle")[0]
            let bannerDescription = document.getElementsByClassName("bannerDescription")[0]
            let watchNow = document.getElementsByClassName("watchNowA")[0]
            let rescanButton = document.getElementById("rescanButton")

            let selectA = document.getElementsByClassName("selectA")[0]
            let sortA = document.getElementsByClassName("sortA")[0]

            bannerGenre.style.top = "46vh"
            bannerTitle.style.top = "47.5vh"
            bannerDescription.style.top = "55vh"
            watchNow.style.top = "65vh"
            rescanButton.style.marginTop = "65vh"

            selectA.style.display = "none"
            sortA.style.display = "none"
        }

        
        allGenres.sort()
        for (const genre of allGenres) {
            let checkboxes = document.getElementById("checkboxes")
            let checkbox = document.createElement("input")
            checkbox.setAttribute("type", "checkbox")

            checkbox.setAttribute("id", genre)
            checkbox.setAttribute("name", genre)
            checkbox.setAttribute("value", genre)
            checkbox.setAttribute("class", "checkboxGenre")
            
            let label = document.createElement("label")
            label.setAttribute("for", genre)
            label.appendChild(checkbox)

            label.innerHTML += `${genre}`
            checkboxes.appendChild(label)
        }

        removeLoader(data)

        setPopup()
    })
}

function showLoader() {
    spinner = document.getElementsByClassName("spinner")[0]
    backgroundSpinner = document.getElementById("loaderBackground")
    spinner.style.opacity = "1"
    spinner.style.display = "block"
    backgroundSpinner.style.display = "block"
}

function forceHideLoader() {
    let loaderBackground = document.getElementById("loaderBackground")
    loaderBackground.style.display = "none"
    let spinner = document.getElementsByClassName("spinner")[0]
    spinner.style.display = "none"
    spinner.style.opacity = "0"
}

let oldSelectValue = "title"
let alreadySorted = false

function sortFilms() {
    let select = document.getElementById("sortSelect")
    let selectValue = select.value
    if (selectValue == "title") {
        orderByAlphabetical()
    } else if (selectValue == "date") {
        orderByDate()
    } else if (selectValue == "rating") {
        orderByRating()
    }
    select.options[0].innerText = select.options[select.selectedIndex].label;
	select.selectedIndex = 0;
}

function orderByAlphabetical() {
    showLoader()
    let allMovies = document.getElementById("series")
    let movies = allMovies.children
    let moviesArray = []
    for (let i = 0; i < movies.length; i++) {
        moviesArray.push(movies[i])
    }
    moviesArray.sort(function(a, b) {
        let titleA = a.getAttribute("data-title")
        let titleB = b.getAttribute("data-title")
        if (titleA < titleB) {
            return -1
        } else if (titleA > titleB) {
            return 1
        }
        return 0
    })
    allMovies.innerHTML = ""
    if (oldSelectValue == "title") {
        moviesArray.reverse()
        oldSelectValue = "titleReverse"
    } else {
        oldSelectValue = "title"
    }

    for (let i = 0; i < moviesArray.length; i++) {
        allMovies.appendChild(moviesArray[i])
    }
    
    forceHideLoader()
}

function orderByRating() {
    showLoader()
    let allMovies = document.getElementById("series")
    let movies = allMovies.children
    let moviesArray = []
    for (let i = 0; i < movies.length; i++) {
        moviesArray.push(movies[i])
    }
    moviesArray.sort(function(a, b) {
        let ratingA = a.getAttribute("data-rating")
        let ratingB = b.getAttribute("data-rating")
        if (ratingA < ratingB) {
            return 1
        } else if (ratingA > ratingB) {
            return -1
        } else {
            return 0
        }
    })
    if (oldSelectValue == "rating") {
        moviesArray.reverse()
        oldSelectValue = "ratingReverse"
    } else {
        oldSelectValue = "rating"
    }


    allMovies.innerHTML = ""
    for (let i = 0; i < moviesArray.length; i++) {
        allMovies.appendChild(moviesArray[i])
    }
    forceHideLoader()
}

function orderByDate() {
    showLoader()
    let allMovies = document.getElementById("series")
    let movies = allMovies.children
    let moviesArray = []
    for (let i = 0; i < movies.length; i++) {
        moviesArray.push(movies[i])
    }
    moviesArray.sort(function(a, b) {
        let dateA = a.getAttribute("data-date")
        let dateB = b.getAttribute("data-date")
        if (dateA < dateB) {
            return 1
        } else if (dateA > dateB) {
            return -1
        } else {
            return 0
        }
    })

    if (oldSelectValue == "date") {
        moviesArray.reverse()
        oldSelectValue = "dateReverse"
    } else {
        oldSelectValue = "date"
    }



    allMovies.innerHTML = ""
    for (let i = 0; i < moviesArray.length; i++) {
        allMovies.appendChild(moviesArray[i])
    }
    forceHideLoader()
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
    imgs.length = 32
    imgsArray.splice(36, imgsArray.length - 1)
    imgsArray.splice(0, 4)
    for (img of imgsArray) {
        const acutalIndex = imgsArray.indexOf(img)
        img = imgs.item(acutalIndex)
        img.addEventListener("load", function() {
            const imagesLenght = imgsArray.length - 1
            if (acutalIndex == (imagesLenght-4)) {
                spinner = document.getElementsByClassName("spinner")[0]
                backgroundSpinner = document.getElementById("loaderBackground")
                spinner.style.opacity = "0"
                spinner.style.display = "none"
                backgroundSpinner.style.display = "none"
            }
        })
    }}
}


window.onload = function() {
    brokenPathDiv = document.getElementsByClassName("brokenPath")[0]
    brokenPath = brokenPathDiv.getAttribute("id")
    brokenPathDiv.parentNode.removeChild(brokenPathDiv)
    playPopup = document.getElementsByClassName("playPopup")[0]
    playPopup.style.display = "none"
    downloadPopup = document.getElementById("downloadMovieButton")
    downloadPopup.style.display = "none"
    popupContent = document.getElementsByClassName("popupContent")[0]
    popupContent.style.height = "86vh"
    getFirstSeries()
}