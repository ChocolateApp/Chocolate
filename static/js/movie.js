// when the page is loaded, get the movie duration from the cookie if it exists
window.onload = function() {
    var video = document.getElementById("movie_html5_api")
    let lastPush = ""

    video.addEventListener("timeupdate", function() {
        actualDuration = video.currentTime
        var path = window.location.pathname
        var cookie = `movieDuration=${actualDuration}; path=${path}`
        document.cookie = cookie
        videoDuration = Math.round(video.duration)
        roundedDuration = Math.round(actualDuration)
        percent = roundedDuration / videoDuration * 100
        title = document.title.split(" | ")[0]
        durationInHHMMSS = new Date(roundedDuration * 1000).toISOString().substr(11, 8);
        secondDurationInHHMMSS = new Date(videoDuration * 1000).toISOString().substr(11, 8);
        if (percent >= 90) {
            cookie = `${title}=Finished; path=/`
        } else {
            cookie = `${title}=${durationInHHMMSS}; path=/`
        }
        document.cookie = cookie
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
}