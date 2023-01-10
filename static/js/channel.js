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

//when the player is ready, show the progress bar and set the visibility to hidden
player.ready(function() {
    progressBar = document.querySelector('.vjs-progress-control');
    progressBar.style.visibility = 'hidden';
    progressBar.style.display = 'block';

});