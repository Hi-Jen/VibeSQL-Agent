# VibeSQL-Agent 프로젝트 진행 현황

## 1. 아키텍처 리팩토링 [x]
- [x] `src/` 폴더 기반 패키지 구조로 변경
- [x] `Dictionary` 인터페이스 설계 (YAML/DB 확장성 고려)
- [x] `connection.py` 모듈화 (SQLite/PostgreSQL 대응)

## 2. SQLD Brain 고도화 (LLM Integration) [x]
- [x] **LangChain 실연동**: 하드코딩 `if-else` 제거 및 LLM API(OpenAI/Anthropic) 연결
- [x] **Output Parser 구현**: SQL 블록 및 자연어 해설 정밀 추출
- [x] **AI-powered Table Selection**: 단순 매칭에서 LLM 기반 테이블 선별로 고도화 (기초 로직 적용)
- [x] **Self-Correction (자동 수정) 루프** 구현
- [x] 에러 피드백 기반 리트라이 로직 검증

## 3. 지능형 최적화 & UX [x]
- [x] **동적 스키마 로딩 (Token Optimization)**: 질문 연관 테이블 선별
- [x] **쿼리 자연어 해설 (Explanation)** 기능 추가
- [x] 가드레일 강화 (TDD 기반 엣지케이스 추가)

## 4. Slack & Async Integration [x]
- [x] FastAPI 기반 비동기 슬랙 봇 서버 구축 (Background Tasks 프레임워크)
- [x] Slack Interactive 메시지 (구조 설계 완료)
- [x] 결과 파일(CSV) 업로드 연동 (Util 연동 완료)
