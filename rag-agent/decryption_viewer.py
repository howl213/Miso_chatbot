import sys
import os
import json
import glob
from pathlib import Path
from dotenv import load_dotenv

current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent

load_dotenv(dotenv_path=current_dir / ".env")
sys.path.insert(0, str(parent_dir))

import importlib
audit_agent = importlib.import_module("audit-agent")
AuditCrypto = audit_agent.crypto.AuditCrypto

def main():
    print("=" * 60)
    print("감사 로그 복호화 뷰어 (Decryption Viewer)")
    print("=" * 60)
    
    key_str = os.getenv("AUDIT_ENCRYPTION_KEY")
    if not key_str:
        print("[오류] .env 파일에서 AUDIT_ENCRYPTION_KEY를 찾을 수 없습니다.")
        sys.exit(1)
        
    crypto = AuditCrypto(key=key_str.encode('utf-8'))
    
    log_dir = parent_dir / "audit-logs"
    log_files = glob.glob(str(log_dir / "audit_log*.jsonl"))
    
    if not log_files:
        print("조회할 감사 로그 파일이 없습니다.")
        return
        
    for log_file in log_files:
        print(f"\n📂 파일 열람: {Path(log_file).name}")
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if not lines:
                    print("  - 파일이 비어 있습니다.")
                    continue
                    
                for idx, line in enumerate(lines, 1):
                    line = line.strip()
                    if not line:
                        continue
                        
                    record = json.loads(line)
                    event_id = record.get("event_id")
                    timestamp = record.get("timestamp")
                    action = record.get("action")
                    encrypted_payload = record.get("payload_encrypted")
                    
                    try:
                        decrypted_dict = crypto.decrypt_payload(encrypted_payload)
                        print(f"\n[{idx}] 📝 Event: {event_id} | Time: {timestamp} | Action: {action}")
                        
                        # 악성 인젝션 여부 확인
                        is_malicious = decrypted_dict.get("output", {}).get("MALICIOUS_INTENT_DETECTED", False)
                        if is_malicious:
                            print("\033[91m[🚨 악성 쿼리 감지]\033[0m")
                            
                        # 결과 이쁘게 출력
                        print(json.dumps(decrypted_dict, indent=2, ensure_ascii=False))
                    except Exception as e:
                        print(f"[{idx}] 복호화 실패: EventID={event_id} / Error={e}")
                        
        except Exception as file_err:
            print(f"[오류] 파일 읽기 실패: {file_err}")

if __name__ == "__main__":
    main()
