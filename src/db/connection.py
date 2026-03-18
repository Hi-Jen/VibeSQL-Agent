from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any, Optional

class DatabaseConnection:
    """
    SQLAlchemy 기반의 Read-only 데이터베이스 연결 관리자.
    """
    def __init__(self, connection_string: str = "sqlite:///vibesql_demo.db"):
        self.engine = create_engine(
            connection_string,
            connect_args={"timeout": 10} if "sqlite" in connection_string else {},
            pool_pre_ping=True
        )
        self.SessionLocal = sessionmaker(bind=self.engine)

    def get_schema_info(self, relevant_tables: Optional[List[str]] = None) -> str:
        """
        데이터베이스의 테이블 및 컬럼 정보를 반환함. 
        relevant_tables가 주어지면 해당 테이블 정보만 반환하여 토큰을 절약함.
        """
        inspector = inspect(self.engine)
        schema_info = []
        
        target_tables = relevant_tables if relevant_tables else inspector.get_table_names()

        for table_name in target_tables:
            try:
                columns = inspector.get_columns(table_name)
                col_desc = ", ".join([f"{c['name']} ({c['type']})" for c in columns])
                schema_info.append(f"Table: {table_name}\nColumns: {col_desc}")
            except Exception:
                continue
        
        return "\n\n".join(schema_info)

    def execute_read_query(self, sql: str) -> List[Dict[str, Any]]:
        """
        SQL 쿼리를 실행하고 결과를 딕셔너리 리스트로 반환함 (Read-only).
        """
        session = self.SessionLocal()
        try:
            result = session.execute(text(sql))
            columns = result.keys()
            data = [dict(zip(columns, row)) for row in result]
            return data
        except SQLAlchemyError as e:
            # 에러 발생 시 원본 예외와 메시지 반환 (Self-Correction에서 활용)
            raise e
        finally:
            session.close()
