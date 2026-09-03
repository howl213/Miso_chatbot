// DB 접속 정보를 환경변수로 받는다. 기본값은 로컬 개발용.
module.exports = {
  dbHost: process.env.DB_HOST || "localhost",
  dbPort: Number(process.env.DB_PORT || 3306),
  dbUser: process.env.DB_USER || "vulnuser",
  dbPassword: process.env.DB_PASSWORD || "vulnpass", // 실습용 - 실제 서비스에 절대 사용 금지
  dbName: process.env.DB_NAME || "vulnapp",

  // 세션 시크릿도 고정값 사용 (실습 환경이라 auth.js의 "약한 세션 관리" 데모에 재활용)
  sessionSecret: process.env.SESSION_SECRET || "insecure-fixed-secret-key",

  port: Number(process.env.PORT || 3000),
};
