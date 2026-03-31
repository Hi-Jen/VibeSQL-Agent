# ⚡ VibeSQL-Agent

**VibeSQL-Agent**는 자연어(한국어) 질문을 안전한 SQL로 변환하고 실행하는 사내망 특화 LLM 에이전트입니다. LLM의 환각(Hallucination)과 데이터 파괴를 방지하는 **'안전 가드레일'**과 **'Self-Correction'** 루프, 그리고 데이터 분석을 위한 **'CSV 익스포트'** 기능을 핵심으로 제공합니다.

---

## 🚀 주요 기능 (Phase 2 완료)

### 1. 🧠 고정밀 SQL 생성 (Few-shot Precision)
- **지능형 예시 주입**: 시스템 프롬프트에 JOIN, GROUP BY, 집계 함수 등이 포함된 실무형 쿼리 페어를 학습시켜 복합 질문에 대한 정확도를 극대화했습니다.
- **Dynamic Schema**: 질문에 필요한 테이블만 선별적으로 참조하여 토큰 효율성을 높이고 정확한 컬럼 매핑을 수행합니다.

### 2. 📊 데이터 분석 및 익스포트 (CSV Export)
- **인터랙티브 저장**: 쿼리 결과 출력 후 즉시 CSV 파일로 저장할 수 있는 인터페이스를 제공합니다.
- **엑셀 호환성**: `utf-8-sig` 인코딩을 적용하여 엑셀에서 파일 오픈 시 한글이 깨지는 문제를 완벽히 해결했습니다.
- **자동 파일 관리**: `output/` 폴더에 타임스탬프 기반으로 고유한 파일명을 자동 생성합니다.

### 3. 🛡️ 안전 가드레일 (Safe Guardrails)
- **위험 쿼리 차단**: `DELETE`, `DROP` 등 데이터 변조 쿼리를 사전에 차단하며, 오직 `SELECT`와 `WITH` 구문만 실행 허용합니다.
- **자동 수정 루프**: SQL 에러 발생 시 에러 메시지를 LLM에 피드백하여 최대 3회까지 스스로 쿼리를 수정하고 재시도합니다.

---

## 💡 추천 테스트 질문 (Recommended Questions)

에이전트의 성능을 확인하기 위해 다음 질문들을 입력해 보세요:

| 레벨 | 질문 예시 | 핵심 기술 |
| :--- | :--- | :--- |
| **Lv 1. 기초** | "전체 직원 목록 보여줘" | Simple SELECT |
| **Lv 2. 관계** | "부서별 이름과 소속 직원 명단을 알려줘" | **Inner Join** |
| **Lv 3. 통계** | "부서별 평균 연봉이 높은 순서대로 정렬해줘" | **Group By + AVG** |
| **Lv 4. 복합** | "2023년 이후 입사자 중 개발팀원의 이름과 이메일은?" | **Filter + Join** |
| **Lv 5. 분석** | "가장 많은 연봉을 받는 상위 3명의 상세 정보를 뽑아줘" | Order By + Limit |

---

## 📂 디렉토리 구조

```text
VibeSQL-Agent/
├── config/
│   └── dictionary.yaml      # 도메인 용어 사전 (Semantic Layer)
├── output/                  # [NEW] CSV 익스포트 결과물 저장 (Git 제외)
├── src/
│   ├── core/
│   │   ├── engine.py        # Few-shot 및 Self-Correction 코어
│   │   ├── guardrails.py    # SQL 안전 검증 로직
│   │   └── dictionary.py    # YAML 사전 파싱
│   ├── db/
│   │   └── connection.py    # DB 연동 및 스키마 추출
│   └── utils/
│       └── export.py        # CSV 내보내기 유틸리티
├── tests/                   # 단위 테스트 (Pytest)
├── .env                     # GOOGLE_API_KEY 및 MODEL_NAME 설정
├── main.py                  # CLI 진입점 (대화형 루프 및 Export 지원)
└── requirements.txt         # 프로젝트 의존성
```

---

## ⚙️ 설치 및 실행

### 1. 환경 설정
`.env` 파일을 생성하고 발급받은 Google API Key를 입력합니다.
```env
GOOGLE_API_KEY=your_google_api_key_here
MODEL_NAME=gemini-1.5-flash
```

### 2. 의존성 설치 및 실행
```bash
# 의존성 설치
pip install -r requirements.txt

# 실행
python main.py
```

---

## ✅ 안정성 검증

현재 가이드라인 및 익스포트 기능을 포함한 모든 단위 테스트가 통과되었습니다.
```bash
python -m pytest tests/
# 결과: 27 passed
```
