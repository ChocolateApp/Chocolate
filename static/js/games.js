function getAllGames() {
    var title = document.getElementsByTagName("title")[0].innerHTML;
    console = title.split(" | ")[0]
    fetch(`/getGames/${console}`).then(function(response) {
        return response.json();
    }).then(function(json) {
        var games = json;
        for (game of games) {
            var gameDiv = document.createElement("div");
            gameDiv.className = "gameDiv";
            var gameImageDiv = document.createElement("div");
            gameImageDiv.className = "gameImageDiv";
            var gameImage = document.createElement("img");
            gameImage.className = "gameImage";
            gameImage.src = game.cover;
            var gameName = document.createElement("p");
            gameName.className = "gameName";
            gameName.innerHTML = game.title;
            gameImageDiv.appendChild(gameImage);
            gameDiv.appendChild(gameImageDiv);
            gameDiv.appendChild(gameName);
            let realTitle = game.realTitle;
            gameDiv.addEventListener("click", function() {
                window.location.href = `/game/${console}/${realTitle}`;
            });
            var gameList = document.getElementById("gameList");
            gameList.appendChild(gameDiv);
        };
    });
}

backButton = document.getElementById("backButton")
backButton.addEventListener("click", function() {
    window.history.back();
});

function hideLoader() {
    spinner = document.getElementById("spinner")
    backgroundSpinner = document.getElementById("loaderBackground")
    spinner.style.visibility = "hidden"
    backgroundSpinner.style.display = "none"
}

getAllGames()
hideLoader()