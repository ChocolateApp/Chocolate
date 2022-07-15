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
        var movieYear = image.getAttribute("year");
        var movieGenre = image.getAttribute("genre");
        var movieDuration = image.getAttribute("duration");
        var movieCast = image.getAttribute("cast"); // a list of lists of strings

        movieCast = movieCast.replaceAll("'", '"')


        movieCast = JSON.parse(movieCast)

        // order by the default order of the cast

        movieCast.sort(function(a, b) {
            var nameA = a[0].toUpperCase(); // ignore upper and lowercase
            var nameB = b[0].toUpperCase(); // ignore upper and lowercase
            if (nameA < nameB) {
                return -1;
            }
            if (nameA > nameB) {
                return 1;
            }
            // names must be equal
            return 0;
        })


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

        var yearPopup = document.getElementsByClassName("yearPopup")[0]
        yearPopup.innerHTML = `Date : ${movieYear}`;

        var genrePopup = document.getElementsByClassName("genrePopup")[0]
        var genreList = movieGenre.substring(1, movieGenre.length - 1)
        genreList = genreList.replace(/'/g, "")
        genreList = genreList.split(",")
        var genreString = ""
        for (var i = 0; i < genreList.length; i++) {
            genreString += genreList[i]
            if (i != genreList.length - 1) {
                genreString += ", "
            }
        }
        genrePopup.innerHTML = `Genre : ${genreString}`;

        var durationPopup = document.getElementsByClassName("durationPopup")[0]
        durationPopup.innerHTML = `Durée : ${movieDuration}`;




        castPopup = document.getElementById("castPopup")
            // delete all the old cast divs
        castDivs = castPopup.getElementsByClassName("castMember")
        while (castDivs.length > 0) {
            castPopup.removeChild(castDivs[0])
        }

        // add the new cast divs
        for (var i = 0; i < movieCast.length; i++) {
            castMember = document.createElement("div")
            castMember.className = "castMember"
            castImage = document.createElement("img")
            castImage.className = "castImage"
            castImage.setAttribute("src", movieCast[i][2])
            castImage.setAttribute("alt", movieCast[i][0])
            castImage.setAttribute("title", movieCast[i][0])
            castMember.appendChild(castImage)
            castName = document.createElement("p")
            castName.className = "castName"
            castName.innerHTML = movieCast[i][0]
            castMember.appendChild(castName)
            castCharacter = document.createElement("p")
            castCharacter.className = "castCharacter"
            castCharacter.innerHTML = movieCast[i][1]
            castMember.appendChild(castCharacter)
            castPopup.appendChild(castMember)
        }

        var playButton = document.getElementsByClassName("playPopup")[0]
        playButton.setAttribute("href", movieUrl);
    })
}