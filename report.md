# 병합 작업 리뷰 및 취약점/보안 분석 리포트

본 리포트는 `plan.md`에 명시된 `audit_decorator.py` 통합 작업을 수행하며 파악된 시스템 내 잠재적 취약점과 구조적 보완점, 그리고 지시사항 외에 자체적으로 판단하여 추가로 반영한 내용들을 정리한 것입니다.

## 1. 취약점 및 보완점 (Vulnerabilities & Improvements)

### 1-1. 중복된 감사 로그(Audit Logging) 시스템의 파편화
현재 챗봇 서비스 내부에는 두 가지 서로 다른 감사(Audit) 로그 파이프라인이 병존하고 있습니다.
* **`app.py` 내부의 로깅 로직:** SQLite DB (`chatbot_logs.db`)에 환자의 ID, 암호화된 원문 질의, 마스킹된 질의 및 응답을 저장하며, 암호화 키는 `secret.key` 파일로 별도 관리됩니다.
* **이번에 적용된 `audit_decorator.py`:** 외부 `audit-agent` 엔진을 사용해 비동기적으로 PII 마스킹, 데이터 암호화(KMS 연동, `.env`의 `AUDIT_ENCRYPTION_KEY` 사용), 해시 체인 생성 후 `audit-logs/audit_log.jsonl`에 저장합니다.
* **보완점:** 로그가 분산 저장되고, 암호화 키 역시 파편화되어 있어 유지보수성과 보안성이 떨어집니다. `app.py` 단의 SQLite 로깅을 제거하고(혹은 대체하고) 데코레이터 방식의 일원화된 체계로 통합하는 것이 권장됩니다.

### 1-2. 비동기 로그 저장 방식의 에러 사각지대
* `audit_decorator.py`는 메인 스레드 지연을 막기 위해 `ThreadPoolExecutor(max_workers=2)`를 사용하여 비동기로 저장(Fire-and-forget)합니다. 
* **취약점:** 만약 백그라운드 스레드에서 파일 권한 문제나 디스크 용량 부족 등으로 파일 입출력(I/O) 에러가 발생해도, 메인 애플리케이션은 이를 즉각 인지하지 못하고 로깅 유실이 발생할 수 있습니다.
* **보완점:** 에러 발생 시 지정된 재시도(Retry) 로직이나, Dead Letter Queue(DLQ)를 통한 실패 로그 별도 적재 방식의 도입이 필요합니다.

### 1-3. Rate Limiting 기준점의 잠재적 우회 가능성
* `app.py`에서 `slowapi`를 사용해 분당 20회(`20/minute`)의 Rate Limit을 걸고 있으며, 이 기준점은 `get_remote_address` (IP 기반)를 사용하고 있습니다.
* **취약점:** Node(WAS)나 Nginx 같은 리버스 프록시 서버를 거쳐서 API가 호출되는 구조라면, 챗봇 서비스에 도달하는 IP는 모두 'WAS 서버의 단일 IP'로 고정될 확률이 높습니다. 이 경우, 악성 사용자 1명의 요청 과다로 인해 서비스 전체가 Rate Limit에 걸려 모든 사용자의 접속이 차단(Denial of Service)될 수 있습니다.
* **보완점:** 프록시 계층에서 넘겨주는 `X-Forwarded-For` 헤더를 신뢰하여 IP를 파싱하도록 Rate Limiter의 Key 추출 함수를 변경하거나, 클라이언트 세션 토큰 / `patient_id` 기반으로 Rate Limit을 관리해야 합니다.

### 1-4. 자연어 내 정규표현식 파싱 로직 (Regex) 안정성
* `hospital_agent.py`의 `tool_book_appointment`에서 예약 일시 및 진료과를 추출하기 위해 정규표현식(`re.compile`)을 사용합니다.
* **취약점:** 일반적인 자연어에 대한 정규식 파싱 자체는 유효하나, 악의적 사용자가 아주 길고 복잡한 형태의 특수문자 조합을 보낼 경우 정규식 엔진의 백트래킹 과정에서 과부하가 걸리는 **ReDoS(Regular Expression Denial of Service)** 공격에 노출될 수 있습니다. 

---

## 2. 임의로 수행한 작업 내용 (Unrequested Arbitrary Actions)

`plan.md`의 요구사항은 "필요 시 도구 호출부에 데코레이터 적용 필요"라고만 간략히 작성되어 있었으나, 시스템의 완성도를 높이기 위해 다음과 같은 조치를 임의로 진행했습니다.

1. **도구별 식별자(Action Name) 명시적 할당:**
   * 단순히 `@audit_log("tool_called")` 형태로 묶지 않고, 각 도구의 성격에 맞춰 명시적인 인자값을 부여했습니다.
   * 예: `@audit_log("rag")`, `@audit_log("book_appointment")`, `@audit_log("check_medical_records")` 등.
   * 이를 통해 추후 생성된 JSONL 로그를 분석하거나 파싱할 때, 어떤 비즈니스 로직(RAG 검색인지, 예약 생성인지, 기록 조회인지)이 실행되었는지 한눈에 파악할 수 있도록 조치했습니다.

2. **데코레이터의 모든 Tool 함수 전파:**
   * 특정 메인 라우터(`run_agent`) 한 곳에만 데코레이터를 적용한 것이 아니라, `hospital_agent.py` 내부에서 RAG 엔진, LLM 직접 호출, 예약 및 조회 등 각각의 개별 Tool을 호출하는 함수 선언부 전체에 데코레이터를 일일이 덧씌웠습니다.
   * 이를 통해 특정 도구 내부에서 일어나는 페이로드 입출력 단위를 개별 건으로 모두 감시(Audit)망 안에 넣을 수 있게 되었습니다.
