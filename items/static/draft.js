    function updateEmoji(name, emoji){
        var url="https://infinitecraft.up.railway.app/api/addEmoji"
        fetch(url, {
            method: 'POST',
            body: JSON.stringify({
                name: name,
                emoji: emoji
            }),
            mode: 'no-cors'
        })
    }

    function upperLevelText(element){
        child = element.firstChild,
        texts = [];

        while (child) {
            if (child.nodeType == 3) {
                texts.push(child.data);
            }
            child = child.nextSibling;
        }
        return texts.join("");
    }

document.querySelectorAll(".item").forEach((itemDiv) => {
    var emojiSpan = itemDiv.querySelector(".item-emoji")
    updateEmoji(upperLevelText(itemDiv).trim(), emojiSpan.innerText.trim())
})

document.querySelectorAll(".instance").forEach((itemDiv) => {
    var emojiSpan = itemDiv.querySelector(".instance-emoji")
    var textSpan = itemDiv.querySelector(".instance-text")
    updateEmoji(textSpan.innerText.trim(),emojiSpan.innerText.trim().replace(String.fromCharCode(65039),""))
})

navigator.clipboard.writeText(document.querySelector(".instance-text").innerText)