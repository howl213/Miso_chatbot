const WAS_BASE = "http://localhost:3000";

document.getElementById('loginForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const userid = document.getElementById('userid').value;
    const userpw = document.getElementById('password').value;

    // [취약점 포인트] 클라이언트 단 입력값 검증 없이 그대로 서버로 전송
    // ' OR '1'='1' -- 같은 SQLi 페이로드도 필터링 없이 /api/login으로 전달됨
    const res = await fetch(`${WAS_BASE}/api/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include', // 세션 쿠키를 주고받기 위해 필요
        body: JSON.stringify({ username: userid, password: userpw }),
    });
    const data = await res.json();

    if (data.success) {
        window.location.href = 'board.html';
    } else {
        alert(data.message || '로그인 실패');
    }
});
