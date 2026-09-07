from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sqlite3
import os
from cryptography.fernet import Fernet
from datetime import datetime

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Local imports
from pii_masking import mask_pii
from hospital_agent import run_agent

app = FastAPI(title="Hospital Chatbot API")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Allow CORS for the frontend (http://localhost:8080 or file://)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Encryption Setup ---
KEY_FILE = "secret.key"
if not os.path.exists(KEY_FILE):
    # Generate and save a new key
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as key_file:
        key_file.write(key)
else:
    with open(KEY_FILE, "rb") as key_file:
        key = key_file.read()

cipher = Fernet(key)

# --- Database Setup ---
DB_FILE = "chatbot_logs.db"
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            original_encrypted BLOB,
            masked_text TEXT,
            response TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- API Models ---
class ChatRequest(BaseModel):
    question: str
    patient_id: Optional[int] = None

class ChatResponse(BaseModel):
    answer: str
    masked_question: str

# --- API Endpoints ---
@app.post("/chat", response_model=ChatResponse)
@limiter.limit("5/minute")
async def chat_endpoint(req: ChatRequest, request: Request):
    original_question = req.question
    
    if not original_question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
        
    # 1. PII 마스킹 처리
    masked_question = mask_pii(original_question)
    
    # 2. RAG 에이전트를 통한 답변 생성 (반드시 마스킹된 질문 사용)
    try:
        answer = run_agent(masked_question, req.patient_id)
    except Exception as e:
        print(f"Agent error: {e}")
        answer = "죄송합니다. 현재 챗봇 서비스에 문제가 발생했습니다."
        
    # 3. 로그 DB 저장 (원문 암호화)
    try:
        encrypted_question = cipher.encrypt(original_question.encode('utf-8'))
        
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(
            "INSERT INTO logs (original_encrypted, masked_text, response) VALUES (?, ?, ?)",
            (encrypted_question, masked_question, answer)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Logging error: {e}")
        # 로깅 실패해도 챗봇 응답은 반환
    
    return ChatResponse(
        answer=answer,
        masked_question=masked_question
    )

if __name__ == "__main__":
    import uvicorn
    # run on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
