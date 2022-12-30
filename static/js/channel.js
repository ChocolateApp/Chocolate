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
            'chromecastButton',
            'airPlayButton',
            'pictureInPictureToggle',
            'fullscreenToggle',
        ],
    }, 
}

//add the quality selector
var player = videojs('movie', options);