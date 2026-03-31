"""
engine.py - LLM 에이전트 코어 엔진
"""

import os
import logging
import time
from typing import Any

from dotenv import load_dotenv
# 최신 버전 라이브러리 사용
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# 프로젝트 내부 모듈 (경로가 다를 경우 수정 필요)
try:
    from src.core.guardrails import validate_sql
    from src.core.dictionary import get_dictionary_context, load_dictionary
    from src.db.connection import DatabaseManager
except ImportError:
    # 경로 문제 방지를 위한 가상 임포트 (실제 환경에 맞게 유지하세요)
    pass

load_dotenv()
logger = logging.getLogger(__name__)
MAX_RETRY = 3

def _build_system_prompt(schema_info: str, dictionary_context: str) -> str:
    return f"""너는 사내 데이터 분석가다. 사용자의 자연어 질문을 분석하여 정확한 SQL 쿼리를 작성해라.

## 규칙
1. 반드시 SELECT 또는 WITH(CTE)로 시작하는 읽기 전용 쿼리만 작성할 것.
2. SQL만 반환하라. 마크다운 코드 블록(```)으로 감싸지 마라.
3. 한국어 용어는 아래 도메인 사전을 참고하여 올바른 테이블/컬럼명으로 변환하라.

## DB 스키마
{schema_info}

## 도메인 용어 사전
{dictionary_context}
"""

class VibeQLEngine:
    def __init__(
        self,
        db_manager: DatabaseManager | None = None,
        model_name: str | None = None,
    ):
        self.db = db_manager or DatabaseManager()
        if db_manager is None:
            self.db.initialize_demo_db()

        api_key = os.getenv("GOOGLE_API_KEY")
        # 환경변수에서 모델명을 가져오되, 기본값은 명확하게 지정
        # 기본값을 gemini-2.0-flash로 설정 (1.5는 2026년 기준 폐기됨)
        target_model = model_name or os.getenv("MODEL_NAME", "gemini-2.0-flash")

        if not api_key:
            raise ValueError("❌ GOOGLE_API_KEY가 설정되지 않았습니다.")

        self.llm = ChatGoogleGenerativeAI(
            model=target_model,
            google_api_key=api_key,
            temperature=0,
            max_retries=3,
        )

        self._dict_context = get_dictionary_context()

    def _extract_relevant_tables(self, natural_language: str) -> list[str]:
        try:
            dict_data = load_dictionary()
            domains = dict_data.get("domains", {})
            relevant_tables = set()
            for _, info in domains.items():
                synonyms = info.get("synonyms", {})
                for keyword, mapping in synonyms.items():
                    if keyword in natural_language and mapping.isidentifier():
                        relevant_tables.add(mapping)
            return list(relevant_tables)
        except:
            return []

    def generate_and_execute(self, natural_language: str) -> dict[str, Any]:
        relevant_tables = self._extract_relevant_tables(natural_language)
        schema_info = self.db.get_schema_info(table_names=relevant_tables or None)
        system_prompt = _build_system_prompt(schema_info, self._dict_context)
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=natural_language),
        ]

        last_error = None
        final_sql = None

        for attempt in range(MAX_RETRY + 1):
            try:
                response = self.llm.invoke(messages)
                raw_sql = response.content.strip()
                
                # 마크다운 정제 (LLM이 ```sql ... ``` 로 줄 경우 대비)
                clean_sql = raw_sql.replace("```sql", "").replace("```", "").strip()
                
                safe_sql = validate_sql(clean_sql)
                final_sql = safe_sql

                result = self.db.execute_query(safe_sql)

                return {
                    "question": natural_language,
                    "sql": safe_sql,
                    "result": result,
                    "retries": attempt,
                    "success": True,
                    "error": None,
                }

            except Exception as e:
                error_msg = str(e)
                last_error = error_msg
                logger.warning(f"[시도 {attempt + 1}] 에러: {error_msg}")

                # 404 NOT_FOUND는 설정 오류이므로 재시도 무의미 → 즉시 중단
                if "NOT_FOUND" in error_msg or "404" in error_msg:
                    logger.error(
                        "🛑 모델을 찾을 수 없습니다. "
                        ".env의 MODEL_NAME이 올바른지 확인하세요. "
                        "(예: gemini-2.0-flash, gemini-2.5-flash)"
                    )
                    break

                if attempt < MAX_RETRY:
                    if 'raw_sql' in locals():
                        messages.append(AIMessage(content=raw_sql))
                    messages.append(HumanMessage(content=f"에러 발생: {error_msg}\n수정된 SQL만 다시 작성해줘."))
                    time.sleep(2)
                else:
                    break

        # engine.py의 generate_and_execute 함수 마지막 return 부분
        return {
            "question": natural_language,
            "sql": final_sql,
            "result": [],
            "retries": attempt,  # 이 부분을 추가해야 main.py에서 에러가 안 납니다.
            "success": False,
            "error": f"최종 실패: {last_error}",
        }