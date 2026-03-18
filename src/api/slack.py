from fastapi import FastAPI, Request, BackgroundTasks
from pydantic import BaseModel
import httpx
import os
from src.core.engine import VibeSQLEngine
from src.core.dictionary import YamlDictionary
from src.db.connection import DatabaseConnection

app = FastAPI()

# 글로벌 엔진 초기화 (DB 및 사전 로드)
db_conn = DatabaseConnection("sqlite:///vibesql_demo.db")
dictionary = YamlDictionary("config/dictionary.yaml")
engine = VibeSQLEngine(dictionary=dictionary, db_connection=db_conn)

class SlackEvent(BaseModel):
    token: str
    challenge: str = None
    type: str
    event: dict = None

@app.post("/slack/events")
async def slack_events(request: Request, background_tasks: BackgroundTasks):
    """
    슬랙 이벤트를 수신하는 엔드포인트.
    3초 이내 응답을 위해 BackgroundTasks를 사용함.
    """
    data = await request.json()
    
    # URL Verification (슬랙 앱 설정 시 필요)
    if "challenge" in data:
        return {"challenge": data["challenge"]}
    
    event = data.get("event", {})
    if event.get("type") == "app_mention":
        # 백그라운드에서 처리 시작
        background_tasks.add_task(process_vibe_query, event)
        return {"status": "ok"}
    
    return {"status": "ignored"}

async def process_vibe_query(event: dict):
    """
    자연어 쿼리를 처리하고 결과를 슬랙으로 재전송함.
    """
    text = event.get("text", "")
    channel = event.get("channel")
    user = event.get("user")
    
    # 1. 초기 응답 전송 (처리 중 알림)
    # 실제 구현 시 Slack SDK의 chat.postMessage 사용
    print(f"[*] Processing query from {user} in {channel}: {text}")

    # 2. 엔진 실행
    # (주의: 실제 구현 시 텍스트에서 멘션 제거 로직 필요)
    result = engine.generate_and_execute(text, department="marketing")
    
    # 3. 결과 전송 (chat.update 또는 chat.postMessage)
    if result.get("success"):
        response_text = f"✅ **쿼리 실행 결과**\n\n> {result['explanation']}\n\n```sql\n{result['sql']}\n```\n\n*데이터 {result['count']}건이 조회되었습니다.*"
    else:
        response_text = f"❌ **쿼리 실행 실패**\n\n> {result.get('explanation', '분석 실패')}\n\n에러: {result.get('error')}"
    
    print(f"[+] Response: {response_text}")
    # TODO: httpx를 사용하여 슬랙 API 호출 (chat.postMessage)
