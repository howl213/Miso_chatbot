const WAS_BASE = "http://localhost:3000";

document.getElementById('signupForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const name = document.getElementById('name').value;
    const rrn = document.getElementById('rrn').value;

    // [취약점 포인트] 클라이언트 단 검증 없음 - 빈 값, 형식이 이상한 주민번호 등 그대로 서버로 전송
    const res = await fetch(`${WAS_BASE}/api/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, name, rrn }),
    });
    const data = await res.json();

    if (data.success) {
        alert('가입이 완료되었습니다. 로그인해주세요.');
        window.location.href = 'index.html';
    } else {
        // [취약점] 서버가 "이미 존재하는 아이디"라고 그대로 알려줌 -> User Enumeration
        alert(data.message || '가입 실패');
    }
});
