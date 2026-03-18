import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.guardrails import SQLGuardrail
import pytest

def test_guardrail_dml_block():
    guard = SQLGuardrail()
    
    # 1. DELETE 차단 테스트
    with pytest.raises(PermissionError) as exc:
        guard.validate_query("DELETE FROM users")
    assert "허용되지 않은 명령어 감지: DELETE" in str(exc.value)
    
    # 2. DROP 차단 테스트
    with pytest.raises(PermissionError):
        guard.validate_query("DROP TABLE users")

    # 3. UPDATE 차단 테스트
    with pytest.raises(PermissionError):
        guard.validate_query("UPDATE users SET name='hacker'")

def test_guardrail_limit_injection():
    guard = SQLGuardrail()
    
    # LIMIT가 없는 경우 자동 추가
    sql = "SELECT * FROM users"
    safe_sql = guard.validate_query(sql)
    assert "LIMIT 1000" in safe_sql.upper()
    
    # 이미 LIMIT가 있는 경우 유지
    sql_with_limit = "SELECT * FROM users LIMIT 5"
    safe_sql_with_limit = guard.validate_query(sql_with_limit)
    assert "LIMIT 5" in safe_sql_with_limit.upper()
    assert "LIMIT 1000" not in safe_sql_with_limit.upper()

def test_guardrail_cartesian_product():
    guard = SQLGuardrail()
    
    # 1. 콤마로 테이블을 나열하고 WHERE가 없는 경우 (위험)
    with pytest.raises(ValueError) as exc:
        guard.validate_query("SELECT * FROM users, orders")
    assert "Cartesian Product" in str(exc.value)
    
    # 2. JOIN 키워드는 있지만 ON/WHERE가 명확하지 않은 경우 (sqlparse 토큰 분석에 따름)
    # 현재 구현은 JOIN 키워드 자체가 있으면 통과시키되, 콤마 나열만 체크함.
    
    # 3. 정상적인 JOIN/WHERE는 통과해야 함
    try:
        guard.validate_query("SELECT * FROM users WHERE id = 1")
    except ValueError:
        pytest.fail("정상적인 WHERE 문이 Cartesian Product로 오진되었습니다.")

if __name__ == "__main__":
    # pytest 없이도 실행 가능하도록 간단한 실행 로직
    try:
        test_guardrail_dml_block()
        print("[SUCCESS] DML Block Test Passed")
        test_guardrail_limit_injection()
        print("[SUCCESS] LIMIT Injection Test Passed")
        test_guardrail_cartesian_product()
        print("[SUCCESS] Cartesian Product Test Passed")
    except Exception as e:
        print(f"[FAILURE] Test Failed: {e}")
        sys.exit(1)
