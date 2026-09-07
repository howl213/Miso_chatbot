from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Callable, Optional
from datetime import datetime, timedelta

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
TOOLS_DB = load_module("tools_db", "tools_db.py")

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

def tool_book_appointment(patient_id: Optional[int], question: str) -> str:
    if not patient_id:
        return "로그인이 필요하거나 환자 정보를 알 수 없어 예약을 진행할 수 없습니다."
    
    # 단순한 예시를 위해 날짜는 내일, 과목은 내과로 고정 또는 키워드로 추출.
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d 10:00:00")
    dept = "내과" 
    
    if "소아과" in question:
        dept = "소아과"
    elif "이비인후과" in question:
        dept = "이비인후과"
    
    return TOOLS_DB.book_appointment(patient_id, tomorrow, dept)

def tool_check_appointments(patient_id: Optional[int], question: str) -> str:
    return TOOLS_DB.check_appointments(patient_id)

def tool_check_medical_records(patient_id: Optional[int], question: str) -> str:
    return TOOLS_DB.check_medical_records(patient_id)


def choose_action(question: str) -> tuple[str, Callable[..., str]]:
    lowered = question.lower()
    
    # 예약 확인 의도
    if any(keyword in question for keyword in ["예약 확인", "예약 내역", "내 예약", "예약조회"]):
        return ("예약 확인 질문이므로 DB 조회 도구를 사용", tool_check_appointments)
        
    # 예약 생성 의도
    if any(keyword in question for keyword in ["예약해", "예약 해", "진료 예약", "예약 잡"]):
        return ("예약 생성 질문이므로 DB 예약 도구를 사용", tool_book_appointment)
        
    # 진료 기록 조회 의도
    if any(keyword in question for keyword in ["진료 기록", "진료기록", "내 기록", "이전 기록"]):
        return ("진료 기록 조회 질문이므로 DB 기록 조회 도구를 사용", tool_check_medical_records)
    
    # 병원 도메인 관련 키워드 (위의 명확한 의도를 제외한 나머지 중 병원과 관련된 질문)
    if any(keyword in question for keyword in ["시간", "위치", "어디", "증상", "아파", "예약", "진료", "기침", "복통", "응급실"]):
        return ("병원 정보 관련 질문이므로 RAG 도구를 사용", tool_rag)

    if any(keyword in lowered for keyword in ["hospital", "time", "location", "symptom"]):
        return ("영문 병원 질문이므로 RAG 도구를 사용", tool_rag)

    return ("일반적인 질문이거나 확인되지 않은 질문이므로 일반 답변을 사용", tool_direct_answer)

def run_agent(question: str, patient_id: Optional[int] = None) -> str:
    reason, action = choose_action(question)
    
    if action in [tool_book_appointment, tool_check_appointments, tool_check_medical_records]:
        result = action(patient_id, question)
    elif action in [tool_rag, tool_direct_answer]:
        result = action(question)
    else:
        result = action()
        
    return result

if __name__ == "__main__":
    test_q = "내 예약 확인해줘"
    print(run_agent(test_q, patient_id=1))
