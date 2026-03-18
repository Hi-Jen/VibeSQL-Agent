# VibeSQL-Agent 🚀

**VibeSQL-Agent**는 현업 실무자가 자연어(Vibe)로 질문하면 사내 정의된 '용어 사전(Semantic Dictionary)'을 참조하여 정확하고 안전한 SQL을 실행하고 결과를 제공하는 지능형 데이터 분석 에이전트입니다.

## 🌟 주요 특징

- **Semantic Layer**: 부서별 전용 용어 사전을 통해 비즈니스 용어를 SQL 조건으로 자동 매핑.
- **SQLD Brain**: DB 스키마 자동 추출 및 LLM 프롬프트 주입으로 고도의 쿼리 생성.
- **Self-Correction**: SQL 실행 에러 발생 시 스스로 코드를 수정하는 자가 치유 루프.
- **Token Optimization**: 대규모 스키마 대응을 위한 동적 테이블 테이블 선별 로직.
- **Safety Guardrails**: DML/DDL 차단, Cartesian Product 감지, LIMIT 자동 주입.
- **Async Slack Interaction**: FastAPI와 BackgroundTasks를 이용한 비동기 슬랙 봇 지원.
- **Hallucination Explanation**: 쿼리 생성 의도를 자연어로 해설하여 신뢰도 확보.

## 🏗️ 프로젝트 구조

```text
VibeSQL-Agent/
├── config/              # 설정 파일 (dictionary.yaml 등)
├── src/
│   ├── api/            # 외부 인터페이스 (Slack API 등)
│   ├── core/           # 핵심 엔진 (Engine, Guardrails, Dictionary)
│   ├── db/             # 데이터베이스 연결 및 관리
│   └── utils/          # 유틸리티 (데이터 내보내기 등)
├── tests/              # TDD를 위한 테스트 케이스
├── requirements.txt    # 의존성 패키지 목록
└── README.md
```

## 🚀 시작하기

### 1. 환경 설정
```bash
pip install -r requirements.txt
```

### 2. 테스트 실행
```bash
# 가드레일 테스트
$env:PYTHONPATH = "."; python tests/test_guardrails.py

# 고도화 기능 테스트 (해설, 셀프 코렉션 등)
$env:PYTHONPATH = "."; python tests/test_advanced_features.py
```

## 🛠️ 기술 스택
- **Language**: Python 3.11+
- **LLM Framework**: LangChain
- **Analysis**: sqlparse (AST 기반 안전 검증)
- **Database**: SQLAlchemy (Read-only)
- **Interface**: Slack SDK, FastAPI

## 📝 라이선스
MIT License
