# ⚡ VibeSQL-Agent

**VibeSQL-Agent**는 자연어(한국어) 질문을 안전한 SQL로 변환하고 실행하는 사내망 특화 LLM 에이전트입니다. LLM의 환각(Hallucination)과 데이터 파괴(DELETE, DROP 등)를 방지하는 **'안전 가드레일'**과 에러 발생 시 스스로 쿼리를 수정하는 **'Self-Correction'** 루프를 핵심 기능으로 제공합니다.

---

## 🚀 주요 기능

### 1. 🛡️ 안전 가드레일 (Safe Guardrails)
- **위험 쿼리 차단**: `DELETE`, `DROP`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE` 등 데이터 변조/삭제 쿼리를 `sqlparse` 토큰 분석을 통해 사전에 완벽히 차단합니다.
- **읽기 전용 강제**: 오직 `SELECT`와 `WITH`(CTE) 구문만 실행할 수 있습니다.
- **대량 데이터 방지**: 쿼리에 `LIMIT` 절이 없을 경우 성능 보호를 위해 자동으로 `LIMIT 1000`을 추가합니다.

### 2. 🔄 자기 교정 루프 (Self-Correction Loop)
- **자동 에러 수정**: SQL 실행 중 구문 에러가 발생하면, 에러 메시지를 LLM에 피드백하여 최대 3회까지 스스로 쿼리를 수정하고 재시도합니다.

### 3. 📖 도메인 사전 (Semantic Layer)
- **한국어 용어 매핑**: `config/dictionary.yaml`을 통해 "직원", "연봉", "부서명" 등 현업에서 사용하는 한국어 용어를 실제 DB 테이블 및 컬럼명과 정확하게 연결합니다.

### 4. 📊 스키마 자동 추출
- **컨텍스트 주입**: DB의 모든 테이블 구조(컬럼명, 데이터 타입, PK/FK 관계)를 자동으로 추출하여 LLM 프롬프트에 제공함으로써 변환 정확도를 극대화합니다.

---

## 🛠️ 기술 스택

- **Core**: Python 3.12+
- **LLM Framework**: LangChain, Google Gemini 1.5 Flash
- **Database**: SQLite (Demo), SQLAlchemy
- **SQL Parser**: sqlparse
- **UI**: CLI (tabulate 기반 결과 출력)

---

## 📂 디렉토리 구조

```text
VibeSQL-Agent/
├── config/
│   └── dictionary.yaml      # 도메인 용어 사전 (Semantic Layer)
├── src/
│   ├── core/
│   │   ├── engine.py        # LLM 코어 및 Self-Correction 루프
│   │   ├── guardrails.py    # SQL 안전 검증 로직
│   │   └── dictionary.py    # YAML 사전 파싱
│   ├── db/
│   │   └── connection.py    # DB 연동 및 스키마 추출
│   └── utils/
│       └── export.py        # CSV 내보내기 유틸리티
├── tests/                   # 단위 테스트 (Pytest)
├── .env                     # GOOGLE_API_KEY 설정
├── main.py                  # CLI 진입점
└── requirements.txt         # 프로젝트 의존성
```

---

## ⚙️ 설치 및 실행

### 1. 환경 설정
`.env` 파일을 생성하고 Google API Key를 입력합니다.
```env
GOOGLE_API_KEY=your_google_api_key_here
```

### 2. 의존성 설치
```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 실행
```bash
python main.py
```

---

## ✅ 테스트 결과

현재 26개의 단위 테스트가 작성되어 있으며, 가드레일 및 DB 연동의 안정성을 보장합니다.
```bash
python -m pytest tests/
# 결과: 26 passed
```

---

## 📝 향후 계획 (Phase 2)
- 결과 데이터 CSV 다운로드 기능 활성화
- 부서별 맞춤형 사전 강화
- Streamlit 기반 웹 대시보드 구현
