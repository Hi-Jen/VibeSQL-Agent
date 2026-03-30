"""
connection.py - SQLAlchemy DB 연결 및 스키마 정보 추출 모듈

SQLite 메모리 DB에 테스트용 테이블과 더미 데이터를 생성하고,
LLM 프롬프트에 주입할 스키마 정보를 문자열로 반환합니다.
"""

from datetime import date

from sqlalchemy import (
    create_engine, MetaData, Table, Column, Integer, String,
    Float, Date, ForeignKey, text, inspect, Engine
)
from sqlalchemy.orm import Session


class DatabaseManager:
    """
    DB 연결, 스키마 조회, 쿼리 실행을 담당하는 클래스.
    테스트 시에는 SQLite 인메모리 DB를 사용합니다.
    """

    def __init__(self, database_url: str = "sqlite:///:memory:"):
        """
        Args:
            database_url: SQLAlchemy 연결 문자열.
                          기본값은 인메모리 SQLite.
        """
        self.engine: Engine = create_engine(database_url, echo=False)
        self.metadata = MetaData()

    def initialize_demo_db(self) -> None:
        """
        테스트용 departments, employees 테이블을 생성하고
        더미 데이터를 삽입합니다.
        """
        # 부서 테이블 정의
        departments = Table(
            "departments", self.metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("department_name", String(100), nullable=False),
            Column("location", String(100)),
        )

        # 직원 테이블 정의
        employees = Table(
            "employees", self.metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("name", String(100), nullable=False),
            Column("email", String(150)),
            Column("position", String(50)),
            Column("salary", Float),
            Column("hire_date", Date),
            Column("department_id", Integer, ForeignKey("departments.id")),
        )

        # 테이블 생성
        self.metadata.create_all(self.engine)

        # 더미 데이터 삽입
        with self.engine.begin() as conn:
            conn.execute(departments.insert(), [
                {"department_name": "개발팀",   "location": "서울 본사 3층"},
                {"department_name": "마케팅팀", "location": "서울 본사 5층"},
                {"department_name": "인사팀",   "location": "서울 본사 2층"},
                {"department_name": "디자인팀", "location": "판교 오피스 4층"},
            ])

            conn.execute(employees.insert(), [
                {"name": "김민수", "email": "minsu@company.com",
                 "position": "시니어 개발자", "salary": 7500,
                 "hire_date": date(2020, 3, 15), "department_id": 1},
                {"name": "이지은", "email": "jieun@company.com",
                 "position": "마케팅 매니저", "salary": 6800,
                 "hire_date": date(2019, 7, 1), "department_id": 2},
                {"name": "박서준", "email": "seojun@company.com",
                 "position": "주니어 개발자", "salary": 4500,
                 "hire_date": date(2023, 1, 10), "department_id": 1},
                {"name": "최유진", "email": "yujin@company.com",
                 "position": "HR 담당자", "salary": 5200,
                 "hire_date": date(2021, 9, 20), "department_id": 3},
                {"name": "정하늘", "email": "haneul@company.com",
                 "position": "UI 디자이너", "salary": 5800,
                 "hire_date": date(2022, 5, 11), "department_id": 4},
                {"name": "한소희", "email": "sohee@company.com",
                 "position": "시니어 개발자", "salary": 8200,
                 "hire_date": date(2018, 11, 3), "department_id": 1},
                {"name": "오태양", "email": "taeyang@company.com",
                 "position": "콘텐츠 마케터", "salary": 4800,
                 "hire_date": date(2023, 6, 15), "department_id": 2},
            ])

    def get_schema_info(self) -> str:
        """
        DB의 모든 테이블 이름, 컬럼명, 데이터 타입을 LLM 프롬프트에
        주입할 수 있는 문자열 형태로 반환합니다.

        Returns:
            스키마 정보 문자열 (예:
              Table: employees
                - id (INTEGER, PK)
                - name (VARCHAR(100), NOT NULL)
                ...
            )
        """
        inspector = inspect(self.engine)
        table_names = inspector.get_table_names()

        if not table_names:
            return "데이터베이스에 테이블이 없습니다."

        schema_parts: list[str] = []

        for table_name in table_names:
            columns = inspector.get_columns(table_name)
            pk_columns = inspector.get_pk_constraint(table_name)
            pk_names = set(pk_columns.get("constrained_columns", []))
            fk_list = inspector.get_foreign_keys(table_name)

            # 외래키 매핑: 컬럼명 → 참조 테이블.컬럼
            fk_map: dict[str, str] = {}
            for fk in fk_list:
                for col, ref_col in zip(
                    fk["constrained_columns"],
                    fk["referred_columns"]
                ):
                    fk_map[col] = f"{fk['referred_table']}.{ref_col}"

            lines = [f"Table: {table_name}"]

            for col in columns:
                col_name = col["name"]
                col_type = str(col["type"])
                nullable = col.get("nullable", True)

                # 부가 정보 조립
                flags: list[str] = []
                if col_name in pk_names:
                    flags.append("PK")
                if not nullable:
                    flags.append("NOT NULL")
                if col_name in fk_map:
                    flags.append(f"FK → {fk_map[col_name]}")

                flag_str = f", {', '.join(flags)}" if flags else ""
                lines.append(f"  - {col_name} ({col_type}{flag_str})")

            schema_parts.append("\n".join(lines))

        return "\n\n".join(schema_parts)

    def execute_query(self, sql: str) -> list[dict]:
        """
        검증 완료된 SQL을 실행하고 결과를 딕셔너리 리스트로 반환합니다.

        Args:
            sql: 실행할 SELECT SQL 문자열

        Returns:
            각 행을 딕셔너리로 변환한 결과 리스트

        Raises:
            Exception: SQL 실행 중 발생한 에러를 그대로 전파
        """
        with self.engine.connect() as conn:
            result = conn.execute(text(sql))
            columns = list(result.keys())
            rows = result.fetchall()

        return [dict(zip(columns, row)) for row in rows]
