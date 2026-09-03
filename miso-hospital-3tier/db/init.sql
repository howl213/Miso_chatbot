-- 취약점 실습용 더미 데이터. 실존 인물과 무관.
CREATE DATABASE IF NOT EXISTS vulnapp CHARACTER SET utf8mb4;
USE vulnapp;

CREATE TABLE patients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,       -- 평문 저장 (취약점: 해시 미적용)
    name VARCHAR(20) NOT NULL,
    rrn VARCHAR(14) NOT NULL              -- 형식: 990101-1234567
);

-- board.html/view.html이 참조하는 "진료 문의 게시글" 테이블
CREATE TABLE board_posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,               -- IDOR 지점: 조회 시 로그인 사용자와 일치 여부 검증 안 함
    title VARCHAR(200) NOT NULL,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);

INSERT INTO patients (username, password, name, rrn) VALUES
('patient1', 'pass1234', '김환자', '990101-1234567'),
('patient2', 'pw5678',   '이몽룡', '850520-2345678'),
('patient3', 'qwerty1',  '성춘향', '920315-2456789');

INSERT INTO board_posts (patient_id, title, content) VALUES
(1, '어제부터 열이 나고 기침이 심해요', '체온은 38.2도이고 목도 아픕니다. 언제 방문하면 될까요?'),
(2, '허리 디스크 재발한 것 같습니다', '예전에 수술받은 부위가 다시 저리고 아픕니다. MRI 재검사가 필요할까요?'),
(3, '우울증 약 복용 중 부작용 문의', '처방받은 약을 먹은 뒤로 어지럼증이 심합니다. 용량을 줄여도 될까요?');
