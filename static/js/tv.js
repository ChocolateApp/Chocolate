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
}