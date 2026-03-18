from core.engine import VibeSQLEngine
from utils.export import DataExporter
import json

def test_vibe_sql_flow():
    # 1. 엔진 초기화 (테스트용 DB 사용)
    engine = VibeSQLEngine(db_url="sqlite:///vibesql_demo.db")
    
    print("=== [1] 프롬프트 생성 테스트 ===")
    prompt = engine.build_prompt_with_context("지난 달 활성유저 리스트랑 이메일 보여줘", "marketing")
    print(prompt)
    
    print("\n=== [2] SQL 생성 및 실행 테스트 (활성유저) ===")
    result = engine.generate_and_execute("지난 달 활성유저 보여줘", "marketing")
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Generated SQL: {result['sql']}")
        print(f"Result Count: {result['count']}")
        print(f"Data Sample: {result['results'][:2]}")
        
        # 3. CSV 내보내기 테스트
        csv_path = DataExporter.to_csv(result['results'], "marketing_active_users.csv")
        print(f"\n[3] 결과가 저장되었습니다: {csv_path}")

    print("\n=== [4] 안전 장치 테스트 (Cartesian Product) ===")
    try:
        # 가드레일에서 차단되어야 함
        invalid_sql = "SELECT * FROM users, orders"
        engine.guardrail.validate_query(invalid_sql)
    except Exception as e:
        print(f"Expected Guardrail Block: {e}")

if __name__ == "__main__":
    test_vibe_sql_flow()
