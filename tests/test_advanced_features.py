import sys
import os
os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-test"
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.engine import VibeSQLEngine
from src.core.dictionary import YamlDictionary
from src.db.connection import DatabaseConnection
from unittest.mock import MagicMock, patch

def test_llm_integration():
    print("=== [테스트] LangChain 실연동 및 출력 파싱 검증 ===")
    
    db = DatabaseConnection("sqlite:///vibesql_demo.db")
    dictionary = YamlDictionary("config/dictionary.yaml")
    engine = VibeSQLEngine(dictionary=dictionary, db_connection=db)
    
    # LLM Mocking: patch를 사용하여 ChatOpenAI.invoke를 가로챔
    with patch("langchain_openai.ChatOpenAI.invoke") as mock_invoke:
        mock_response = MagicMock()
        mock_response.content = """
네, 분석 결과입니다.
```sql
SELECT name, last_login FROM users WHERE last_login >= date('now', '-30 days')
```
최근 30일 이내에 로그인한 유저 리스트를 조회합니다.
"""
        mock_invoke.return_value = mock_response
        
        print("\n[1] LLM 응답 파싱 테스트")
        result = engine.generate_and_execute("최근 활성유저 보여줘", "marketing")
        
        if result.get("success"):
            print(f"✅ SQL 추출 성공: {result['sql']}")
            print(f"✅ 해설 추출 성공: {result['explanation']}")
            print(f"✅ 데이터 조회 성공 (건수: {result['count']})")
        else:
            print(f"❌ 테스트 실패: {result.get('error')}")

if __name__ == "__main__":
    test_llm_integration()
