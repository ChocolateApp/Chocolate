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
                'chromecastButton',
                'airPlayButton',
                'pictureInPictureToggle',
                'fullscreenToggle',
            ],
        },
    }
    var player = videojs('movie', options);
    player.hlsQualitySelector({
        displayCurrentQuality: true,
        placementIndex: 7
    });

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
    })
    var path = window.location.pathname
    var slug = path.split("/")
    slug = slug[2]
};