// chatbot.js
document.addEventListener("DOMContentLoaded", () => {
    // Inject HTML
    const chatbotContainer = document.createElement("div");
    chatbotContainer.id = "chatbot-container";
    chatbotContainer.innerHTML = `
        <button id="chatbot-btn">💬</button>
        <div id="chatbot-window">
            <div id="chatbot-header">
                <span>미소 챗봇</span>
                <button id="chatbot-close">✕</button>
            </div>
            <div id="chatbot-messages">
                <div class="chat-msg bot">안녕하세요! 미소병원 챗봇입니다. 진료시간, 위치, 증상 상담 등을 도와드립니다.</div>
            </div>
            <div id="chatbot-input-area">
                <input type="text" id="chatbot-input" placeholder="질문을 입력하세요...">
                <button id="chatbot-send">➤</button>
            </div>
        </div>
    `;
    document.body.appendChild(chatbotContainer);

    const btn = document.getElementById("chatbot-btn");
    const chatWindow = document.getElementById("chatbot-window");
    const closeBtn = document.getElementById("chatbot-close");
    const sendBtn = document.getElementById("chatbot-send");
    const input = document.getElementById("chatbot-input");
    const messages = document.getElementById("chatbot-messages");

    // Toggle Chat Window
    btn.addEventListener("click", () => {
        chatWindow.style.display = chatWindow.style.display === "flex" ? "none" : "flex";
    });

    closeBtn.addEventListener("click", () => {
        chatWindow.style.display = "none";
    });

    // Send Message
    const sendMessage = async () => {
        const text = input.value.trim();
        if (!text) return;

        // 1. Add user message to UI
        addMessage(text, "user");
        input.value = "";

        // 2. Call API
        try {
            // NOTE: assuming Chatbot Python API runs on port 8000
            const response = await fetch("http://localhost:8000/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ question: text })
            });

            if (!response.ok) {
                if (response.status === 429) {
                    const errData = await response.json();
                    addMessage("호출 한도를 초과했습니다: " + errData.error, "bot");
                    return;
                }
                throw new Error("API Network error");
            }

            const data = await response.json();
            addMessage(data.answer, "bot");
            
            // Optionally, we could display how the bot masked it (for demo purposes)
            // console.log("Masked request:", data.masked_question);

        } catch (err) {
            console.error(err);
            addMessage("죄송합니다. 챗봇 서버와 연결할 수 없습니다.", "bot");
        }
    };

    sendBtn.addEventListener("click", sendMessage);
    input.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendMessage();
    });

    function addMessage(text, sender) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `chat-msg ${sender}`;
        msgDiv.textContent = text;
        messages.appendChild(msgDiv);
        messages.scrollTop = messages.scrollHeight;
    }
});
