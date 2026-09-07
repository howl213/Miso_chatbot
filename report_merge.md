# 미소병원 챗봇 모듈 업데이트 및 통합 가이드 (Report for Merge)

## 1. 개요
본 문서는 미소병원 웹 서비스(`miso-hospital-feature-ocr`)에 통합될 **챗봇 모듈(Chatbot API)의 고도화 업데이트 내역**을 타 팀(Frontend / WAS / DB 담당자)에게 공유하기 위해 작성되었습니다. 

챗봇 담당 파트에서는 환자의 진료 예약, 예약 확인, 진료 기록 조회 등의 신규 기능을 챗봇 에이전트에 추가하였으며, 이를 전체 시스템에 온전히 연동하기 위해 타 팀에서 진행해 주셔야 할 **코드 병합 및 수정 요청 사항**을 상세히 정리하였습니다.

---

## 2. 챗봇 파트 작업 내역 (주요 변경 사항)
챗봇 모듈 내부적으로 업데이트되어 전달드리는 사항은 다음과 같습니다.

### 2.1 LLM 및 임베딩 모델 단일화 (Gemini)
- 당초 DeepSeek API 도입을 검토하였으나 텍스트 임베딩 모델의 부재 이슈가 있어, RAG 검색(문서 임베딩) 및 응답 생성(LLM) 모델 모두 기존처럼 **Gemini API**를 사용하도록 확정/원복하였습니다.
- 챗봇 서비스 구동을 위한 `.env` 파일 설정 시, `GEMINI_API_KEY` 환경변수를 통합하여 사용하시면 됩니다.

### 2.2 챗봇 에이전트(Agent) 신규 기능(Tool) 확장
환자의 질문 의도를 챗봇이 파악하여 DB와 직접 상호작용하는 3가지 신규 기능이 추가되었습니다.
1. **진료 예약 도구:** 환자의 예약 요청 시 DB(`appointments`)에 예약을 생성합니다.
2. **예약 조회 도구:** 환자의 최신 3건의 예약 내역(`appointments`)을 DB에서 조회하여 답변합니다.
3. **진료 기록 조회 도구:** 환자의 진료 기록 유무(`medical_records`)를 확인하고, 기록이 존재하면 홈페이지의 진료기록 페이지(`/records.html`) 링크를 챗봇이 반환합니다.

### 2.3 DB 직접 연결 로직 (`tools_db.py` 신설)
- 챗봇 내부에서 위 3가지 신규 기능을 처리하기 위해, Python 챗봇(FastAPI) 단에서 MySQL(`vulnapp`)로 직접 커넥션을 맺고 쿼리를 수행하는 로직을 추가했습니다. (`pymysql` 패키지 사용)
- 환경변수 `DB_HOST`, `DB_USER`, `DB_PASS`, `DB_NAME`을 읽어와 WAS와 동일한 DB에 직접 접근하도록 구현되었습니다.

---

## 3. 타 팀 협조 및 추가 작업 요청 사항 (Action Required)
챗봇 팀의 업데이트 사항이 정상 동작하기 위해서는 **프론트엔드, 백엔드(WAS), DB 파트의 코드 병합 및 수정이 필수적**입니다. 전달받으신 챗봇 코드를 병합하실 때 아래 사항들을 최신 코드에 반드시 반영해 주시기 바랍니다.

### 3.1 WAS 서버 챗봇 API 호출부 수정 (Backend/WAS 팀)
챗봇이 특정 환자의 예약 및 기록 조회를 수행하려면 **'현재 질문하는 환자가 누구인지'** 식별할 수 있어야 합니다.
- **수정 대상:** WAS 라우터 코드 (예: `was/routes/chat.js` 내부의 챗봇 호출부)
- **변경 내용:** WAS에서 Python 챗봇 서비스로 HTTP POST 요청을 보낼 때, 기존의 `{ "question": message }` 외에 현재 로그인된 사용자 세션 ID를 **`patient_id`** 필드로 추가하여 넘겨주도록 수정 부탁드립니다.
  ```javascript
  // WAS측 챗봇 fetch 로직 수정 예시
  const upstream = await fetch(`${config.chatbotServiceUrl}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ 
      question: message, 
      patient_id: req.session.patientId // <- 해당 필드가 반드시 추가되어야 챗봇이 환자를 식별합니다.
    }),
  });
  ```

### 3.2 DB 스키마 업데이트 요청 (DB/Backend 팀)
챗봇이 예약 및 진료 기록 데이터를 다룰 수 있도록 `vulnapp` 데이터베이스(초기화 스크립트 `init.sql` 등)에 다음 2개의 테이블을 신설해 주셔야 합니다. (두 테이블 모두 기존 `patients` 테이블의 `id`를 외래키로 참조합니다)
1. **`appointments` 테이블:** 환자 ID(`patient_id`), 예약 일시, 과목, 예약 상태 등
2. **`medical_records` 테이블:** 환자 ID(`patient_id`), 방문 일자, 진단 내용, 처방 내용 등
- *※ 협의된 바와 같이 기존 `scanned_documents` 테이블과는 별개로 동작하는 챗봇/기록 전용 테이블입니다.*

### 3.3 프론트엔드 연동 확인 (Frontend 팀)
- 챗봇 응답 중 "진료 기록 조회"를 수행할 경우, 화면에 `[진료 기록 바로가기](/records.html)` 형태의 마크다운 링크 문법이 텍스트로 전달됩니다.
- 챗봇 UI 화면(Chat Widget) 렌더링 시 해당 텍스트가 정상적으로 클릭 가능한 HTML 앵커 태그(`<a>`)로 파싱되어 페이지 이동이 잘 이루어지는지 테스트를 부탁드립니다.

### 3.4 구동 환경(Dependencies) 및 설정 확인
- 챗봇 병합을 진행하시면서 챗봇 서비스 구동 환경 파일(`requirements.txt`)에 `pymysql` 의존성이 누락되지 않고 잘 설치되는지 확인 바랍니다.
- 챗봇 서버(`start.sh` 등) 구동 시, WAS와 동일한 MySQL 접속 정보(`DB_HOST`, `DB_USER` 등) 환경 변수가 정상 주입되는지 확인이 필요합니다.
