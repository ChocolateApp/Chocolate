profilePictureImg = document.getElementById("profilePictureImg")
editProfilePicture = document.getElementsByClassName("editProfilePicture")[0]
profilePictureInput = document.getElementById("profilePicture")
profilePictureImg.addEventListener("mouseover", function() {
    editProfilePicture.style.display = "block"
})
editProfilePicture.addEventListener("mouseover", function() {
    editProfilePicture.style.display = "block"
})
editProfilePicture.addEventListener("mouseout", function() {
    editProfilePicture.style.display = "none"
})
profilePictureImg.addEventListener("mouseout", function() {
    editProfilePicture.style.display = "none"
})

editProfilePicture.addEventListener("click", function() {
    profilePictureInput.click()
})

profilePictureInput.addEventListener("change", function() {
    var file = document.getElementById("profilePicture").files[0];
    getBase64(file)
})


function getBase64(file) {
    var reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = function() {
        resultat = reader.result;
        profilePictureImg = document.getElementById("profilePictureImg")
        profilePictureImg.setAttribute('src', resultat)
    };
    reader.onerror = function(error) {
        console.log('Error: ', error);
    };
}