function main() {
    url = window.location.href
    library = url.split("/")[4]
    fetch(`/getChannels/${library}`).then(function(response) {
        return response.json();
    }).then(function(json) {
        channels = json
        for (channel of channels) {
            let channelRealName = encode_utf8(channel.name).replace(/\(.*?\)|\[.*?\]/g, "")
            let channelID = channel.channelID

            let channelDiv = document.createElement("div")
            channelDiv.className = "channelDiv"
            let channelImage = document.createElement("img")
            channelImage.className = "channelImage"
            channelImage.src = channel.logo
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
    })
}

function encode_utf8(s) {
    try {
        return decodeURIComponent(escape(s));
    } catch (e) {
        return s;
    }
  }

main()