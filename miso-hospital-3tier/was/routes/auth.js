const express = require("express");
const pool = require("../db");

const router = express.Router();

router.post("/login", async (req, res) => {
  const { username, password } = req.body;

  // ⚠ 취약점: 입력값을 그대로 문자열 결합 -> SQL Injection
  // 예: username에 " ' OR '1'='1' -- " 입력 시 인증 우회 가능
  const query = `SELECT * FROM patients WHERE username = '${username}' AND password = '${password}'`;

  const [rows] = await pool.query(query);
  const patient = rows[0];

  if (!patient) {
    return res.status(401).json({ success: false, message: "로그인 실패" });
  }

  // 로그인한 본인 id만 세션에 저장 (그런데도 아래 board.js의 상세조회는 이 값을 확인하지 않음)
  req.session.patientId = patient.id;
  req.session.patientName = patient.name;

  res.json({ success: true, patient: { id: patient.id, name: patient.name } });
});

router.post("/signup", async (req, res) => {
  const { username, password, name, rrn } = req.body;

  // ⚠ 취약점: 아이디 중복 여부를 응답 메시지로 그대로 알려줌 -> User Enumeration
  // (공격자가 이 메시지로 어떤 아이디가 이미 가입되어 있는지 하나씩 확인 가능)
  const [existing] = await pool.query(
    "SELECT id FROM patients WHERE username = ?",
    [username]
  );
  if (existing.length > 0) {
    return res.status(409).json({ success: false, message: "이미 존재하는 아이디입니다." });
  }

  // ⚠ 취약점: 비밀번호를 해시 없이 평문 그대로 저장, 입력값 검증(길이/형식)도 없음
  const [result] = await pool.query(
    "INSERT INTO patients (username, password, name, rrn) VALUES (?, ?, ?, ?)",
    [username, password, name, rrn]
  );

  res.json({ success: true, id: result.insertId });
});

module.exports = router;
