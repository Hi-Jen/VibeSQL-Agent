import sys
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.engine import VibeSQLEngine
from src.core.dictionary import YamlDictionary
from src.db.connection import DatabaseConnection

def test_real_gemini_execution():
    print("=== [실전 통합 테스트] Google Gemini + SQLite 실연동 검증 ===")
    
    # 1. 환경 설정 확인
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key.startswith("AIzaSy-dummy"):
        print("❌ 에러: 유효한 GOOGLE_API_KEY가 .env 파일에 설정되지 않았습니다.")
        return

    # 2. 엔진 초기화
    db = DatabaseConnection("sqlite:///vibesql_demo.db")
    dictionary = YamlDictionary("config/dictionary.yaml")
    engine = VibeSQLEngine(dictionary=dictionary, db_connection=db)
    
    # 3. 테스트 시나리오
    queries = [
        "최근 30일 이내에 활동한 유저 리스트 뽑아줘",
        "마케팅 부서 기준으로 활성유저 데이터 조회해줘",
        "테이블에 있는 모든 사용자 정보를 보여줘"
    ]
    
    for idx, nl_query in enumerate(queries, 1):
        print(f"\n[{idx}] 질문: {nl_query}")
        print("-" * 50)
        
        try:
            result = engine.generate_and_execute(nl_query, "marketing")
            
            if result.get("success"):
                print(f"✅ 생성된 SQL: {result['sql']}")
                print(f"✅ AI 해설: {result['explanation']}")
                print(f"✅ 데이터 건수: {result['count']}")
                if result['count'] > 0:
                    print(f"📋 샘플 데이터: {result['data'][0]}")
            else:
                print(f"❌ 실행 실패: {result.get('error')}")
                if "last_sql" in result:
                    print(f"⚠️ 마지막 시도 SQL: {result['last_sql']}")
                    
        except Exception as e:
            print(f"💥 예상치 못한 에러 발생: {str(e)}")

if __name__ == "__main__":
    test_real_gemini_execution()
