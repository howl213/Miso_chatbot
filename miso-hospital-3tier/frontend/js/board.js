const WAS_BASE = "http://localhost:3000";
const inquiryList = document.getElementById('inquiryList');

// [취약점 포인트] XSS 방어 누락
// 서버가 돌려준 제목을 이스케이프 없이 innerHTML로 그대로 삽입.
// title에 <script> 태그가 저장되어 있었다면 여기서 그대로 실행됨.
function renderPost(post) {
    const li = document.createElement('li');
    li.innerHTML = `<a href="view.html?patient_id=${post.patient_id}">${post.title}</a>`;
    inquiryList.appendChild(li);
}

async function loadMyInquiries() {
    const res = await fetch(`${WAS_BASE}/api/board`, { credentials: 'include' });
    if (!res.ok) {
        window.location.href = 'index.html'; // 로그인 안 된 상태면 로그인 페이지로
        return;
    }
    const posts = await res.json();
    inquiryList.innerHTML = '';
    posts.forEach(renderPost);
}

document.getElementById('inquiryForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const title = document.getElementById('title').value;
    const content = document.getElementById('content').value;

    const res = await fetch(`${WAS_BASE}/api/board`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ title, content }),
    });
    const newPost = await res.json();

    renderPost(newPost); // 서버 응답을 그대로 innerHTML에 꽂음 -> XSS 페이로드 저장형(Stored)으로 재현

    document.getElementById('title').value = '';
    document.getElementById('content').value = '';
});

loadMyInquiries();
