"""
test_connection.py - DB 연결 및 스키마 추출 모듈 단위 테스트

인메모리 SQLite에서 테이블 생성, 더미 데이터, 스키마 정보 추출을 검증합니다.
"""

import pytest
from src.db.connection import DatabaseManager


@pytest.fixture
def db():
    """각 테스트마다 깨끗한 인메모리 DB를 생성합니다."""
    manager = DatabaseManager("sqlite:///:memory:")
    manager.initialize_demo_db()
    return manager


class TestDemoDatabase:
    """데모 DB 초기화 검증"""

    def test_tables_created(self, db: DatabaseManager):
        """departments, employees 테이블이 생성되었는지 확인"""
        schema = db.get_schema_info()
        assert "departments" in schema
        assert "employees" in schema

    def test_employee_count(self, db: DatabaseManager):
        """더미 직원 데이터 7건이 삽입되었는지 확인"""
        result = db.execute_query("SELECT COUNT(*) as cnt FROM employees")
        assert result[0]["cnt"] == 7

    def test_department_count(self, db: DatabaseManager):
        """더미 부서 데이터 4건이 삽입되었는지 확인"""
        result = db.execute_query("SELECT COUNT(*) as cnt FROM departments")
        assert result[0]["cnt"] == 4


class TestSchemaInfo:
    """스키마 정보 추출 검증"""

    def test_contains_column_names(self, db: DatabaseManager):
        """주요 컬럼명이 스키마 정보에 포함되는지 확인"""
        schema = db.get_schema_info()
        assert "name" in schema
        assert "salary" in schema
        assert "department_name" in schema
        assert "hire_date" in schema

    def test_contains_types(self, db: DatabaseManager):
        """데이터 타입 정보가 포함되는지 확인"""
        schema = db.get_schema_info()
        assert "INTEGER" in schema
        assert "VARCHAR" in schema or "FLOAT" in schema

    def test_contains_pk_info(self, db: DatabaseManager):
        """PK 정보가 포함되는지 확인"""
        schema = db.get_schema_info()
        assert "PK" in schema

    def test_contains_fk_info(self, db: DatabaseManager):
        """FK 정보가 포함되는지 확인"""
        schema = db.get_schema_info()
        assert "FK" in schema


class TestQueryExecution:
    """쿼리 실행 검증"""

    def test_select_all_employees(self, db: DatabaseManager):
        """전체 직원 조회"""
        result = db.execute_query("SELECT * FROM employees")
        assert len(result) == 7
        assert "name" in result[0]

    def test_join_query(self, db: DatabaseManager):
        """JOIN 쿼리 실행"""
        sql = (
            "SELECT e.name, d.department_name "
            "FROM employees e "
            "JOIN departments d ON e.department_id = d.id "
            "WHERE d.department_name = '개발팀'"
        )
        result = db.execute_query(sql)
        # 개발팀에는 3명의 직원이 있음
        assert len(result) == 3

    def test_aggregate_query(self, db: DatabaseManager):
        """집계 쿼리 실행"""
        result = db.execute_query(
            "SELECT AVG(salary) as avg_salary FROM employees"
        )
        assert result[0]["avg_salary"] > 0

    def test_invalid_sql_raises(self, db: DatabaseManager):
        """잘못된 SQL은 예외 발생"""
        with pytest.raises(Exception):
            db.execute_query("SELECT * FROM nonexistent_table")
