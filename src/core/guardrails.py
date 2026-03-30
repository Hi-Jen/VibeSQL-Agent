"""
guardrails.py - SQL 안전 가드레일 모듈

sqlparse를 사용하여 LLM이 생성한 SQL을 분석하고,
데이터 변조(DELETE, DROP 등)를 사전에 차단합니다.
오직 SELECT와 WITH(CTE)만 허용합니다.
"""

import re
import sqlparse
from sqlparse.sql import Statement
from sqlparse.tokens import Keyword, DML, DDL


# 데이터를 변조하거나 파괴할 수 있는 위험 키워드 목록
_FORBIDDEN_KEYWORDS: set[str] = {
    "DELETE", "DROP", "UPDATE", "INSERT",
    "ALTER", "TRUNCATE", "CREATE", "REPLACE",
    "GRANT", "REVOKE", "EXEC", "EXECUTE",
    "MERGE", "CALL",
}

# 허용되는 최상위 명령어 (SELECT, WITH만 허용)
_ALLOWED_STATEMENT_TYPES: set[str] = {"SELECT", "WITH"}

# LIMIT 절이 없을 때 자동 추가할 기본값
DEFAULT_LIMIT = 1000


def validate_sql(raw_sql: str) -> str:
    """
    SQL 쿼리의 안전성을 검증하고, LIMIT이 없으면 자동 추가하여 반환합니다.

    Args:
        raw_sql: LLM이 생성한 원본 SQL 문자열

    Returns:
        안전 검증 및 LIMIT이 추가된 SQL 문자열

    Raises:
        ValueError: 위험한 키워드가 발견되거나 허용되지 않는 구문일 때
    """
    if not raw_sql or not raw_sql.strip():
        raise ValueError("빈 SQL 쿼리는 실행할 수 없습니다.")

    cleaned_sql = _strip_markdown_fences(raw_sql)
    _check_forbidden_keywords(cleaned_sql)
    _check_statement_type(cleaned_sql)
    safe_sql = _ensure_limit(cleaned_sql)

    return safe_sql


def _strip_markdown_fences(sql: str) -> str:
    """
    LLM이 마크다운 코드 블록으로 감싼 경우 제거합니다.
    예: ```sql\nSELECT ...\n``` → SELECT ...
    """
    stripped = sql.strip()

    # ```sql ... ``` 또는 ``` ... ``` 패턴 제거
    pattern = r"^```(?:sql)?\s*\n?(.*?)\n?\s*```$"
    match = re.match(pattern, stripped, re.DOTALL | re.IGNORECASE)
    if match:
        stripped = match.group(1).strip()

    return stripped


def _check_forbidden_keywords(sql: str) -> None:
    """
    sqlparse로 토큰을 분석하여 위험 키워드를 탐지합니다.
    단순 문자열 매칭이 아닌 토큰 레벨 분석으로 오탐을 줄입니다.
    """
    parsed = sqlparse.parse(sql)

    for statement in parsed:
        for token in statement.flatten():
            # DML/DDL 토큰 타입이거나, Keyword 타입 중 금지 목록에 해당하면 차단
            word = token.ttype
            value_upper = token.value.upper().strip()

            if word in (DML, DDL) and value_upper in _FORBIDDEN_KEYWORDS:
                raise ValueError(
                    f"🚫 위험 SQL 감지: '{value_upper}' 구문은 허용되지 않습니다. "
                    f"데이터 보호를 위해 SELECT/WITH 쿼리만 실행할 수 있습니다."
                )

            if word is Keyword and value_upper in _FORBIDDEN_KEYWORDS:
                raise ValueError(
                    f"🚫 위험 SQL 감지: '{value_upper}' 키워드가 발견되었습니다. "
                    f"읽기 전용 쿼리만 허용됩니다."
                )


def _check_statement_type(sql: str) -> None:
    """
    SQL 문의 최상위 구문이 SELECT 또는 WITH(CTE)인지 확인합니다.
    """
    parsed = sqlparse.parse(sql)

    if not parsed:
        raise ValueError("SQL 파싱에 실패했습니다.")

    # 첫 번째 의미 있는 토큰으로 구문 타입 판별
    first_statement: Statement = parsed[0]
    first_token = first_statement.token_first(skip_cm=True, skip_ws=True)

    if first_token is None:
        raise ValueError("유효한 SQL 구문을 찾을 수 없습니다.")

    first_word = first_token.value.upper().strip()

    if first_word not in _ALLOWED_STATEMENT_TYPES:
        raise ValueError(
            f"🚫 허용되지 않는 구문: '{first_word}'. "
            f"오직 SELECT와 WITH(CTE) 쿼리만 실행할 수 있습니다."
        )


def _ensure_limit(sql: str) -> str:
    """
    쿼리에 LIMIT 절이 없다면 기본 LIMIT을 추가합니다.
    이미 LIMIT이 있으면 원본 그대로 반환합니다.
    """
    # 세미콜론 제거 후 LIMIT 존재 여부 확인
    trimmed = sql.rstrip().rstrip(";").rstrip()

    # 정규식으로 LIMIT 절 존재 여부 확인 (서브쿼리 내부의 LIMIT은 무시하기 어려우므로 최외곽만 체크)
    has_limit = re.search(
        r"\bLIMIT\s+\d+\s*$",
        trimmed,
        re.IGNORECASE
    )

    if has_limit:
        return sql.rstrip().rstrip(";")

    return f"{trimmed}\nLIMIT {DEFAULT_LIMIT}"
