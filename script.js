document.addEventListener("DOMContentLoaded", function() {
    const chatBox = document.getElementById("chat-box");
    const userInput = document.getElementById("user-input");
    const sendButton = document.getElementById("send-button");

    function appendMessage(sender, message) {
        const messageElement = document.createElement("div");
        messageElement.classList.add("message", sender);
        messageElement.innerHTML = message; // Use innerHTML for links
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    sendButton.addEventListener("click", function() {
        const message = userInput.value;
        if (message.trim() === "") return;
        appendMessage("user", message);
        userInput.value = "";

        fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            appendMessage("bot", data.response);
            if (data.recommendations) {
                data.recommendations.forEach(song => {
                    appendMessage("bot", `Song: ${song.song_name} by ${song.artist}`);
                    if (song.spotify_image) {
                        const img = document.createElement("img");
                        img.src = song.spotify_image;
                        img.alt = song.song_name;
                        img.style.width = "100px";
                        chatBox.appendChild(img);
                    }
                    appendMessage("bot", `<a href="${song.spotify_link}" target="_blank">Listen on Spotify</a>`);
                });
            }
        });
    });
});
