# 담당 파트 (howl213)

이 프로젝트는 팀 프로젝트입니다. 처음 파트를 나눌 때 **챗봇(본인, howl213) / 프론트엔드(Sunjung Hwang) / 백엔드·WAS(yysong1249)**로 역할을 정했습니다. `chatbot-service`(챗봇 로직·보안)는 본인이 처음 설계·구현했고, 이후 팀원들이 함께 개선/보완했습니다.

## chatbot-service (본인 담당, 원 설계자)

`chatbot` 브랜치 기준 본인 커밋 21건을 주제별로 정리하면 다음과 같습니다.

**회원가입 실명 인증 (모의 PASS)**
- `human.csv` 기반 실명+주민번호 매칭 모의 인증(`mock_pass.py`) 및 `/internal/verify-identity` 엔드포인트 구현, WAS 회원가입 라우트에 fail-closed 게이트 연동

**예약 확인·취소 2단계 플로우**
- 자유 텍스트 파싱 즉시 예약 대신 확인/취소 단계 추가(백엔드+프론트 Yes/No 버튼), 예약 정원 체크 로직 추가(TDD)

**PII 마스킹**
- 이름 마스킹 오탐/누락 수정, `mask_pii()` 회귀 테스트 pytest 이관, 본인 등록 이름 우선 마스킹(`own_name`) 기능 추가

**프롬프트 인젝션 탐지 / Rate Limit**
- 시스템 프롬프트 유출 탐지 로직 수정, 환자별 rate limit key 분리(기존 WAS IP 공용 문제 수정) — TDD로 진행

**감사 로그 (Audit Log)**
- 내부 URL/API 키 노출 탐지 + 감사 로그 마스킹 통합, 해시체인 영속화, `risk_level` 기반 위험도 분류·리포트 도구, `risk_level=high` Discord 실시간 알림, 감사 기준 문서화

**기타 유지보수**
- 챗봇 LLM/임베딩 모델 설정 수정, origin/main 병합 후 구문 오류 수정, `audit-agent` → `audit_agent` 디렉토리명 리팩터(하이픈이 파이썬 패키지명으로 쓰일 수 없어 pytest 수집이 깨지던 문제 해결), README 작업 기록·용어 설명서 작성

## was (팀원 yysong1249 담당 — 본인은 챗봇 연동을 위한 최소 수정만)

- 챗봇이 예약 확인/취소·회원가입 인증을 처리하려면 WAS 쪽 호출 지점도 함께 바뀌어야 해서, `was/routes/chat.js`(예약 확인/취소 라우트, 병합 후 구문 오류 수정), `was/routes/auth.js`(실명인증 연동) 등 백엔드 담당(yysong1249) 영역을 7건 함께 수정
- 나머지 세션/CSRF/OCR/관리자 기능/IP 차단 등은 전부 yysong1249 담당

## audit-agent / audit_agent (감사 로그 인프라, 팀 공동)

- 초기 골격(yysong1249) 위에 본인이 내부 URL/API 키 노출 탐지, 해시체인 영속화, risk_level 리포트 도구, Discord 실시간 알림 추가
- 팀원들이 위험도 분류 체계·대시보드·페이지네이션·PII 스캔 재설계를 지속 개선

## frontend (팀원 Sunjung Hwang 담당 — 본인 1건)

- 예약 확인 UI(Yes/No 버튼)는 프론트엔드 담당(Sunjung Hwang) 영역이지만, 챗봇 응답 구조 변경과 맞물려 1건 직접 구현(`frontend/js/chat-common.js` 등)

## 팀원의 chatbot-service 개선 사례 (반대 방향 협업)

- 팀원들이 본인이 만든 챗봇 코드를 이어받아 개선한 사례: PII 마스킹 오탐 추가 완화(성씨 화이트리스트, spaCy NER 모델 교체), `get_patient_name()` DB 연결 누수 수정, 진료과 매칭 버그 수정, 감사 요약 캐시/레이스 컨디션 수정 등
