import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.engine import VibeSQLEngine
from src.core.dictionary import YamlDictionary
from src.db.connection import DatabaseConnection

def test_advanced_features():
    print("=== [테스트] 고도화 기능 (해설 & 스키마 필터링) 검증 ===")
    
    db = DatabaseConnection("sqlite:///vibesql_demo.db")
    dictionary = YamlDictionary("config/dictionary.yaml")
    engine = VibeSQLEngine(dictionary=dictionary, db_connection=db)
    
    # 1. 스키마 필터링 검증 (질문에 'users' 포함)
    print("\n[1] 스키마 필터링 테스트: '최근 유저 리스트 보여줘'")
    relevant_tables = engine._get_relevant_tables("최근 유저 리스트 보여줘")
    print(f"선택된 테이블: {relevant_tables}")
    
    prompt = engine.build_prompt_with_context("최근 유저 리스트 보여줘", "marketing")
    if "Table: users" in prompt and "Table: orders" not in prompt:
        print("✅ 토큰 최적화: 필요한 테이블 정보만 프롬프트에 주입됨.")
    else:
        print("⚠️ 스키마 필터링 결과 확인 필요.")

    # 2. 자연어 해설 생성 검증
    print("\n[2] 자연어 해설 및 결과 통합 테스트")
    result = engine.generate_and_execute("지난 달 활성유저 보여줘", "marketing")
    
    if result.get("success"):
        print(f"✅ 해설 생성: {result['explanation']}")
        print(f"✅ 실행 SQL: {result['sql']}")
        print(f"✅ 조회 건수: {result['count']}")
    else:
        print(f"❌ 테스트 실패: {result.get('error')}")

if __name__ == "__main__":
    test_advanced_features()
