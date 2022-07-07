function goToHome() {
    document.location.pathname = "/home"
}

var player = document.getElementById("videoPlayer");


function playPauseVid() {
    button = document.getElementById("playPauseButton");
    console.log(button.className)
    if (button.className == "zmdi zmdi-pause zmdi-hc-lg") {
        player.pause();
        button.className = "zmdi zmdi-play zmdi-hc-lg"
    } else if (button.className == "zmdi zmdi-play zmdi-hc-lg") {
        player.play()
        button.className = "zmdi zmdi-pause zmdi-hc-lg"
    }
}

function changeVol() {
    player.volume = document.getElementById("changeVol").value / 100;
    audioIcon = document.getElementById("audioSize")
    console.log(player.volume)
    let icon;
    if (player.volume >= 0.5) {
        icon = "zmdi zmdi-volume-up zmdi-hc-lg"
    } else if (player.volume > 0) {
        icon = "zmdi zmdi-volume-down zmdi-hc-lg"
    } else if (player.volume == 0) {
        icon = "zmdi zmdi-volume-mute zmdi-hc-lg"
    }
    audioIcon.className = icon
}