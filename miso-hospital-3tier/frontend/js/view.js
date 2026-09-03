const WAS_BASE = "http://localhost:3000";

// URL의 patient_id를 그대로 서버에 요청.
// [취약점] 서버(routes/board.js GET /:patientId)가 세션의 patientId와 비교하지 않으므로
// 로그인만 되어 있으면 이 값을 바꿔 타인의 진료 문의를 그대로 받아올 수 있다 (IDOR).
const params = new URLSearchParams(window.location.search);
const patientId = params.get('patient_id');
const detail = document.getElementById('postDetail');

async function loadPost() {
    const res = await fetch(`${WAS_BASE}/api/board/${patientId}`, { credentials: 'include' });
    if (!res.ok) {
        detail.innerHTML = '<p>로그인이 필요합니다.</p>';
        return;
    }
    const posts = await res.json();
    if (posts.length === 0) {
        detail.innerHTML = `<p>해당 문의를 찾을 수 없습니다. (patient_id=${patientId})</p>`;
        return;
    }
    detail.innerHTML = posts.map(p => `
        <p style="color:#888; font-size:14px;">작성자: ${p.name} (patient_id=${p.patient_id})</p>
        <h3>${p.title}</h3>
        <p>${p.content}</p>
    `).join('<hr>');
}

loadPost();
