const express = require("express");
const pool = require("../db");

const router = express.Router();

// 로그인한 본인의 문의 목록만 반환 (board.html의 "나의 문의 내역" 영역용)
router.get("/", async (req, res) => {
  if (!req.session.patientId) {
    return res.status(401).json({ message: "로그인이 필요합니다." });
  }
  const [rows] = await pool.query(
    "SELECT id, patient_id, title FROM board_posts WHERE patient_id = ?",
    [req.session.patientId]
  );
  res.json(rows);
});

// 새 문의 등록 (제목/내용은 클라이언트에서 이스케이프 없이 그대로 저장 -> board.js가 innerHTML로 그릴 때 XSS 발생)
router.post("/", async (req, res) => {
  if (!req.session.patientId) {
    return res.status(401).json({ message: "로그인이 필요합니다." });
  }
  const { title, content } = req.body;
  const [result] = await pool.query(
    "INSERT INTO board_posts (patient_id, title, content) VALUES (?, ?, ?)",
    [req.session.patientId, title, content]
  );
  res.json({ id: result.insertId, patient_id: req.session.patientId, title, content });
});

// ⚠ 취약점(IDOR): URL의 patient_id로 조회하면서 세션의 patientId와 일치하는지 검증하지 않음
// -> 로그인만 되어 있으면(누구든) patient_id를 바꿔 타인의 진료 문의를 그대로 열람 가능
router.get("/:patientId", async (req, res) => {
  if (!req.session.patientId) {
    return res.status(401).json({ message: "로그인이 필요합니다." });
  }
  const [rows] = await pool.query(
    `SELECT bp.id, bp.patient_id, bp.title, bp.content, p.name
     FROM board_posts bp JOIN patients p ON p.id = bp.patient_id
     WHERE bp.patient_id = ?`,
    [req.params.patientId]
  );
  res.json(rows);
});

module.exports = router;
