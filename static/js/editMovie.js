let movieFindedDivs = document.getElementsByClassName("movieFinded")
let originalMovieID = window.location.href.split("/")[4]
let realName = document.getElementById("realName").innerHTML
let libraryName = document.getElementById("library").innerHTML
for (let i = 0; i < movieFindedDivs.length; i++) {
    let movieFindedDiv = movieFindedDivs[i]
    movieFindedDiv.addEventListener("click", function() {
        let movieID = movieFindedDiv.id
        let form = document.createElement("form");
        form.method = "POST";
        form.action = `/editMovie/${realName}/${libraryName}`;
        let input = document.createElement("input");
        input.type = "hidden";
        input.name = "newMovieID";
        input.value = `${movieID}`;
        form.appendChild(input);
        document.body.appendChild(form);
        form.submit();
    })
}

let customIDButton = document.getElementById("customMovieButton")
customIDButton.addEventListener("click", function() {
    let movieID = document.getElementById("movieID").value
    let form = document.createElement("form");
    form.method = "POST";
    form.action = `/editMovie/${realName}/${libraryName}`;
    let input = document.createElement("input");
    input.type = "hidden";
    input.name = "newMovieID";
    input.value = `${movieID}`;
    form.appendChild(input);
    document.body.appendChild(form);
    form.submit();
})