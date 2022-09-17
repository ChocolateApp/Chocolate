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
    https = urlArray[0].replace('http:', 'https:')
    ndd = urlArray[2]
    baseURI = `${https}//${ndd}`
    finalURI = `${baseURI}/getSeasonData/${seasonName}/S${id}`
    console.log(finalURI)
    fetch(finalURI).then(function(response) {
        return response.json()
    }).then(function(data) {
        episodes = data["episodes"]
        episodes = Object.entries(episodes)
        for (var i = 0; i < episodes.length; i++) {
            episodesDiv = document.getElementsByClassName("episodes")[0]
            var episode = episodes[i][1]
            episodeNumber = episode["episodeNumber"]
            var cover = document.createElement("div")
            cover.className = "cover"
            var content = document.createElement("div")
            content.className = "content"
            var image = document.createElement("img")
            image.className = "cover_episode"
            var title = document.createElement("div")
            title.className = "title"
            title.innerHTML = episode["episodeName"]

            image.src = episode["episodeCoverPath"]
            image.title = episode["episodeName"]
            image.alt = episode["episodeName"]
            episodeId = indexOfEpisode
            let newURL = `/serie/${seasonName}/${id}/${episodeId}`
            cover.addEventListener("click", function() {
                window.location = newURL
            })

            content.appendChild(image)
            cover.appendChild(content)
            episodesDiv.appendChild(cover)
            indexOfEpisode += 1
        }
    })
}

window.onload = function() {
    brokenPathDiv = document.getElementsByClassName("brokenPath")[0]
    brokenPath = brokenPathDiv.getAttribute("id")
    brokenPathDiv.parentNode.removeChild(brokenPathDiv)
    getSeasonData()
}