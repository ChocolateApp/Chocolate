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

    var trailerVideo = document.getElementById("trailerVideo")
    trailerVideo.setAttribute("src", "")
    trailerVideo.remove()

})

function setPopup() {
    covers = document.getElementsByClassName("cover")
    for (var i = 0; i < covers.length; i++) {
        covers[i].addEventListener("click", function() {

            popup = document.getElementById("popup")
            popup.style.display = "block"

            document.body.style.overflow = "hidden"

            var image = this.children[0].children[0]
            var serieTitle = image.getAttribute("title");

            fetch("/getSerieData/" + serieTitle).then(function(response) {
                return response.json()
            }).then(function(data) {
                var serieTitle = data.name

                var serieCast = data.cast
                var serieDescription = data.description
                var serieDuration = data.duration
                var serieGenre = data.genre
                var serieNote = data.note
                var seriePoster = data.serieCoverPath
                var serieUrl = data.slug
                serieUrl = "/serie/" + serieUrl
                var serieYear = data.date
                var serieTrailer = data.bandeAnnonce
                var serieSimilar = data.similarSeries
                containerSimilar = document.getElementsByClassName("containerSimilar")[0]

                if (serieSimilar.length === 0) {
                    containerSimilar.style.display = "none"

                } else {
                    containerSimilar.style.display = "inline-grid"
                }

                for (var i = 0; i < serieSimilar.length; i++) {
                    if (i < 4) {
                        var serie = serieSimilar[i]

                        fetch("/getSerieData/" + serie).then(function(response) {
                            return response.json()
                        }).then(function(data) {
                            var serie = data
                            console.log(serie)
                            imageUrl = serie.serieCoverPath
                            serieName = serie.name
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
                        })
                    }
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
                var genreList = serieGenre
                var genreString = ""
                for (var i = 0; i < genreList.length; i++) {
                    genreString += genreList[i]
                    if (i != genreList.length - 1) {
                        genreString += ", "
                    }
                }
                genrePopup.innerHTML = `Genre : ${genreString}`;

                var durationPopup = document.getElementsByClassName("durationPopup")[0]
                durationPopup.innerHTML = `Durée : ${serieDuration}`;
                console.log(serieCast)
                for (var i = 0; i < serieCast.length; i++) {
                    castMember = document.createElement("div")
                    castMember.className = "castMember"
                    castImage = document.createElement("img")
                    castImage.className = "castImage"
                    castImageUrl = serieCast[i]["profile_path"]
                    castImageUrl = "https://image.tmdb.org/t/p/original" + castImageUrl
                    castRealName = serieCast[i]["name"]
                    castCharacterName = serieCast[i]["character"]
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
}


function getFirstSeries() {
    series = document.getElementsByClassName("series")[0]
    routeToUse = series.getAttribute("id")
    console.log(routeToUse)
    series.id = "series"

    fetch(routeToUse).then(function(response) {
        return response.json()
    }).then(function(data) {
        data = Object.entries(data)
        console.log(data)
        for (serie of data) {
            index = data.indexOf(serie)
            if (index === 0) {
                bigBanner = document.getElementsByClassName("bigBanner")[0]
                imageBanner = document.getElementsByClassName("bannerCover")[0]
                genreBanner = document.getElementsByClassName("bannerGenre")[0]
                titleBanner = document.getElementsByClassName("bannerTitle")[0]
                descriptionBanner = document.getElementsByClassName("bannerDescription")[0]
                watchNow = document.getElementsByClassName("watchNowA")[0]

                console.log(serie)

                var serieUrl = serie[1]['seasons'][0]['episodes']['1']['slug']

                serieUrl = "/serie" + serieUrl

                imageBanner.setAttribute("src", serie[1]['banniere'])
                if (imageBanner.src == "https://image.tmdb.org/t/p/originalNone") {
                    imageBanner.src = brokenPath
                }
                imageBanner.setAttribute("alt", serie[0])
                imageBanner.setAttribute("title", serie[0])

                titleBanner.innerHTML = serie[0]
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
                for (var i = 0; i < genres.length; i++) {
                    genreBanner.innerHTML += genres[i]
                    if (i != genres.length - 1) {
                        genreBanner.innerHTML += ", "
                    }
                }

                watchNow.setAttribute("href", serieUrl)
            } else {
                console.log(serie)
                series = document.getElementsByClassName("series")[0]
                var cover = document.createElement("div")
                cover.className = "cover"
                cover.style.marginBottom = "2vh"
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

                content.appendChild(image)
                cover.appendChild(content)
                series.appendChild(cover)
            }
        }

        setPopup()
    })
}

window.onload = function() {
    brokenPathDiv = document.getElementsByClassName("brokenPath")[0]
    brokenPath = brokenPathDiv.getAttribute("id")
    brokenPathDiv.parentNode.removeChild(brokenPathDiv)
    getFirstSeries()
}