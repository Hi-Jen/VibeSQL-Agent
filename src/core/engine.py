import re
from typing import Dict, Any, List, Optional
from sqlalchemy import inspect
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.core.guardrails import SQLGuardrail
from src.db.connection import DatabaseConnection
from src.core.dictionary import BaseDictionary, YamlDictionary

class VibeSQLEngine:
    """
    VibeSQL-Agent의 핵심 엔진.
    자연어 입력을 받아 용어 사전을 참조하고, 안전한 SQL을 생성 및 검증함.
    Self-Correction 루프를 통해 에러 발생 시 자동으로 수정을 시도함.
    """
    def __init__(self, 
                 dictionary: BaseDictionary, 
                 db_connection: DatabaseConnection,
                 model_name: str = "gpt-4-turbo",
                 max_retries: int = 3):
        self.dictionary = dictionary
        self.db = db_connection
        self.guardrail = SQLGuardrail()
        self.max_retries = max_retries
        
        # LLM 초기화 (API Key는 환경변수에서 로드됨)
        self.llm = ChatOpenAI(model=model_name, temperature=0)

    def _parse_llm_output(self, llm_output: str) -> Dict[str, str]:
        """
        LLM의 응답 텍스트에서 SQL과 해설을 추출함.
        마크다운 코드 블록이나 특정 태그를 파싱.
        """
        sql_match = re.search(r"```sql\s*(.*?)\s*```", llm_output, re.DOTALL | re.IGNORECASE)
        if not sql_match:
            # sql 블록이 없는 경우 전체 텍스트에서 첫 번째 SELECT/WITH 찾기 시도
            sql_match = re.search(r"(SELECT|WITH|UPDATE|DELETE|INSERT|CREATE|DROP|ALTER).*?;?", llm_output, re.DOTALL | re.IGNORECASE)
        
        sql = sql_match.group(1).strip() if sql_match else ""
        
        # 해설 추출 (SQL 블록 제외한 나머지 텍스트)
        explanation = llm_output.replace(sql_match.group(0) if sql_match else "", "").strip()
        # 불필요한 마크다운 기호 제거
        explanation = re.sub(r"```(sql)?", "", explanation).strip()
        
        return {"sql": sql, "explanation": explanation}

    def _get_relevant_tables(self, natural_language: str) -> Optional[List[str]]:
        """
        사용자 질문에서 키워드를 추출하여 연관된 테이블만 선별함 (토큰 최적화).
        """
        inspector = inspect(self.db.engine)
        all_tables = inspector.get_table_names()
        
        relevant = []
        for table in all_tables:
            # 단순 키워드 매칭 (임베딩 기반 RAG 도입 전 단계)
            if table.lower() in natural_language.lower():
                relevant.append(table)
        
        # TODO: 사용자의 자연어 질문을 보고 필요한 테이블 목록을 LLM이 먼저 고르게 하는 로직 추가 가능
        return relevant if relevant else None

    def build_prompt_with_context(self, 
                                 natural_language: str, 
                                 department: str, 
                                 error_feedback: Optional[str] = None) -> str:
        """
        부서별 용어 사전 컨텍스트와 동적으로 선택된 DB 스키마 정보를 LLM 프롬프트에 주입함.
        """
        relevant_tables = self._get_relevant_tables(natural_language)
        schema_context = self.db.get_schema_info(relevant_tables)
        dictionary_context = self.dictionary.get_context_string(department)
        
        prompt = f"""
역할: {department} 부서의 전문 데이터 분석가 (SQLD 수준)
목표: 사용자의 자연어 질문을 PostgreSQL SQL 쿼리로 변환하고, 그 쿼리가 무엇을 의미하는지 한 문장으로 해설하라.

[1] 데이터베이스 스키마 정보 (필요한 테이블만 선별됨):
{schema_context}

[2] 사내 용어 사전 (Semantic Layer):
{dictionary_context}

[3] 지시사항:
1. 반드시 위의 스키마 정보에 있는 테이블과 컬럼만 사용할 것. (존재하지 않는 컬럼 사용 금지)
2. 용어 사전에 정의된 조건이나 계산식을 쿼리에 정확히 반영할 것.
3. 결과물 형식:
   - SQL 쿼리는 반드시 ```sql ... ``` 블록 안에 작성할 것.
   - 쿼리에 대한 자연어 해설은 SQL 블록 바로 뒤에 한 문장으로 작성할 것.

질문: {natural_language}
"""
        if error_feedback:
            prompt += f"""
[4] 에러 피드백 (이전 시도 실패):
이전 시도에서 다음 에러가 발생했습니다: "{error_feedback}"
위 에러를 참고하여 SQL 문법이나 컬럼명을 다시 확인하고 수정한 SQL을 출력하라.
"""
        return prompt

    def generate_and_execute(self, natural_language: str, department: str = "marketing") -> Dict[str, Any]:
        """
        LLM을 통해 SQL 및 해설을 생성하고, 검증 후 실행함. 에러 발생 시 Self-Correction 루프를 실행함.
        """
        retry_count = 0
        error_feedback = None
        last_sql = ""
        explanation = ""

        while retry_count < self.max_retries:
            # 1. 프롬프트 생성 (에러 피드백 포함)
            prompt_text = self.build_prompt_with_context(natural_language, department, error_feedback)
            
            # 2. SQL 및 해설 생성 (LangChain LLM 호출)
            try:
                # StrOutputParser를 사용하여 문자열 결과 획득
                response = self.llm.invoke(prompt_text)
                llm_output = response.content
                
                # 출력 파싱 (SQL 블록 및 해설 분리)
                parsed = self._parse_llm_output(llm_output)
                generated_sql = parsed["sql"]
                explanation = parsed["explanation"]
                
                if not generated_sql:
                    raise ValueError("LLM이 유효한 SQL을 생성하지 못했습니다.")
                
            except Exception as e:
                error_feedback = f"LLM 호출/파싱 에러: {str(e)}"
                print(f"LLM Error (Attempt {retry_count + 1}): {error_feedback}")
                retry_count += 1
                continue
            
            last_sql = generated_sql

            # 3. 안전 장치 (Guardrail) 검증
            try:
                safe_sql = self.guardrail.validate_query(generated_sql)
            except Exception as e:
                return {
                    "error": f"Guardrail Block: {str(e)}", 
                    "sql": generated_sql, 
                    "explanation": f"위험 감지: {explanation}",
                    "retry_count": retry_count
                }

            # 4. SQL 실행
            try:
                results = self.db.execute_read_query(safe_sql)
                return {
                    "sql": safe_sql,
                    "explanation": explanation,
                    "results": results,
                    "count": len(results),
                    "retry_count": retry_count,
                    "success": True
                }
            except Exception as e:
                error_feedback = str(e)
                print(f"Attempt {retry_count + 1} failed: {error_feedback}")
                retry_count += 1
                continue

        return {
            "error": "최대 리트라이 횟수를 초과했습니다.",
            "last_error": error_feedback,
            "sql": last_sql,
            "explanation": explanation,
            "retry_count": retry_count,
            "success": False
        }

if __name__ == "__main__":
    # 간단한 통합 테스트용 예시
    db = DatabaseConnection("sqlite:///vibesql_demo.db")
    dict_layer = YamlDictionary("config/dictionary.yaml")
    engine = VibeSQLEngine(dictionary=dict_layer, db_connection=db)
    
    result = engine.generate_and_execute("지난 달 활성유저 보여줘", "marketing")
    print(f"\nFinal Result:\n{result}")
