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
    try {
        trailerVideo.setAttribute("src", "")
        trailerVideo.remove()
    } catch (e) {

    }

})

function setPopup() {
    contents = document.getElementsByClassName("content")
    Array.from(contents).forEach(function(content) {
        content.addEventListener("click", function() {
            popup = document.getElementById("popup")
            popup.style.display = "block"

            document.body.style.overflow = "hidden"

            image = content.children[0]
            movieTitle = image.title;

            fetch("/getMovieData/" + movieTitle).then(function(response) {
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


function getFirstMovies() {
    movies = document.getElementsByClassName("movies")[0]
    routeToUse = movies.getAttribute("id")
    movies.id = "movies"

    fetch("/getRandomMovie").then(function(response) {
        return response.json()
    }).then(function(data) {
        bigBanner = document.getElementsByClassName("bigBanner")[0]
        imageBanner = document.getElementsByClassName("bannerCover")[0]
        genreBanner = document.getElementsByClassName("bannerGenre")[0]
        titleBanner = document.getElementsByClassName("bannerTitle")[0]
        descriptionBanner = document.getElementsByClassName("bannerDescription")[0]
        watchNow = document.getElementsByClassName("watchNowA")[0]

        movie = data

        var slug = movie.slug
        slug = "/movie/" + slug

        cssBigBanner = `background-image: linear-gradient(to bottom, rgb(255 255 255 / 0%), rgb(29 29 29)), url("${movie.banner}")`
        imageBanner.setAttribute('style', cssBigBanner)

        titleBanner.innerHTML = movie.realTitle

        descriptionBanner.innerHTML = movie.description
        descriptionBanner.innerHTML = descriptionBanner.innerHTML.substring(0, 200) + "..."
        descriptionBanner.innerHTML += " <a id='lireLaSuite' href='#'>Lire la suite</a>"

        lireLaSuite = document.getElementById("lireLaSuite")
        lireLaSuite.addEventListener("click", function() {
            descriptionBanner.innerHTML = movie.description
        })

        genreBanner.innerHTML = JSON.parse(movie.genre).join(", ")

        watchNow.setAttribute("href", slug)
    })

    fetch(routeToUse).then(function(response) {
        return response.json()
    }).then(function(data) {
        for (var i = 0; i < data.length; i++) {
            movies = document.getElementsByClassName("movies")[0]
            var movie = data[i]
            adult = movie.adult
            console.log(movie)
            accountType = accountType
            console.log(adult, accountType)
            if ((accountType == "Adult" || accountType == "Admin") || adult == "False") {
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
                cookieValue = getCookie(movie.realTitle)
                if (cookieValue != undefined) {
                    console.log(movie.realTitle, cookieValue)
                    timePopup = document.createElement("div")
                    timePopup.className = "timePopup"
                    timeP = document.createElement("p")
                    timeP.innerHTML = cookieValue
                    timePopup.appendChild(timeP)
                    cover.appendChild(timePopup)
                }

                content.appendChild(image)
                cover.appendChild(content)
                movies.appendChild(cover)
            }
        }

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
        }

        setPopup()
    })
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

function getAccountType() {
    fetch("/getAccountType").then(function(response) {
        return response.json()
    }).then(function(data) {
        console.log(data)
        accountType = data["accountType"]
    }).then(function() {
        getFirstMovies()
    })
}

window.onload = function() {
    brokenPathDiv = document.getElementsByClassName("brokenPath")[0]
    brokenPath = brokenPathDiv.getAttribute("id")
    brokenPathDiv.parentNode.removeChild(brokenPathDiv)
    getAccountType()
}