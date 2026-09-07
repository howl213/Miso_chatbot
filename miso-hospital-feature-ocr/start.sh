#!/bin/bash
# 프로젝트 루트에서 실행: bash start.sh
# WAS(3000), 프론트(5500, 캐시 무효화된 serve.py 사용), 챗봇 서비스(8000) 세 프로세스를
# 한 번에 백그라운드로 띄운다.
set -e

mkdir -p .run

nohup node was/server.js > .run/was.log 2>&1 &
echo $! > .run/was.pid

# frontend/serve.py는 캐시를 꺼서 파일 수정 후 새로고침해도 바로 반영되게 해주는 버전.
# serve.py는 "실행된 위치(cwd)" 기준으로 파일을 찾으므로, frontend/ 안으로 이동해서 실행해야 함.
# bash -c 한 줄로 cd+실행을 묶어야 백그라운드 전환 시 cd가 안 씹힘 (exec로 PID도 그대로 유지됨).
nohup bash -c "cd frontend && exec python3 serve.py 5500" > .run/frontend.log 2>&1 &
echo $! > .run/frontend.pid

nohup uvicorn main:app --app-dir chatbot-service --port 8000 > .run/chatbot.log 2>&1 &
echo $! > .run/chatbot.pid

sleep 1
echo "WAS 실행됨        (PID: $(cat .run/was.pid))      - 로그: .run/was.log"
echo "프론트 실행됨      (PID: $(cat .run/frontend.pid)) - 로그: .run/frontend.log"
echo "챗봇 서비스 실행됨 (PID: $(cat .run/chatbot.pid))  - 로그: .run/chatbot.log"
echo ""
echo "종료하려면: bash stop.sh"
echo "로그 실시간 보기: tail -f .run/was.log .run/frontend.log .run/chatbot.log"
