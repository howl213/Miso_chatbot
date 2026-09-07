const chatPanel = document.getElementById('chatPanel');
const chatMessages = document.getElementById('chatMessages');

document.getElementById('chatToggleBtn').addEventListener('click', async () => {
    const isOpen = chatPanel.style.display !== 'none';
    chatPanel.style.display = isOpen ? 'none' : 'flex';
    if (!isOpen && chatMessages.childElementCount === 0) {
        await loadHistory();
    }
});

// [XSS 방지] 다른 화면들과 동일하게 textContent로만 대입 - 챗봇 응답이나 사용자 입력에
// 스크립트가 섞여 있어도 실행되지 않고 텍스트 그대로만 표시된다.
function appendMessage(sender, text) {
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble chat-bubble--${sender}`;
    bubble.textContent = text;
    chatMessages.appendChild(bubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function loadHistory() {
    const res = await fetch(`${WAS_BASE}/api/chat/history`, { credentials: 'include' });
    if (!res.ok) return;
    const messages = await res.json();
    // 서버가 이미 마스킹까지 마친 텍스트를 보내주므로 그대로 렌더링하면 됨
    messages.forEach((m) => appendMessage(m.sender, m.content));
}

document.getElementById('chatForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    if (!message) return;

    appendMessage('patient', message); // 화면엔 사용자가 방금 입력한 원문 그대로 보여줌(마스킹은 저장/재조회 시 적용)
    input.value = '';

    const res = await fetch(`${WAS_BASE}/api/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': getCsrfToken(),
        },
        credentials: 'include',
        body: JSON.stringify({ message }),
    });

    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        appendMessage('bot', err.message || '메시지 전송에 실패했습니다.');
        return;
    }
    const data = await res.json();
    appendMessage('bot', data.answer);
});
