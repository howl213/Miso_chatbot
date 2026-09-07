const express = require("express");
const pool = require("../db");
const config = require("../config");
const { encryptText, decryptText, maskPii } = require("../crypto-utils");
const { verifyCsrfToken } = require("../middleware/csrf");

const router = express.Router();

// 환자 본인의 상담 이력만 조회 (board.js의 IDOR 방지 패턴과 동일: 세션의 patientId만 사용).
// 이 기능은 RBAC 대상이 아니라 로그인한 모든 환자 계정에 공통으로 열려있음 (requirePermission 미적용).
router.get("/history", async (req, res) => {
  if (!req.session.patientId) {
    return res.status(401).json({ message: "로그인이 필요합니다." });
  }
  const [rows] = await pool.query(
    "SELECT id, sender, content, created_at FROM chat_messages WHERE patient_id = ? ORDER BY id",
    [req.session.patientId]
  );
  const masked = rows.map((row) => ({
    id: row.id,
    sender: row.sender,
    content: maskPii(decryptText(row.content)),
    created_at: row.created_at,
  }));
  res.json(masked);
});

// 환자가 메시지를 보내면: (1) 원문 암호화 저장 (2) 챗봇 서비스에 질문 전달해 답변 생성
// (3) 답변도 암호화 저장 (4) 화면에는 마스킹된 텍스트만 응답
router.post("/", verifyCsrfToken, async (req, res) => {
  if (!req.session.patientId) {
    return res.status(401).json({ message: "로그인이 필요합니다." });
  }
  const { message } = req.body;
  if (!message || typeof message !== "string" || message.length > 1000) {
    return res.status(400).json({ message: "메시지를 확인해주세요." });
  }

  await pool.query(
    "INSERT INTO chat_messages (patient_id, sender, content) VALUES (?, 'patient', ?)",
    [req.session.patientId, encryptText(message)]
  );

  let answer;
  try {
    // Python 챗봇 서비스에는 질문 원문만 잠깐 전달될 뿐, 저장 책임은 지지 않는다
    // (민감정보가 이 마이크로서비스나 그 로그에 남지 않도록 저장은 항상 이쪽에서만 수행).
    const upstream = await fetch(`${config.chatbotServiceUrl}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: message, patient_id: req.session.patientId }),
    });
    if (!upstream.ok) throw new Error(`챗봇 서비스 응답 오류: ${upstream.status}`);
    const data = await upstream.json();
    answer = data.answer;
  } catch (err) {
    console.error("[chat] 챗봇 서비스 호출 실패:", err.message);
    answer = "죄송합니다, 지금은 상담 서비스에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.";
  }

  await pool.query(
    "INSERT INTO chat_messages (patient_id, sender, content) VALUES (?, 'bot', ?)",
    [req.session.patientId, encryptText(answer)]
  );

  res.json({ answer: maskPii(answer) });
});

module.exports = router;
