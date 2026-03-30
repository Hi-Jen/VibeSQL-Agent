import pytest
from unittest.mock import MagicMock
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from src.core.engine import VibeQLEngine
from src.db.connection import DatabaseManager

def test_engine_context_preservation_on_error():
    """에러 발생 시 AIMessage가 대화 내역에 포함되는지 검증합니다."""
    # Mock 설정
    mock_db = MagicMock(spec=DatabaseManager)
    mock_db.get_schema_info.return_value = "Table: employees"
    mock_db.execute_query.side_effect = [Exception("Syntax Error"), [{"id": 1}]]
    
    engine = VibeQLEngine(db_manager=mock_db)
    
    # LLM 응답 Mocking
    mock_response_1 = MagicMock()
    mock_response_1.content = "SELECT * FROM employees"
    
    mock_response_2 = MagicMock()
    mock_response_2.content = "SELECT id FROM employees"
    
    engine.llm.invoke = MagicMock(side_effect=[mock_response_1, mock_response_2])
    
    # 실행
    result = engine.generate_and_execute("직원 목록 보여줘")
    
    # 검증: invoke가 호출될 때 전달된 메시지 확인
    # 첫 번째 호출은 [System, Human]
    # 두 번째 호출(Retry)은 [System, Human, AI, Human]
    calls = engine.llm.invoke.call_args_list
    retry_messages = calls[1][0][0]
    
    assert len(retry_messages) == 4
    assert isinstance(retry_messages[0], SystemMessage)
    assert isinstance(retry_messages[1], HumanMessage)
    assert isinstance(retry_messages[2], AIMessage) # [핵심] AI의 실패한 쿼리가 포함되어야 함
    assert retry_messages[2].content == "SELECT * FROM employees"
    assert isinstance(retry_messages[3], HumanMessage)
    assert "Syntax Error" in retry_messages[3].content

def test_extract_relevant_tables_logic():
    """질문에 따라 연관된 테이블만 추출되는지 검증합니다."""
    engine = VibeQLEngine()
    
    # 1. '직원' 키워드가 있을 때
    tables_employees = engine._extract_relevant_tables("우리 회사 직원 리스트")
    assert "employees" in tables_employees
    
    # 2. '부서' 키워드가 있을 때
    tables_depts = engine._extract_relevant_tables("부서별 위치 알려줘")
    assert "departments" in tables_depts
    
    # 3. 키워드가 없을 때 (전체 스키마 반환을 위해 빈 리스트)
    tables_none = engine._extract_relevant_tables("안녕?")
    assert len(tables_none) == 0
