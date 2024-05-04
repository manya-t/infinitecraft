
function updateEmoji(name, emoji){
    var url="http://127.0.0.1:8000/api/addEmoji"
    fetch(url, {
        method: 'POST',
        body: JSON.stringify({
            name: name,
            emoji: emoji
        }),
        mode: 'no-cors'
    })
}

document.querySelectorAll(".item").forEach((itemDiv) => {
    var emojiSpan = itemDiv.querySelector(".item-emoji")
    itemDiv.removeChild(emojiSpan)
    updateEmoji(itemDiv.innerText.trim(), emojiSpan.innerText.trim())
})