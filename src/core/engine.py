"""
engine.py - LLM 에이전트 코어 엔진

LangChain + Gemini 1.5 Flash를 사용하여
자연어 → SQL 변환 → 실행 → Self-Correction 루프를 구현합니다.
"""

import os
import logging
from typing import Any

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from src.core.guardrails import validate_sql
from src.core.dictionary import get_dictionary_context
from src.db.connection import DatabaseManager

# 환경 변수 로드
load_dotenv()

logger = logging.getLogger(__name__)

# Self-Correction 최대 재시도 횟수
MAX_RETRY = 3


def _build_system_prompt(schema_info: str, dictionary_context: str) -> str:
    """
    LLM에게 전달할 시스템 프롬프트를 조합합니다.
    역할 부여, DB 스키마, 도메인 사전, 출력 형식 지시를 포함합니다.
    """
    return f"""너는 사내 데이터 분석가다. 사용자의 자연어 질문을 분석하여 정확한 SQL 쿼리를 작성해라.

## 규칙
1. 반드시 SELECT 또는 WITH(CTE)로 시작하는 읽기 전용 쿼리만 작성할 것.
2. DELETE, DROP, UPDATE, INSERT 등 데이터 변조 쿼리는 절대 작성하지 마라.
3. SQL만 반환하라. 마크다운 코드 블록(```)으로 감싸지 마라.
4. 설명이나 부가 텍스트 없이 순수 SQL만 출력하라.
5. 한국어 용어는 아래 도메인 사전을 참고하여 올바른 테이블/컬럼명으로 변환하라.
6. 테이블 조인 시 적절한 JOIN 조건을 명시하라.

## DB 스키마
{schema_info}

## 도메인 용어 사전
{dictionary_context}
"""


class VibeQLEngine:
    """
    자연어 → SQL 변환 및 실행 에이전트.
    생성된 SQL이 에러를 일으키면 에러 메시지를 LLM에 피드백하여
    최대 {MAX_RETRY}회까지 자동 수정을 시도합니다.
    """

    def __init__(
        self,
        db_manager: DatabaseManager | None = None,
        model_name: str | None = None,
    ):
        """
        Args:
            db_manager: DatabaseManager 인스턴스. None이면 인메모리 데모 DB 생성.
            model_name: Gemini 모델명. None이면 환경 변수에서 로드.
        """
        # DB 매니저 초기화
        self.db = db_manager or DatabaseManager()
        if db_manager is None:
            self.db.initialize_demo_db()

        # LLM 초기화
        resolved_model = model_name or os.getenv("MODEL_NAME", "gemini-1.5-flash")
        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY가 설정되지 않았습니다. "
                ".env 파일 또는 환경 변수를 확인하세요."
            )

        self.llm = ChatGoogleGenerativeAI(
            model=resolved_model,
            google_api_key=api_key,
            temperature=0,  # SQL 생성에는 결정적 출력이 적합
        )

        # 프롬프트 구성 요소 로드
        self._schema_info = self.db.get_schema_info()
        self._dict_context = get_dictionary_context()
        self._system_prompt = _build_system_prompt(
            self._schema_info, self._dict_context
        )

    def generate_sql(self, natural_language: str) -> str:
        """
        자연어를 SQL로 변환합니다 (실행은 하지 않음).

        Args:
            natural_language: 사용자의 한국어 질문

        Returns:
            가드레일을 통과한 안전한 SQL 문자열
        """
        messages = [
            SystemMessage(content=self._system_prompt),
            HumanMessage(content=natural_language),
        ]

        response = self.llm.invoke(messages)
        raw_sql = response.content.strip()

        # 가드레일 검증 (위험 키워드 차단 + LIMIT 자동 추가)
        safe_sql = validate_sql(raw_sql)
        return safe_sql

    def generate_and_execute(
        self, natural_language: str
    ) -> dict[str, Any]:
        """
        자연어 → SQL 변환 → 실행 → Self-Correction 루프.

        에러 발생 시 LLM에게 에러 메시지를 피드백하여
        최대 MAX_RETRY회까지 쿼리를 자동 수정합니다.

        Args:
            natural_language: 사용자의 한국어 질문

        Returns:
            {
                "question": 원본 질문,
                "sql": 최종 실행된 SQL,
                "result": 쿼리 결과 리스트,
                "retries": 재시도 횟수,
                "success": 성공 여부,
                "error": 에러 메시지 (실패 시)
            }
        """
        messages = [
            SystemMessage(content=self._system_prompt),
            HumanMessage(content=natural_language),
        ]

        last_error = None
        final_sql = None

        for attempt in range(MAX_RETRY + 1):
            try:
                # 1단계: LLM에게 SQL 생성 요청
                response = self.llm.invoke(messages)
                raw_sql = response.content.strip()
                logger.info(f"[시도 {attempt + 1}] 생성된 SQL:\n{raw_sql}")

                # 2단계: 가드레일 검증
                safe_sql = validate_sql(raw_sql)
                final_sql = safe_sql

                # 3단계: SQL 실행
                result = self.db.execute_query(safe_sql)

                return {
                    "question": natural_language,
                    "sql": safe_sql,
                    "result": result,
                    "retries": attempt,
                    "success": True,
                    "error": None,
                }

            except ValueError as e:
                # 가드레일 위반 → 재시도하지 않고 즉시 중단
                logger.warning(f"가드레일 위반: {e}")
                return {
                    "question": natural_language,
                    "sql": raw_sql if 'raw_sql' in dir() else None,
                    "result": [],
                    "retries": attempt,
                    "success": False,
                    "error": str(e),
                }

            except Exception as e:
                # SQL 실행 에러 → Self-Correction 피드백
                last_error = str(e)
                logger.warning(
                    f"[시도 {attempt + 1}] SQL 실행 실패: {last_error}"
                )

                if attempt < MAX_RETRY:
                    # 에러 메시지를 대화에 추가하여 LLM이 수정하도록 유도
                    correction_prompt = (
                        f"위 SQL을 실행했더니 다음 에러가 발생했다:\n"
                        f"에러: {last_error}\n\n"
                        f"이 에러를 해결한 수정된 SQL만 다시 작성해라. "
                        f"설명 없이 SQL만 출력하라."
                    )
                    messages.append(HumanMessage(content=correction_prompt))

        # 모든 재시도 실패
        return {
            "question": natural_language,
            "sql": final_sql,
            "result": [],
            "retries": MAX_RETRY,
            "success": False,
            "error": f"최대 재시도({MAX_RETRY}회) 초과. 마지막 에러: {last_error}",
        }
