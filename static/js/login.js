const allUsers = document.getElementsByClassName("user")
allusers = Array.from(allUsers)

crossPopup = document.getElementById("crossPopup")
crossPopup.addEventListener("click", function() {
    loginForm = document.getElementsByClassName("loginForm")[0]
    loginForm.style.display = "none"
    document.getElementsByClassName("nameInputForm")[0].value = ""
});
allUsersDiv = document.getElementsByClassName("allUsers")[0]
lenAllUsers = allUsersDiv.children.length
if (lenAllUsers < 3){ 
    allUsersDiv.classList.add(`${"a"*lenAllUsers}Users`)
} else {
    allUsersDiv.classList.add(`maxUsers`)
}
for (user of allusers) {
    user.addEventListener("click", function() {
        document.getElementsByClassName("nameInputForm")[0].value = this.id
        loginForm = document.getElementsByClassName("loginForm")[0]
        accountType = this.getAttribute("type")
        passwordEmpty = this.getAttribute("data-passwordEmpty")
        print
        if (["Admin", "Adult", "Teen"].includes(accountType) && passwordEmpty == "no") {
            loginForm.style.display = "block"
        } else {
            loginForm = document.getElementsByClassName("loginForm")[0]
            document.getElementById("password").value = ""
            loginForm.submit()
        }
    });

    let userImage = user.children[0]
        //fetch user image and check if 404
    fetch(userImage.src).then(function(response) {
        if (response.status == 404) {
            userImage.src = "/static/img/defaultUserProfilePic.png"
        }
    })
}

header = document.getElementsByTagName("header")[0];
searchForm
header.remove()
searchForm = document.getElementById("searchForm");
searchForm.remove()
settings = document.getElementsByClassName("settings")[0]
settings.remove()