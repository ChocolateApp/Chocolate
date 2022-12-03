const createObjectFromString = (str) => {
	return eval(`(function () { return ${str}; })()`);
}

window.onload = function() {
    let lastPush = ""
    let options;

    var path = window.location.pathname
    movieID = window.location.href.split("/")[4]


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
               'pictureInPictureToggle',
               'fullscreenToggle',
            ],
        },
        
    }

    //add the quality selector
    var player = videojs('movie', options);
    
    player.hlsQualitySelector({
        displayCurrentQuality: true,
        placementIndex : 6
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
                    video.currentTime = timeCode

                })

                buttonNo = document.getElementById("buttonNo")
                buttonNo.addEventListener("click", function() {
                    popup.style.display = "none"
                    document.body.style.overflow = "auto"
                    video = document.getElementById("movie_html5_api")
                })
            }
        })
    })

    var path = window.location.pathname
    var slug = path.split("/")
    slug = slug[2]

}