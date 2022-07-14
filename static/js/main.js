function goToHome() {
    document.location.pathname = "/home"
}


var closePopup = document.getElementById("crossPopup")
closePopup.addEventListener("click", function() {
    popup = document.getElementById("popup")
    popup.style.display = "none"

    document.body.style.overflow = "auto"
})

covers = document.getElementsByClassName("cover")
for (var i = 0; i < covers.length; i++) {
    covers[i].addEventListener("click", function() {

        popup = document.getElementById("popup")
        popup.style.display = "block"

        document.body.style.overflow = "hidden"

        var image = this.children[0].children[0]
        var movieUrl = image.getAttribute("movieUrl");
        var movieTitle = image.getAttribute("title");
        var moviePoster = image.getAttribute("src");
        var movieDescription = image.getAttribute("description");
        var movieNote = image.getAttribute("note");


        var imagePopup = document.getElementsByClassName("coverPopup")[0]
        imagePopup.setAttribute("src", moviePoster);
        imagePopup.setAttribute("alt", movieTitle);
        imagePopup.setAttribute("title", movieTitle);

        var titlePopup = document.getElementsByClassName("titlePopup")[0]
        titlePopup.innerHTML = movieTitle;

        var descriptionPopup = document.getElementsByClassName("descriptionPopup")[0]
        descriptionPopup.innerHTML = movieDescription;

        var notePopup = document.getElementsByClassName("notePopup")[0]
        notePopup.innerHTML = `Note : ${movieNote}/10`;

        var playButton = document.getElementsByClassName("playPopup")[0]
        playButton.setAttribute("href", movieUrl);
    })
}