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
    childs = document.getElementsByClassName("season")
    while (childs.length > 0) {
        childs[0].remove()
    }
    var similar = document.getElementsByClassName("containerSimilar")[0]
    similar.style.gridTemplateColumns = "repeat(0, 1fr)"
    containerSeasons = document.getElementsByClassName("containerSeasons")[0]
    while (containerSeasons.firstChild) {
        containerSeasons.removeChild(containerSeasons.firstChild)
    }

    var trailerVideo = document.getElementById("trailerVideo")
    trailerVideo.setAttribute("src", "")
    trailerVideo.remove()
})

function getSeasonData() {
    url = window.location.href
    urlArray = url.split("/")
    seasonName = urlArray[urlArray.length - 2]
    id = urlArray[urlArray.length - 1]
    id = id.substring(1)
    indexOfEpisode = 1
    https = urlArray[0]
    if (https == "https:") {
        document.head.innerHTML += '<meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests">'
    }
    ndd = urlArray[2]
    baseURI = `${https}//${ndd}`
    finalURI = `${baseURI}/getSeasonData/${seasonName}/S${id}`
    console.log(ndd, baseURI, finalURI)
    fetch(finalURI).then(function(response) {
        return response.json()
    }).then(function(data) {
        episodes = data["episodes"]
        episodes = Object.entries(episodes)
        for (var i = 0; i < episodes.length; i++) {
            if (i != 0) {
                episodesDiv = document.getElementsByClassName("episodes")[0]
                var episode = episodes[i][1]
                episodeNumber = episode["episodeNumber"]
                var cover = document.createElement("div")
                cover.className = "coverEpisodes"
                var content = document.createElement("div")
                content.className = "contentEpisodes"
                var image = document.createElement("img")
                image.className = "cover_episode"
                var title = document.createElement("div")
                title.className = "title"
                title.innerHTML = episode["episodeName"]

                episodeTitle = document.createElement("h1")
                episodeTitle.className = "episodeTitle"
                episodeTitle.innerHTML = "EP" + episode["episodeNumber"] + " - " + episode["episodeName"]

                episodeDescription = document.createElement("p")
                episodeDescription.className = "episodeDescription"
                episodeDescription.innerHTML = episode["episodeDescription"]

                image.src = episode["episodeCoverPath"]
                image.title = episode["episodeName"]
                image.alt = episode["episodeName"]
                episodeId = indexOfEpisode

                episodeText = document.createElement("div")
                episodeText.className = "episodeText"
                episodeText.appendChild(episodeTitle)
                episodeText.appendChild(episodeDescription)

                watchNowButton = document.createElement("a")
                watchNowButton.className = "watchNowSeason md hydrated"

                ionIcon = document.createElement("ion-icon")
                ionIcon.className = "watchNow"
                ionIcon.setAttribute("name", "play")
                ionIcon.setAttribute("role", "img")
                ionIcon.setAttribute("aria-label", "play outline")
                let serieURL = `/serie/${seasonName}/${id}/${episodeId}`
                watchNowButton.href = serieURL
                watchNowButton.appendChild(ionIcon)
                watchNowButton.innerHTML = watchNowButton.innerHTML + "Watch Now"
                content.appendChild(image)
                content.appendChild(episodeText)
                content.appendChild(watchNowButton)
                cover.appendChild(content)
                episodesDiv.appendChild(cover)
                indexOfEpisode += 1
            } else {
                bigBanner = document.getElementsByClassName("bigBanner")[0]
                imageBanner = document.getElementsByClassName("bannerSeasonCover")[0]
                titleBanner = document.getElementsByClassName("bannerTitle")[0]
                descriptionBanner = document.getElementsByClassName("bannerDescription")[0]
                watchNow = document.getElementsByClassName("watchNowA")[0]

                var episode = episodes[i][1]
                episodeId = indexOfEpisode

                let serieURL = `/serie/${seasonName}/${id}/${episodeId}`

                imageBanner.setAttribute("alt", episode.episodeName)
                imageBanner.setAttribute("title", episode.episodeName)
                imageBanner.setAttribute("src", episode.episodeCoverPath)

                titleBanner.innerHTML = episode.episodeName
                description = episode.episodeDescription
                descriptionBanner.innerHTML = description
                descriptionBanner.innerHTML = descriptionBanner.innerHTML.substring(0, 200) + "..."
                descriptionBanner.innerHTML += " <a id='lireLaSuite' href='#'>Lire la suite</a>"

                lireLaSuite = document.getElementById("lireLaSuite")
                lireLaSuite.addEventListener("click", function() {
                    descriptionBanner.innerHTML = description
                })

                watchNow.setAttribute("href", serieURL)
                indexOfEpisode += 1
            }
        }
    })
}

window.onload = function() {
    brokenPathDiv = document.getElementsByClassName("brokenPath")[0]
    brokenPath = brokenPathDiv.getAttribute("id")
    brokenPathDiv.parentNode.removeChild(brokenPathDiv)
    getSeasonData()
}