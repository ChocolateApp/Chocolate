backButton = document.getElementById("backButton")
backButton.addEventListener("click", function() {
    window.history.back();
});

//remove the emulatorJS ad
//wait for the ad to load
setTimeout(function() {
    ad = document.getElementsByClassName("ejs--3a16fd9a56aec8059089709cbb16f4")[0]
    ad.remove()
}, 1000)