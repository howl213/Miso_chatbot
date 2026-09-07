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
    key_str = os.getenv("AUDIT_ENCRYPTION_KEY")
    if not key_str:
        print("[오류] .env 파일에서 AUDIT_ENCRYPTION_KEY를 찾을 수 없습니다.")
        sys.exit(1)
        
    crypto = AuditCrypto(key=key_str.encode('utf-8'))
    log_dir = parent_dir / "audit-logs"
    log_files = glob.glob(str(log_dir / "audit_log*.jsonl"))
    
    out_file_path = parent_dir / "manual_test_logs.md"
    
    with open(out_file_path, "w", encoding="utf-8") as out_f:
        out_f.write("# 수동 테스트 결과 로그 (복호화 데이터)\n\n")
        out_f.write("> **참고:** `.env` 마스터 키가 적용되기 전에(구현 초기에) 임시 키로 저장되었던 일부 과거 로그들은 마스터 키 불일치로 인해 복호화가 실패할 수 있습니다. 정상적으로 키가 연동된 이후의 테스트 내역들을 확인해주세요.\n\n")
        
        for log_file in log_files:
            out_f.write(f"## 📂 파일: `{Path(log_file).name}`\n\n")
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for idx, line in enumerate(lines, 1):
                    line = line.strip()
                    if not line: continue
                    record = json.loads(line)
                    event_id = record.get("event_id")
                    timestamp = record.get("timestamp")
                    action = record.get("action")
                    encrypted_payload = record.get("payload_encrypted")
                    
                    out_f.write(f"### [{idx}] Event: `{event_id}`\n")
                    out_f.write(f"- **Time:** {timestamp}\n")
                    out_f.write(f"- **Action:** {action}\n")
                    
                    try:
                        decrypted_dict = crypto.decrypt_payload(encrypted_payload)
                        is_malicious = decrypted_dict.get("MALICIOUS_INTENT_DETECTED", False)
                        
                        # masking.py 에서 플래그를 추가하면 최상위에 있거나 output 안에 있을 수 있음
                        if not is_malicious:
                            is_malicious = decrypted_dict.get("output", {}).get("MALICIOUS_INTENT_DETECTED", False)
                            
                        if is_malicious:
                            out_f.write("> **🚨 [경고] 악성 인젝션 시도(Malicious Intent)가 감지되었습니다!**\n\n")
                        
                        out_f.write("```json\n")
                        out_f.write(json.dumps(decrypted_dict, indent=2, ensure_ascii=False) + "\n")
                        out_f.write("```\n\n")
                    except Exception as e:
                        out_f.write(f"> ❌ **복호화 실패:** (마스터 키 적용 이전 로그이므로 열람 불가)\n\n")

    print(f"로그 내보내기 완료: {out_file_path}")

if __name__ == "__main__":
    main()
