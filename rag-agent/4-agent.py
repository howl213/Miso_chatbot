# 4-agent.py
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Callable

from audit_decorator import audit_log

BASE_DIR = Path(__file__).resolve().parent


def load_module(module_name: str, file_name: str):
    """번호가 붙은 예제 파일을 경로로 직접 로드한다."""
    module_path = BASE_DIR / file_name
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"모듈을 불러올 수 없습니다: {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# 이 예제 폴더는 단계별 파일명 앞에 번호가 붙어 있어서
# 일반적인 import 문으로는 바로 불러오기 어렵다.
# 그래서 경로를 직접 지정해 1~3단계 모듈을 읽어온다.
DOCUMENTS = load_module("documents_demo", "1-documents.py")
sys.modules.setdefault("documents", DOCUMENTS)
EMBEDDINGS = load_module("embeddings_demo", "2-embeddings.py")
sys.modules.setdefault("embeddings", EMBEDDINGS)
LLM = load_module("llm_demo", "3-1-llm.py")
sys.modules.setdefault("llm", LLM)
RAG = load_module("rag_demo", "3-2-rag.py")


def tool_list_documents() -> str:
    """에이전트가 문서 목록을 확인할 때 쓰는 도구."""
    docs = DOCUMENTS.load_documents()
    lines = ["[도구] 문서 목록 조회"]
    for doc in docs:
        lines.append(f"- {doc.doc_id}: {doc.text}")
    return "\n".join(lines)


def tool_document_summary() -> str:
    """에이전트가 현재 보유한 문서 구성을 짧게 요약할 때 쓰는 도구."""
    docs = DOCUMENTS.load_documents()
    lines = ["[도구] 문서 구성 요약"]
    lines.append(f"- 문서 수: {len(docs)}")
    lines.append(f"- 문서 id: {', '.join(doc.doc_id for doc in docs)}")
    return "\n".join(lines)


def tool_rag(question: str) -> str:
    """에이전트가 RAG 검색 + 답변 생성을 요청할 때 쓰는 도구."""
    # run_rag() 는 내부에서 문서 로드 → 임베딩 → 검색 → 답변 생성을 모두 수행한다.
    return RAG.run_rag(question, top_k=2)


def tool_direct_answer(question: str) -> str:
    """문서 검색 없이 일반 답변만 생성한다."""
    return LLM.generate_direct_answer(question)


def choose_action(question: str) -> tuple[str, Callable[..., str]]:
    """질문을 보고 어떤 도구를 쓸지 고른다.

    이 예제는 진짜 복잡한 계획 대신, 학습용 규칙 기반 분기만 사용한다.
    실제 에이전트는 보통 LLM 이 직접 다음 행동을 고르기도 한다.
    """
    lowered = question.lower()

    if any(keyword in question for keyword in ["몇 개", "구성", "종류", "요약"]):
        return ("문서 구성을 먼저 요약하는 것이 맞음", tool_document_summary)

    # 문서 자체를 보여달라는 요청이면 검색보다 목록 조회가 먼저다.
    if any(keyword in question for keyword in ["문서", "목록", "documents"]):
        return ("문서 목록을 먼저 보여주는 것이 맞음", tool_list_documents)

    # 이 키워드들은 현재 예제 문서와 직접 관련 있는 질문들이다.
    # 이런 경우에는 RAG 도구를 써서 문서를 찾아본 뒤 답하게 한다.
    if any(
        keyword in question
        for keyword in ["날씨", "지원", "환불", "정책", "고객", "주말"]
    ):
        return ("문서 기반 질문이라 RAG 도구를 사용", tool_rag)

    if any(keyword in lowered for keyword in ["weather", "support", "refund", "policy"]):
        return ("영문이지만 문서 검색 주제라 RAG 도구를 사용", tool_rag)

    # 문서 검색이 꼭 필요하지 않은 일반 질문은 바로 답변 생성으로 보낸다.
    return ("문서 검색보다 일반 답변이 더 적절함", tool_direct_answer)


@audit_log(action="Agent.RunTrace")
def run_agent_with_trace(question: str) -> dict[str, str]:
    """질문을 받아 도구 선택 과정과 최종 결과를 함께 반환한다."""
    print("=" * 60, flush=True)
    print("Agent 데모", flush=True)
    print("=" * 60, flush=True)
    print(f"[입력] {question}", flush=True)

    reason, action = choose_action(question)
    print("[계획] 질문을 보고 다음 행동을 결정합니다.", flush=True)
    print(f"  - 판단: {reason}", flush=True)
    print(f"  - 선택 도구: {action.__name__}", flush=True)

    print("[행동] 도구를 실행합니다.", flush=True)
    # 도구마다 받는 인자가 다르다.
    # RAG/일반답변 도구는 질문 문자열이 필요하고,
    # 문서 목록 도구는 추가 인자 없이 바로 실행된다.
    if action is tool_rag or action is tool_direct_answer:
        result = action(question)
    else:
        result = action()

    # 에이전트는 보통 도구 실행 결과를 관찰한 뒤 다음 행동을 정한다.
    # 이 예제는 한 번만 실행하고 끝나는 아주 작은 형태다.
    print("[관찰] 도구 실행 결과를 받았습니다.", flush=True)
    return {
        "question": question,
        "reason": reason,
        "tool_name": action.__name__,
        "result": result,
    }


def run_agent(question: str) -> str:
    """질문을 받아 도구를 고르고, 최종 결과 문자열만 반환한다."""
    trace = run_agent_with_trace(question)
    return trace["result"]


def main() -> None:
    """학습용 예제 질문을 순서대로 실행한다."""
    # 질문별로 어떤 도구가 선택되는지 비교해보기 위해
    # 성격이 다른 예제 질문을 섞어 두었다.
    questions = [
        "문서 목록 보여줘",
        "문서 구성 요약해줘",
        "주말에 고객 지원 받을 수 있어?",
        "서울 여름 날씨는 어때?",
        "파이썬은 어떤 언어야?",
    ]

    for index, question in enumerate(questions, start=1):
        print()
        print(f"======== Agent 질문 {index} ========", flush=True)
        try:
            answer = run_agent(question)
        except Exception as exc:
            print(f"[오류] {exc}", file=sys.stderr, flush=True)
            sys.exit(1)
        print("--- 최종 결과 ---", flush=True)
        print(answer, flush=True)


if __name__ == "__main__":
    main()
