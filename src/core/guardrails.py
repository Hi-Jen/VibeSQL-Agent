import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Where, Comparison
from sqlparse.tokens import Keyword, DML, DDL

class SQLGuardrail:
    FORBIDDEN_KEYWORDS = {"UPDATE", "DELETE", "DROP", "TRUNCATE", "ALTER", "INSERT", "CREATE"}

    @staticmethod
    def validate_query(sql: str) -> str:
        """
        SQL 쿼리를 검증하고 안전한 쿼리로 변환하거나 에러를 발생시킴.
        """
        parsed = sqlparse.parse(sql)
        if not parsed:
            raise ValueError("유효하지 않은 SQL 형식입니다.")

        statement = parsed[0]

        # 1. DML/DDL 변조 금지 체크
        for token in statement.tokens:
            if token.ttype in (DML, DDL) and token.value.upper() in SQLGuardrail.FORBIDDEN_KEYWORDS:
                raise PermissionError(f"허용되지 않은 명령어 감지: {token.value}")

        # 2. Cartesian Product 체크 (JOIN 조건 누락)
        # 단순 SELECT일 경우 FROM 뒤에 여러 테이블이 나열될 때 WHERE나 JOIN ON이 있는지 확인
        if SQLGuardrail._is_cartesian_product(statement):
            raise ValueError("JOIN 조건이 누락된 Cartesian Product가 감지되었습니다.")

        # 3. LIMIT 1000 강제 적용
        sql_normalized = sql.strip().rstrip(';')
        if "LIMIT" not in sql_normalized.upper():
            sql_normalized += " LIMIT 1000"
        
        return sql_normalized

    @staticmethod
    def _is_cartesian_product(statement) -> bool:
        """
        간이 Cartesian Product 체크 로직.
        FROM 절에 테이블이 2개 이상일 때 JOIN 조건이 없으면 위험군으로 판단.
        """
        has_from = False
        tables_count = 0
        has_where_or_join = False

        for token in statement.tokens:
            if token.ttype is Keyword and token.value.upper() == "FROM":
                has_from = True
            elif has_from:
                if isinstance(token, IdentifierList):
                    # IdentifierList 내의 실제 Identifier 개수 합산
                    tables_count += len([i for i in token.get_identifiers() if isinstance(i, Identifier)])
                elif isinstance(token, Identifier):
                    tables_count += 1
                elif isinstance(token, Where) or (token.ttype is Keyword and "JOIN" in token.value.upper()):
                    has_where_or_join = True
                    break
                elif token.ttype is Keyword and token.value.upper() in ("GROUP", "ORDER", "LIMIT", "HAVING"):
                    # FROM 절이 끝나는 지점들
                    break
        
        # 테이블이 2개 이상인데 WHERE나 JOIN 조건이 없으면 위험군
        return tables_count > 1 and not has_where_or_join

if __name__ == "__main__":
    # Test cases
    guard = SQLGuardrail()
    try:
        print(guard.validate_query("SELECT * FROM users"))
        print(guard.validate_query("SELECT * FROM users, orders"))  # Should fail
    except Exception as e:
        print(f"Error: {e}")

    try:
        print(guard.validate_query("DELETE FROM users"))  # Should fail
    except Exception as e:
        print(f"Error: {e}")
