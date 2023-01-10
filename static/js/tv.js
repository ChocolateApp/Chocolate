function main() {
    url = window.location.href
    library = url.split("/")[4]
    fetch(`/getChannels/${library}`).then(function(response) {
        return response.json();
    }).then(function(channels) {
        for (channel of channels) {
            let channelRealName = encode_utf8(channel.name).replace(/\(.*?\)|\[.*?\]/g, "")
            let channelID = channel.channelID

            let channelDiv = document.createElement("div")
            channelDiv.className = "channelDiv"
            let channelImage = document.createElement("img")
            channelImage.className = "channelImage"
            channelImage.src = channel.logo
            channelImage.setAttribute("loading", "lazy")
            let channelName = document.createElement("p")
            channelName.className = "channelName"
            channelName.innerHTML = channelRealName
            channelDiv.appendChild(channelImage)
            channelDiv.appendChild(channelName)
            channelDiv.addEventListener("click", function() {
                window.location.href = `/tv/${library}/${channelID}`
            })
            document.getElementById("tvChannels").appendChild(channelDiv)
        }
        removeLoader(channels)
    })
}


function removeLoader(data){
    if (data.length <= 1) {
        spinner = document.getElementsByClassName("spinner")[0]
        backgroundSpinner = document.getElementById("loaderBackground")
        spinner.style.opacity = "0"
        spinner.style.display = "none"
        backgroundSpinner.style.display = "none"
    } else {

    const imgs = document.images
    const imgsArray = Array.prototype.slice.call(document.images)
    imgs.length = 32
    imgsArray.splice(36, imgsArray.length - 1)
    imgsArray.splice(0, 4)
    for (img of imgsArray) {
        const acutalIndex = imgsArray.indexOf(img)
        img = imgs.item(acutalIndex)
        img.addEventListener("load", function() {
            const imagesLenght = imgsArray.length - 1
            //console.log(`${acutalIndex}/${imagesLenght-4}`)
            if (acutalIndex == (imagesLenght-4)) {
                spinner = document.getElementsByClassName("spinner")[0]
                backgroundSpinner = document.getElementById("loaderBackground")
                spinner.style.opacity = "0"
                spinner.style.display = "none"
                backgroundSpinner.style.display = "none"
            }
        })
    }}
}

function encode_utf8(s) {
    try {
        return decodeURIComponent(escape(s));
    } catch (e) {
        return s;
    }
  }

main()