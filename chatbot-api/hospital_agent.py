from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Callable

BASE_DIR = Path(__file__).resolve().parent

def load_module(module_name: str, file_name: str):
    module_path = BASE_DIR / file_name
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"모듈을 불러올 수 없습니다: {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

DOCUMENTS = load_module("documents", "1-documents.py")
sys.modules.setdefault("documents", DOCUMENTS)
EMBEDDINGS = load_module("embeddings", "2-embeddings.py")
sys.modules.setdefault("embeddings", EMBEDDINGS)
LLM = load_module("llm", "3-1-llm.py")
sys.modules.setdefault("llm", LLM)
RAG = load_module("rag", "3-2-Rag.py")

def tool_list_documents() -> str:
    docs = DOCUMENTS.load_documents()
    lines = ["[도구] 병원 정보 문서 목록 조회"]
    for doc in docs:
        lines.append(f"- {doc.doc_id}: {doc.text}")
    return "\n".join(lines)

def tool_rag(question: str) -> str:
    return RAG.run_rag(question, top_k=2)

def tool_direct_answer(question: str) -> str:
    return LLM.generate_direct_answer(question)

def choose_action(question: str) -> tuple[str, Callable[..., str]]:
    lowered = question.lower()
    
    # 병원 도메인 관련 키워드
    if any(keyword in question for keyword in ["시간", "위치", "어디", "증상", "아파", "예약", "진료", "기침", "복통", "응급실"]):
        return ("병원 정보 관련 질문이므로 RAG 도구를 사용", tool_rag)

    if any(keyword in lowered for keyword in ["hospital", "time", "location", "symptom"]):
        return ("영문 병원 질문이므로 RAG 도구를 사용", tool_rag)

    return ("일반적인 질문이거나 확인되지 않은 질문이므로 일반 답변을 사용", tool_direct_answer)

def run_agent(question: str) -> str:
    reason, action = choose_action(question)
    
    if action is tool_rag or action is tool_direct_answer:
        result = action(question)
    else:
        result = action()
        
    return result

if __name__ == "__main__":
    test_q = "배가 아프고 토할 것 같은데 어디로 가야하나요?"
    print(run_agent(test_q))
