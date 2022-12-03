const createObjectFromString = (str) => {
	return eval(`(function () { return ${str}; })()`);
}

window.onload = function() {
    let lastPush = ""
    let options;

    var path = window.location.pathname
    movieID = window.location.href.split("/")[4]

    if (navigator.userAgent.match(/Android/i) || navigator.userAgent.match(/webOS/i) || navigator.userAgent.match(/iPhone/i) || navigator.userAgent.match(/iPad/i) || navigator.userAgent.match(/iPod/i) || navigator.userAgent.match(/BlackBerry/i) || navigator.userAgent.match(/Windows Phone/i)) {
        //remove the first 2 sources
        document.getElementById("movie").removeChild(document.getElementById("movie").firstChild);
        document.getElementById("movie").removeChild(document.getElementById("movie").firstChild);
        document.getElementById("movie").removeChild(document.getElementById("movie").firstChild);
        document.getElementById("movie").removeChild(document.getElementById("movie").firstChild);
    }


    options = {
        controls: true,
        preload: 'none',
        techOrder: ['chromecast', 'html5'],
        html5: {
            vhs: {
                overrideNative: !videojs.browser.IS_SAFARI,
            },
        },
        'html5': {
            nativeTextTracks: false
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
               'pictureInPictureToggle',
               'fullscreenToggle',
            ],
        },
        
    }

    //add the quality selector
    var player = videojs('movie', options);
    
    player.hlsQualitySelector({
        displayCurrentQuality: true,
        placementIndex : 7
    });
    player.chromecast();
    player.controls(true);

    var video = document.getElementById("movie_html5_api")
    video.addEventListener("timeupdate", function() {
        let href = window.location.href
        movieID = href.split("/")[4]
        fetch(`/setVuesTimeCode/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            //set the form
            body: JSON.stringify({
                movieID: movieID,
                timeCode: video.currentTime
            })
        })
    })


    let username = ""
    fetch("/whoami").then(function(response) {
        return response.json()
    }).then(function(data) {
        username = data.name
    }).then(function() {
        fetch(`/getMovieData/${movieID}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        }).then(response => response.json())
        .then(data => {
            vues = data.vues
            //vues is a string representing an array convert it to an array
            vues = createObjectFromString(vues)
            if (vues[username] !== undefined){
                timeCode = vues[username]
                timeCode = parseInt(timeCode)
                var popup = document.getElementById("popup")
                popup.style.display = "block"

                buttonYes = document.getElementById("buttonYes")
                buttonYes.addEventListener("click", function() {
                    popup.style.display = "none"
                    document.body.style.overflow = "auto"
                    video = document.getElementById("movie_html5_api")
                    video.play()
                    video.currentTime = timeCode

                })

                buttonNo = document.getElementById("buttonNo")
                buttonNo.addEventListener("click", function() {
                    popup.style.display = "none"
                    document.body.style.overflow = "auto"
                    video = document.getElementById("movie_html5_api")
                    video.play()
                })
            }
        })
    })

    var path = window.location.pathname
    var slug = path.split("/")
    slug = slug[2]

}