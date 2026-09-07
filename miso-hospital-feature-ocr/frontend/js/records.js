const recordList = document.getElementById('recordList');
const emptyState = document.getElementById('emptyState');
const recordDetail = document.getElementById('recordDetail');

function formatDate(isoOrDateString) {
    if (!isoOrDateString) return '-';
    const d = new Date(isoOrDateString);
    const pad = (n) => String(n).padStart(2, '0');
    return `${d.getFullYear()}.${pad(d.getMonth() + 1)}.${pad(d.getDate())}`;
}

function formatAmount(amount) {
    return amount == null ? '-' : `${amount.toLocaleString()}원`;
}

// [XSS 방지] 다른 화면과 동일하게 textContent로만 대입
function renderRow(doc) {
    const tr = document.createElement('tr');
    tr.style.cursor = 'pointer';

    const typeTd = document.createElement('td');
    typeTd.textContent = doc.document_type_label;
    const dateTd = document.createElement('td');
    dateTd.textContent = formatDate(doc.parsed_date || doc.created_at);
    const amountTd = document.createElement('td');
    amountTd.textContent = formatAmount(doc.parsed_amount);

    tr.append(typeTd, dateTd, amountTd);
    tr.addEventListener('click', () => loadDetail(doc.id));
    recordList.appendChild(tr);
}

async function loadList() {
    const res = await fetch(`${WAS_BASE}/api/documents/mine`, { credentials: 'include' });
    if (!res.ok) {
        window.location.href = 'login.html';
        return;
    }
    const docs = await res.json();
    recordList.innerHTML = '';
    emptyState.hidden = docs.length > 0;
    docs.forEach(renderRow);
}

// [보안] URL이 아니라 클릭한 문서의 id로만 요청 - 서버가 세션의 patientId로 소유권을 다시 검증하므로
// 설령 id를 조작해도 타인의 기록은 절대 내려오지 않는다 (was/routes/documents.js GET /mine/:id 참고).
async function loadDetail(id) {
    const res = await fetch(`${WAS_BASE}/api/documents/mine/${id}`, { credentials: 'include' });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        showToast(err.message || '조회에 실패했습니다.');
        return;
    }
    const doc = await res.json();

    recordDetail.innerHTML = '';
    const title = document.createElement('h3');
    title.textContent = `${doc.document_type_label} - ${formatDate(doc.parsed_date || doc.created_at)}`;
    const body = document.createElement('pre');
    body.className = 'record-detail__text';
    body.textContent = doc.extracted_text; // OCR 원문. pre + textContent라 줄바꿈은 유지되면서 스크립트 실행은 안 됨

    recordDetail.append(title, body);
    recordDetail.hidden = false;
    recordDetail.scrollIntoView({ behavior: 'smooth' });
}

async function loadUserInfo() {
    const res = await fetch(`${WAS_BASE}/api/me`, { credentials: 'include' });
    if (!res.ok) {
        window.location.href = 'login.html';
        return;
    }
    const me = await res.json();
    setCsrfToken(me.csrfToken);
    document.getElementById('userInfo').textContent = `${me.name}님`;
}

document.getElementById('logoutBtn').addEventListener('click', async () => {
    await fetch(`${WAS_BASE}/api/logout`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'X-CSRF-Token': getCsrfToken() },
    });
    window.location.href = 'index.html';
});

loadUserInfo();
loadList();
