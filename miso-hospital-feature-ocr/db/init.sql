-- 스키마만 정의. 더미 데이터는 was/seed.js에서 비밀번호 해시/주민번호 암호화 후 삽입한다.
-- (비밀번호 해시, 주민번호 암호화는 SQL이 아닌 애플리케이션 코드에서 수행되어야 하므로
--  평문 INSERT문을 여기 두지 않는다.)
CREATE DATABASE IF NOT EXISTS vulnapp CHARACTER SET utf8mb4;
USE vulnapp;

-- 재실행 시 이전 스키마(예: 취약점 버전의 짧은 rrn 컬럼)가 남아있지 않도록 항상 깨끗하게 초기화.
-- scanned_documents/board_posts가 patients를 외래키로 참조하고, role_permissions가 roles/permissions를
-- 참조하므로 참조하는 쪽을 먼저 삭제.
DROP TABLE IF EXISTS chat_messages;
DROP TABLE IF EXISTS scanned_documents;
DROP TABLE IF EXISTS board_posts;
DROP TABLE IF EXISTS medical_records;
DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS patients;
DROP TABLE IF EXISTS role_permissions;
DROP TABLE IF EXISTS permissions;
DROP TABLE IF EXISTS roles;

CREATE TABLE patients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,       -- [보안 강화] bcrypt 해시 저장 (60자 고정 길이, 평문 저장 금지)
    name VARCHAR(20) NOT NULL,
    rrn VARCHAR(100) NOT NULL,            -- [보안 강화] AES-256-GCM 암호문(base64) 저장. 평문보다 길어져 컬럼 확장
    role ENUM('patient', 'admin') NOT NULL DEFAULT 'patient'  -- RBAC의 역할(role). 이 값 자체가 권한을 뜻하지 않고,
                                                               -- 실제 권한은 아래 roles/permissions/role_permissions로 조회한다.
);

-- RBAC: 역할(Role). patients.role의 값과 이름이 대응된다.
CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(30) UNIQUE NOT NULL
);

-- RBAC: 권한(Permission). "역할 이름"이 아니라 "할 수 있는 행위" 단위로 정의해,
-- 라우트가 특정 역할 문자열이 아니라 권한 이름에만 의존하도록 한다 (routes/*.js의 requirePermission 참고).
CREATE TABLE permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

-- RBAC: 역할 <-> 권한 매핑 (다대다). 이 테이블만 바꾸면 코드 수정 없이 역할별 권한을 조정할 수 있다.
CREATE TABLE role_permissions (
    role_id INT NOT NULL,
    permission_id INT NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES roles(id),
    FOREIGN KEY (permission_id) REFERENCES permissions(id)
);

-- 역할/권한은 비밀번호·주민번호처럼 애플리케이션 코드에서 가공할 값이 없는 순수 참조 데이터이므로
-- (seed.js가 아니라) 스키마와 함께 여기서 직접 시딩한다.
INSERT INTO roles (name) VALUES ('patient'), ('admin');

INSERT INTO permissions (name) VALUES
    ('ocr:scan'),
    ('documents:create'),
    ('documents:view'),
    ('patients:view');

-- admin 역할에게만 문서 스캔(OCR) 관련 4개 권한을 모두 부여. patient 역할은 권한 없음(게시판 기능은 RBAC 대상이 아님).
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'admin' AND p.name IN ('ocr:scan', 'documents:create', 'documents:view', 'patients:view');

-- board.html/view.html이 참조하는 "진료 문의 게시글" 테이블
CREATE TABLE board_posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);

-- 관리자가 admin.html에서 스캔한 문서(OCR 결과)를 환자와 연결해 저장하는 테이블.
-- 조회는 관리자 전용(GET /api/documents) — 환자용 조회 라우트는 만들지 않는다.
CREATE TABLE scanned_documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,            -- 이 스캔 결과가 속한 환자
    scanned_by INT NOT NULL,            -- 스캔을 수행한 관리자(patients.id, role='admin')
    document_type ENUM('prescription', 'diagnosis', 'receipt') NOT NULL,
    extracted_text TEXT,                 -- OCR 원문. 목록 조회 API는 이 컬럼을 응답에 포함하지 않음
    parsed_date DATE NULL,               -- extracted_text에서 정규식으로 뽑아낸 날짜 (best-effort)
    parsed_amount INT NULL,              -- extracted_text에서 정규식으로 뽑아낸 금액(원) (best-effort)
    parsed_fields JSON NULL,             -- "라벨:값" 형태 줄에서 뽑아낸 나머지 필드. 주민등록번호 등 민감 라벨은 제외
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (scanned_by) REFERENCES patients(id)
);

-- 환자-챗봇 상담 기록. "원문은 암호화 보관, 화면 표시는 마스킹" 원칙에 따라
-- content에는 원문을 AES-256-GCM으로 암호화한 값만 저장한다 (평문 저장 금지).
-- 조회 API(GET /api/chat/history)가 복호화 직후 maskPii()를 거쳐 마스킹된 텍스트만 응답한다.
CREATE TABLE chat_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,             -- 이 상담을 나눈 환자 (본인 것만 조회 가능 - board_posts와 동일한 IDOR 방지 패턴)
    sender ENUM('patient', 'bot') NOT NULL,
    content TEXT NOT NULL,                -- AES-256-GCM 암호문(base64)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);

-- 신규: 진료 예약 (챗봇 연동용)
CREATE TABLE appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    appointment_date DATETIME NOT NULL,
    department VARCHAR(50) NOT NULL,
    status ENUM('scheduled', 'completed', 'cancelled') NOT NULL DEFAULT 'scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);

-- 신규: 진료 기록 (챗봇 연동용)
CREATE TABLE medical_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    visit_date DATE NOT NULL,
    diagnosis TEXT NOT NULL,
    prescription TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);
