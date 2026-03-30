"""
test_guardrails.py - 가드레일 모듈 단위 테스트

안전한 쿼리 통과, 위험 쿼리 차단, LIMIT 자동 추가 등을 검증합니다.
"""

import pytest
from src.core.guardrails import validate_sql


class TestSafeQueries:
    """정상적인 SELECT 쿼리가 통과하는지 검증"""

    def test_simple_select(self):
        sql = "SELECT * FROM employees"
        result = validate_sql(sql)
        assert "SELECT" in result
        assert "LIMIT 1000" in result

    def test_select_with_where(self):
        sql = "SELECT name, salary FROM employees WHERE salary > 5000"
        result = validate_sql(sql)
        assert "WHERE salary > 5000" in result
        assert "LIMIT 1000" in result

    def test_select_with_join(self):
        sql = (
            "SELECT e.name, d.department_name "
            "FROM employees e "
            "JOIN departments d ON e.department_id = d.id"
        )
        result = validate_sql(sql)
        assert "JOIN" in result
        assert "LIMIT 1000" in result

    def test_cte_query(self):
        """WITH(CTE) 쿼리도 허용되어야 함"""
        sql = (
            "WITH dev_team AS ("
            "  SELECT * FROM employees WHERE department_id = 1"
            ") SELECT * FROM dev_team"
        )
        result = validate_sql(sql)
        assert "WITH" in result

    def test_existing_limit_preserved(self):
        """이미 LIMIT이 있으면 중복 추가하지 않음"""
        sql = "SELECT * FROM employees LIMIT 10"
        result = validate_sql(sql)
        assert "LIMIT 10" in result
        assert "LIMIT 1000" not in result


class TestDangerousQueries:
    """위험한 DML/DDL 쿼리가 차단되는지 검증"""

    def test_delete_blocked(self):
        with pytest.raises(ValueError, match="위험 SQL 감지|허용되지 않는 구문"):
            validate_sql("DELETE FROM employees WHERE id = 1")

    def test_drop_blocked(self):
        with pytest.raises(ValueError, match="위험 SQL 감지|허용되지 않는 구문"):
            validate_sql("DROP TABLE employees")

    def test_update_blocked(self):
        with pytest.raises(ValueError, match="위험 SQL 감지|허용되지 않는 구문"):
            validate_sql("UPDATE employees SET salary = 0")

    def test_insert_blocked(self):
        with pytest.raises(ValueError, match="위험 SQL 감지|허용되지 않는 구문"):
            validate_sql("INSERT INTO employees (name) VALUES ('해커')")

    def test_alter_blocked(self):
        with pytest.raises(ValueError, match="위험 SQL 감지|허용되지 않는 구문"):
            validate_sql("ALTER TABLE employees ADD COLUMN hack TEXT")

    def test_truncate_blocked(self):
        with pytest.raises(ValueError, match="위험 SQL 감지|허용되지 않는 구문"):
            validate_sql("TRUNCATE TABLE employees")


class TestEdgeCases:
    """경계 조건 테스트"""

    def test_empty_sql_raises(self):
        with pytest.raises(ValueError, match="빈 SQL"):
            validate_sql("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="빈 SQL"):
            validate_sql("   \n  ")

    def test_markdown_fences_stripped(self):
        """LLM이 마크다운으로 감싼 경우 정상 처리"""
        sql = "```sql\nSELECT * FROM employees\n```"
        result = validate_sql(sql)
        assert "SELECT" in result
        assert "```" not in result

    def test_semicolon_removed(self):
        """세미콜론이 제거되어야 함"""
        sql = "SELECT * FROM employees;"
        result = validate_sql(sql)
        assert not result.rstrip().endswith(";")
