import sys
import os
# src 폴더를 path에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.engine import VibeSQLEngine
from src.core.dictionary import YamlDictionary
from src.db.connection import DatabaseConnection
from src.utils.export import DataExporter
from sqlalchemy import text

def setup_test_db():
    db = DatabaseConnection("sqlite:///vibesql_demo.db")
    with db.engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS users"))
        conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, last_login DATE, total_spent INTEGER)"))
        conn.execute(text("INSERT INTO users (name, last_login, total_spent) VALUES ('홍길동', '2026-03-10', 500000)"))
        conn.execute(text("INSERT INTO users (name, last_login, total_spent) VALUES ('김철수', '2026-03-15', 1200000)"))
        conn.commit()
    return db

def test_self_correction_flow():
    print("=== [테스트 시작] Self-Correction 루프 및 리팩토링 구조 검증 ===")
    
    # 1. 환경 설정
    db = setup_test_db()
    dictionary = YamlDictionary("config/dictionary.yaml")
    engine = VibeSQLEngine(dictionary=dictionary, db_connection=db, max_retries=3)
    
    # 2. 자연어 질문 실행 (내부적으로 1회 실패 후 2회차에 성공하도록 Mocking 되어 있음)
    print("\n질문: '지난 달 활성유저 보여줘' (마케팅 부서)")
    result = engine.generate_and_execute("지난 달 활성유저 보여줘", "marketing")
    
    # 3. 결과 검증
    if result.get("success"):
        print(f"\n[성공] 쿼리 실행 완료!")
        print(f"최종 SQL: {result['sql']}")
        print(f"리트라이 횟수: {result['retry_count']}")
        print(f"데이터 개수: {result['count']}")
        print(f"데이터 샘플: {result['results'][0]}")
        
        # 4. 파일 내보내기 검증
        csv_path = DataExporter.to_csv(result['results'], "marketing_active_users_refactored.csv")
        print(f"\n[결과 저장] CSV 경로: {csv_path}")
    else:
        print(f"\n[실패] 에러 발생: {result.get('error')}")
        print(f"마지막 에러 메시지: {result.get('last_error')}")

    # 4. 가드레일 (DELETE) 차단 검증
    print("\n=== [가드레일 테스트] DELETE 포함 쿼리 ===")
    bad_result = engine.generate_and_execute("유저 정보 다 지워줘", "marketing")
    if "Guardrail Block" in bad_result.get("error", ""):
        print(f"[성공] 위험 쿼리 차단됨: {bad_result['error']}")
    else:
        print(f"[실패] 위험 쿼리가 차단되지 않음!")

if __name__ == "__main__":
    test_self_correction_flow()
