import sys
import importlib.util
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
agent_module_path = BASE_DIR / "4-agent.py"

spec = importlib.util.spec_from_file_location("agent_module", agent_module_path)
agent_module = importlib.util.module_from_spec(spec)
sys.modules["agent_module"] = agent_module
spec.loader.exec_module(agent_module)

def main():
    print("=" * 60)
    print("대화형 수동 테스트 CLI (종료하려면 'exit' 또는 'quit' 입력)")
    print("=" * 60)
    
    while True:
        try:
            user_input = input("\n[👤 사용자]: ")
            if user_input.strip().lower() in ['exit', 'quit']:
                print("채팅을 종료합니다.")
                break
                
            if not user_input.strip():
                continue
                
            # agent.py 의 run_agent 호출 (내부적으로 데코레이터가 부착된 run_agent_with_trace 실행)
            answer = agent_module.run_agent(user_input)
            print(f"[🤖 RAG 에이전트]: {answer}")
            
        except (KeyboardInterrupt, EOFError):
            print("\n채팅을 종료합니다.")
            break
        except Exception as e:
            print(f"[오류 발생]: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
