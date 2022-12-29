function getSeasonData() {
    url = window.location.href
    urlArray = url.split("/")
    id = urlArray[urlArray.length - 1]
    id = id.replace("#", "")
    indexOfEpisode = 1
    https = urlArray[0]
    if (https == "https:") {
        document.head.innerHTML += '<meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests">'
    }
    ndd = urlArray[2]
    baseURI = `${https}//${ndd}`
    finalURI = `${baseURI}/getSeasonData/${id}`
    fetch(finalURI).then(function(response) {
        return response.json()
    }).then(function(data) {
        episodes = data["episodes"]
        episodes = Object.entries(episodes)
        canDownloadDiv = document.getElementById("canDownloadDiv")
        canDownload = canDownloadDiv.getAttribute("data-candownload") == "True"
        let watchNowLanguage = document.getElementById("watchNowLanguage")
        watchNowLanguage = watchNowLanguage.getAttribute("data-value")
        for (let i = 0; i < episodes.length; i++) {
            if (i != 0) {
                episodesDiv = document.getElementsByClassName("episodes")[0]
                let episode = episodes[i][1]
                episodeNumber = episode["episodeNumber"]
                let cover = document.createElement("div")
                cover.className = "coverEpisodes"
                let content = document.createElement("div")
                content.className = "contentEpisodes"
                let image = document.createElement("img")
                image.className = "cover_episode"
                let title = document.createElement("div")
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
                episodeId = episode["episodeId"]

                cookieValue = getCookie(image.title)
                if (cookieValue != undefined) {
                    timePopup = document.createElement("div")
                    timePopup.className = "timePopupSeason"
                    timeP = document.createElement("p")
                    timeP.innerHTML = cookieValue
                    timePopup.appendChild(timeP)
                    cover.appendChild(timePopup)
                }

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
                let serieURL = `/serie/${episodeId}`
                watchNowButton.href = serieURL
                watchNowButton.appendChild(ionIcon)
                watchNowButton.innerHTML += watchNowLanguage
                let episodeButtons = document.createElement("div")
                episodeButtons.className = "episodeButtons"
                episodeButtons.appendChild(watchNowButton)
                if (canDownload) {
                    downloadNowButton = document.createElement("a")
                    downloadNowIcon = document.createElement("ion-icon")
                    downloadNowIcon.setAttribute("name", "download-outline")
                    downloadNowIcon.setAttribute("role", "img")
                    downloadNowIcon.setAttribute("aria-label", "download outline")
                    downloadNowIcon.setAttribute("class", "md hydrated")
                    downloadNowButton.appendChild(downloadNowIcon)
                    downloadNowButton.className = "downloadNowSeason"
                    downloadNowButton.href = `/downloadEpisode/${episodeId}`
                    downloadNowButton.innerHTML += canDownloadDiv.getAttribute("data-value")
                    episodeButtons.appendChild(downloadNowButton)
                }
                episodeText.appendChild(episodeButtons)
                content.appendChild(image)
                content.appendChild(episodeText)
                cover.appendChild(content)
                episodesDiv.appendChild(cover)
                indexOfEpisode += 1
            } else {
                let episode = episodes[i][1]
                episodeId = episode["episodeId"]
                bigBanner = document.getElementsByClassName("bigBanner")[0]
                imageBanner = document.getElementsByClassName("bannerSeasonCover")[0]
                titleBanner = document.getElementsByClassName("bannerTitle")[0]
                descriptionBanner = document.getElementsByClassName("bannerDescription")[0]
                watchNow = document.getElementsByClassName("watchNowA")[0]

                let downloadNowA = document.getElementById("downloadNowA")
                canDownloadDiv = document.getElementById("canDownloadDiv")
                canDownload = canDownloadDiv.getAttribute("data-candownload") == "True"
                if (canDownload) {
                    downloadNowA.setAttribute("href", "/downloadEpisode/" + episodeId)
                } else {
                    downloadNowA.remove()
                }


                let serieURL = `/serie/${episodeId}`
                
                cssBigBanner = `background-image: linear-gradient(to bottom, rgb(255 255 255 / 0%), rgb(29 29 29)), url("${episode.episodeCoverPath}")`
                imageBanner.setAttribute('style', cssBigBanner)

                titleBanner.innerHTML = "EP 1 - " + episode.episodeName
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

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}


window.onload = function() {
    brokenPathDiv = document.getElementsByClassName("brokenPath")[0]
    brokenPath = brokenPathDiv.getAttribute("id")
    brokenPathDiv.parentNode.removeChild(brokenPathDiv)
    getSeasonData()
}