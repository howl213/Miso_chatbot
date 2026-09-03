const express = require("express");
const cors = require("cors");
const session = require("express-session");
const config = require("./config");
const authRoutes = require("./routes/auth");
const boardRoutes = require("./routes/board");

const app = express();

// frontend가 다른 포트(정적 서버)에서 뜨므로 CORS + 세션 쿠키 전달 허용 필요
app.use(cors({ origin: true, credentials: true }));
app.use(express.json());
app.use(
  session({
    secret: config.sessionSecret,
    resave: false,
    saveUninitialized: false,
    cookie: { httpOnly: true }, // secure: true는 HTTPS 환경에서만 추가 (로컬 실습이라 생략)
  })
);

app.use("/api", authRoutes);
app.use("/api/board", boardRoutes);

app.listen(config.port, () => {
  console.log(`WAS listening on http://localhost:${config.port}`);
});
