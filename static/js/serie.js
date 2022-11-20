window.onload = function() {
    let lastPush = ""
    let options;

    options = {
        controls: true,
        preload: 'none',
        techOrder: ['chromecast', 'html5'],
        html5: {
            vhs: {
                overrideNative: !videojs.browser.IS_SAFARI,
            },
        },
        controlBar: {
            children: [
               'playToggle',
               'volumePanel',
               'currentTimeDisplay',
               'progressControl',
               'remainingTimeDisplay',
               'captionsButton',
               'audioTrackButton',
               'qualitySelector',
               'pictureInPictureToggle',
               'fullscreenToggle',
            ],
        },
    }
    var player = videojs('movie', options);
    player.chromecast();
    player.controls(true);

    var video = document.getElementById("movie_html5_api")
    let introStart = 0
    let introEnd = 0
    href = window.location.href
    hrefPARTS = href.split("/")
    episodeID = hrefPARTS[hrefPARTS.length - 1]
    fetch(`/getThisEpisodeData/${episodeID}`).then(function(response) {
        return response.json()
    }).then(function(data) {
        introStart = data.introStart
        introEnd = data.introEnd
    })

    var introSkipButton = document.createElement("button")
    introSkipButton.id = "introSkipButton"
    introSkipButton.className = "introSkipButton"
    introSkipButton.style.display = "none"
    introSkipButton.innerHTML = "Skip Intro"
    frontOfTheVideo = document.getElementById("movie")
    frontOfTheVideo.appendChild(introSkipButton)
    video.addEventListener("timeupdate", function() {
        actualDuration = video.currentTime
        var path = window.location.pathname
        var cookie = `movieDuration=${actualDuration}; path=${path}`
        document.cookie = cookie
        if (video.duration == NaN) {
            video.duration = 1
        }
        videoDuration = Math.round(video.duration)
        roundedDuration = Math.round(actualDuration)
        percent = roundedDuration / videoDuration * 100
        title = document.title.split(" | ")[0]
        durationInHHMMSS = new Date(roundedDuration * 1000).toISOString().substr(11, 8);
        try {
            secondDurationInHHMMSS = new Date(videoDuration * 1000).toISOString().substr(11, 8);
        } catch (RangeError) {

        }
        if (percent >= 90) {
            cookie = `${title}=Finished; path=/`
        } else {
            cookie = `${title}=${durationInHHMMSS}; path=/`
        }
        document.cookie = cookie

        if (actualDuration >= introStart - 4 && actualDuration < introEnd - 2) {
            console.log(actualDuration, introStart - 4)
            introSkipButton = document.getElementById("introSkipButton")
            introSkipButton.style.display = "flex"
        } else {
            introSkipButton = document.getElementById("introSkipButton")
            introSkipButton.style.display = "none"
        }
        introSkipButton.addEventListener("click", function() {
            video.currentTime = introEnd - 2
        })

        /*
        if (durationInHHMMSS != lastPush) {
            fetch(`/sendDiscordPresence/${title}/${durationInHHMMSS}/${secondDurationInHHMMSS}`)
            console.log(`/sendDiscordPresence/${title}/${durationInHHMMSS}/${secondDurationInHHMMSS}`)
            lastPush = durationInHHMMSS
        }
        */
    })
    var path = window.location.pathname

    var allCookies = document.cookie
    var cookies = allCookies.split(";")
    for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i]
        var cookieName = cookie.split("=")[0]
        if (cookieName == "movieDuration") {
            theMovieCookie = cookie
            var theCookieDuration = theMovieCookie.split("=")[1]
            if (theCookieDuration != "0") {
                var popup = document.getElementById("popup")
                popup.style.display = "block"

                buttonYes = document.getElementById("buttonYes")
                buttonYes.addEventListener("click", function() {
                    popup.style.display = "none"
                    document.body.style.overflow = "auto"
                    video = document.getElementById("movie_html5_api")
                    video.play()
                    video.currentTime = theCookieDuration
                })

                buttonNo = document.getElementById("buttonNo")
                buttonNo.addEventListener("click", function() {
                    popup.style.display = "none"
                    document.body.style.overflow = "auto"
                    document.cookie = `movieDuration=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=${path}`
                })
            }
        }
    }

    var path = window.location.pathname
    var slug = path.split("/")
    slug = slug[2]
};