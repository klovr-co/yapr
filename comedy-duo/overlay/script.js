const WS_URL = "ws://localhost:3003";
const MAX_MESSAGES = 5;
const MESSAGE_TTL = 15000;

const ticker = document.getElementById("ticker");

function connect() {
    const ws = new WebSocket(WS_URL);

    ws.onopen = function() {
        console.log("Connected to commentary server");
    };

    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        addMessage(data.bot, data.text);
    };

    ws.onclose = function() {
        console.log("Disconnected, reconnecting in 3s...");
        setTimeout(connect, 3000);
    };

    ws.onerror = function(err) {
        console.error("WebSocket error:", err);
    };
}

function addMessage(botName, text) {
    const el = document.createElement("div");
    const cssClass = botName.toLowerCase();
    el.className = "message " + cssClass;

    const nameEl = document.createElement("div");
    nameEl.className = "bot-name";
    nameEl.textContent = botName;

    const textEl = document.createElement("div");
    textEl.className = "bot-text";
    textEl.textContent = text;

    el.appendChild(nameEl);
    el.appendChild(textEl);
    ticker.appendChild(el);

    while (ticker.children.length > MAX_MESSAGES) {
        ticker.removeChild(ticker.firstChild);
    }

    setTimeout(function() {
        el.classList.add("fading");
        setTimeout(function() { el.remove(); }, 500);
    }, MESSAGE_TTL);
}

connect();
