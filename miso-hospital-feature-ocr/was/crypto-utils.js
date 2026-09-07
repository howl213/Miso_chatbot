const crypto = require("crypto");
const config = require("./config");

const ALGORITHM = "aes-256-gcm";

// 주민번호처럼 "나중에 복호화해서 봐야 할 수도 있는" 데이터는 해시가 아닌 대칭키 암호화를 사용.
// config.rrnEncryptionKey는 32바이트(256비트) 키여야 함 (환경변수로 관리, 기본값은 개발용).
// [챗봇 통합] 상담 원문도 동일한 방식(원문 암호화 저장 + 조회시 마스킹)을 쓰므로,
// 이름은 그대로 두고 범용 함수 encryptText/decryptText를 별도로 두어 재사용한다.
function encryptText(plainText) {
  const iv = crypto.randomBytes(12); // GCM은 96비트(12바이트) IV 권장
  const cipher = crypto.createCipheriv(ALGORITHM, config.rrnEncryptionKey, iv);
  const encrypted = Buffer.concat([cipher.update(plainText, "utf8"), cipher.final()]);
  const authTag = cipher.getAuthTag();
  // iv + authTag + 암호문을 하나의 문자열로 합쳐 저장 (복호화 시 다시 분리)
  return Buffer.concat([iv, authTag, encrypted]).toString("base64");
}

function decryptText(storedValue) {
  const raw = Buffer.from(storedValue, "base64");
  const iv = raw.subarray(0, 12);
  const authTag = raw.subarray(12, 28);
  const encrypted = raw.subarray(28);
  const decipher = crypto.createDecipheriv(ALGORITHM, config.rrnEncryptionKey, iv);
  decipher.setAuthTag(authTag);
  return Buffer.concat([decipher.update(encrypted), decipher.final()]).toString("utf8");
}

const encryptRrn = encryptText;
const decryptRrn = decryptText;

// 화면 표시가 필요해질 경우를 대비한 마스킹 함수 (뒷자리 일부만 노출)
// 예: 990101-1234567 -> 990101-1******
function maskRrn(plainRrn) {
  const [front, back] = plainRrn.split("-");
  if (!back) return plainRrn;
  return `${front}-${back[0]}${"*".repeat(back.length - 1)}`;
}

// [챗봇 상담 원문 마스킹] 주민번호/전화번호/이메일 패턴을 찾아 마스킹.
// "원문은 암호화해서 그대로 저장하되, 화면에 보여줄 때만 마스킹"하는 요구사항에 맞춰
// 저장 시점이 아니라 조회 응답 직전(복호화 직후)에 이 함수를 호출한다.
const SSN_PATTERN = /\d{6}-\d{7}/g;
const PHONE_PATTERN = /010-\d{4}-\d{4}/g;
const EMAIL_PATTERN = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;

function maskPii(text) {
  if (typeof text !== "string") return text;
  let masked = text;
  masked = masked.replace(SSN_PATTERN, (m) => `${m.split("-")[0]}-*******`);
  masked = masked.replace(PHONE_PATTERN, (m) => {
    const [a, , c] = m.split("-");
    return `${a}-****-${c}`;
  });
  masked = masked.replace(EMAIL_PATTERN, (m) => {
    const [local, domain] = m.split("@");
    const visible = local.length > 3 ? local.slice(0, 3) : local[0];
    return `${visible}${"*".repeat(local.length - visible.length)}@${domain}`;
  });
  return masked;
}

module.exports = { encryptText, decryptText, encryptRrn, decryptRrn, maskRrn, maskPii };
