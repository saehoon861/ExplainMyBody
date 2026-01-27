# ExplainMyBody LLM 프로젝트 온보딩 가이드

환영합니다, Serena! 이 문서는 ExplainMyBody LLM 프로젝트를 이해하고 개발에 참여하기 위한 가이드입니다.

---

## 📋 목차

1. [프로젝트 개요](#프로젝트-개요)
2. [빠른 시작](#빠른-시작)
3. [전체 아키텍처](#전체-아키텍처)
4. [데이터 플로우](#데이터-플로우)
5. [핵심 모듈 상세](#핵심-모듈-상세)
6. [데이터베이스 구조](#데이터베이스-구조)
7. [워크플로우 실행](#워크플로우-실행)
8. [코드 구조](#코드-구조)
9. [개발 가이드](#개발-가이드)
10. [문제 해결](#문제-해결)

---

## 프로젝트 개요

### 목적
InBody 측정 데이터를 기반으로:
1. **규칙 기반 분석**: BMI, 체지방률, 근육량을 분석하여 체형 분류 (Stage 2, 3)
2. **LLM 추천 생성**: 분석 결과와 측정 데이터를 바탕으로 개인 맞춤형 운동/식단 추천
3. **데이터 관리**: PostgreSQL 기반 사용자 건강 기록 및 리포트 관리

### 기술 스택
- **Python 3.11+**: 메인 언어
- **PostgreSQL + pgvector**: 데이터베이스 (JSONB, 향후 유사도 검색)
- **Pydantic**: 데이터 검증 및 타입 안전성
- **LLM APIs**: Claude (Anthropic), GPT (OpenAI), Ollama (로컬)
- **psycopg2**: PostgreSQL 드라이버

---

## 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론 (이미 있다면 생략)
cd /home/user/projects/ExplainMyBody/llm

# 의존성 설치
pip install -r requirements.txt

# PostgreSQL 실행 (Docker 권장)
docker run -d \
  --name explainmybody-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=explainmybody \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# .env 파일 확인/수정
cat .env
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/explainmybody
# ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...
```

### 2. 연결 테스트

```bash
# PostgreSQL 연결 확인
python -c "from database import Database; db = Database(); print('✅ OK' if db.test_connection() else '❌ FAIL')"

# 프로필 목록 확인
python main_workflow.py --list-profiles
```

### 3. 첫 실행

```bash
python main_workflow.py \
  --username "테스트유저" \
  --email "test@example.com" \
  --profile-id 1 \
  --model gpt-4o-mini
```

---

## 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                   사용자 입력                                │
│  (username, email, profile_id, model)                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              1️⃣ 회원가입/로그인                               │
│  UserAuthManager.register_or_login()                        │
│  - 이메일로 기존 사용자 확인                                  │
│  - 없으면 신규 회원가입, 있으면 로그인                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              2️⃣ OCR 데이터 추출 (시뮬레이션)                  │
│  InBodyAnalysisWorkflow.extract_ocr_data()                  │
│  - sample_profiles.json에서 프로필 로드                      │
│  - measurements 형식으로 변환                                 │
│    (성별, 나이, 신장, 체중, BMI, 체지방률, 골격근량 등)        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              3️⃣ 사용자 데이터 확인                            │
│  InBodyAnalysisWorkflow.get_user_confirmation()             │
│  - 실제로는 Frontend에서 사용자가 확인/수정                    │
│  - 지금은 시뮬레이션 (그대로 승인)                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              4️⃣ Stage 2, 3 계산                              │
│  InBodyAnalysisWorkflow.calculate_stages()                  │
│  - rule_based_bodytype 알고리즘 사용                         │
│  - BodyCompositionAnalyzer.analyze_full_pipeline()          │
│    • Stage 2: 근육보정체형 (표준형, 근육형, 비만형 등)         │
│    • Stage 3: 상하체밸런스 (표준형, 상체발달형, 하체발달형)    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              5️⃣ 데이터 병합                                   │
│  InBodyAnalysisWorkflow.merge_data()                        │
│  - OCR 데이터 + Stage 2, 3 결과 병합                         │
│  - 최종 measurements 생성                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              6️⃣ health_records DB 저장                       │
│  Database.save_health_record()                              │
│  - PostgreSQL에 JSONB 형식으로 저장                          │
│  - user_id, measurements, source, measured_at               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              7️⃣ LLM 분석 리포트 생성                          │
│  InBodyAnalysisWorkflow.generate_llm_report()               │
│  - DB에서 measurements 추출                                  │
│  - prompt_generator_measurements.py로 프롬프트 생성          │
│  - LLM 클라이언트 호출 (Claude/GPT/Ollama)                   │
│  - 자연어 리포트 생성                                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              8️⃣ analysis_reports DB 저장                     │
│  Database.save_analysis_report()                            │
│  - llm_output, model_version 저장                           │
│  - 리포트 ID 반환                                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              9️⃣ 결과 출력 및 파일 저장                        │
│  - 터미널에 리포트 출력                                       │
│  - outputs/ 폴더에 텍스트 파일 저장                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 데이터 플로우

### 입력 → 출력

```python
# 입력: sample_profiles.json
{
  "id": 1,
  "name": "이영희",
  "sex": "여자",
  "age": 28,
  "height_cm": 165.0,
  "weight_kg": 58.0,
  "bmi": 21.3,
  "fat_rate": 28.5,
  "smm": 22.0,
  "muscle_seg": {"왼팔": "표준", "오른팔": "표준", ...},
  "fat_seg": {"왼팔": "표준", "오른팔": "표준", ...}
}

        ↓ [OCR 추출 + 변환]

# measurements 형식
{
  "성별": "여자",
  "나이": 28,
  "신장": 165.0,
  "체중": 58.0,
  "BMI": 21.3,
  "체지방률": 28.5,
  "골격근량": 22.0,
  "무기질": 3.5,
  "체수분": 40.0,
  ...
  "근육_부위별등급": {...},
  "체지방_부위별등급": {...}
}

        ↓ [Stage 계산]

# Stage 결과 추가
{
  ...기존 measurements...
  "stage2_근육보정체형": "표준형",
  "stage3_상하체밸런스": "표준형"
}

        ↓ [DB 저장]

# health_records 테이블 (PostgreSQL JSONB)
id=1, user_id=1, measurements={...전체 데이터...}

        ↓ [LLM 호출]

# 프롬프트 생성 → LLM → 자연어 리포트
"이영희님의 체형 분석 결과...
- 현재 BMI는 21.3으로 정상 범위입니다.
- 체지방률은 28.5%로 약간 높은 편입니다.
- 골격근량은 22.0kg으로 표준입니다.

운동 계획:
1. 주 3-4회 유산소 운동 (30-40분)
2. 주 2-3회 근력 운동...

식단 계획:
- 목표 칼로리: 1800kcal
- 단백질 비율: 25%..."

        ↓ [DB 저장 + 파일 저장]

# analysis_reports 테이블
id=1, record_id=1, llm_output="..."

# outputs/report_1_20260123_120000.txt
```

---

## 핵심 모듈 상세

### 1. database.py - PostgreSQL 관리

**역할**: PostgreSQL 데이터베이스 연결 및 CRUD 작업

**주요 클래스**:
```python
class Database:
    def __init__(self, connection_string=None):
        # 환경변수 또는 파라미터에서 연결 문자열 읽기
        # pgvector extension 자동 설치 시도
        # 테이블 생성 (users, health_records, analysis_reports, user_goals)
```

**주요 메서드**:
```python
# 사용자
create_user(username, email) -> int
get_user_by_email(email) -> Dict
get_user_by_id(user_id) -> Dict

# 건강 기록
save_health_record(user_id, measurements, source, measured_at) -> int
get_health_record(record_id) -> Dict
get_user_health_records(user_id, limit) -> List[Dict]
search_health_records_by_measurement(user_id, key, value) -> List[Dict]  # JSONB 검색

# 분석 리포트
save_analysis_report(user_id, record_id, llm_output, model_version) -> int
get_analysis_report(report_id) -> Dict
get_report_by_record_id(record_id) -> Dict

# 유틸리티
test_connection() -> bool
get_user_statistics(user_id) -> Dict
```

**PostgreSQL 특징**:
- **JSONB**: measurements를 JSONB로 저장 → 빠른 검색
- **GIN 인덱스**: JSONB 필드에 GIN 인덱스 → 검색 성능 향상
- **pgvector 준비**: 향후 임베딩 벡터 저장 및 유사도 검색

---

### 2. workflow.py - 워크플로우 로직

**역할**: 전체 분석 프로세스 관리

**주요 클래스**:

#### InBodyAnalysisWorkflow
```python
class InBodyAnalysisWorkflow:
    def __init__(self, db: Database, llm_client, model_version: str):
        self.db = db
        self.llm_client = llm_client  # Claude/GPT/Ollama 클라이언트
        self.model_version = model_version
        self.analyzer = BodyCompositionAnalyzer()  # rule_based_bodytype
```

**주요 메서드**:
```python
# 1단계
extract_ocr_data(sample_profile) -> Dict
    # sample_profile → measurements 형식 변환

# 2단계
get_user_confirmation(ocr_data) -> Dict
    # 사용자 확인 (현재는 시뮬레이션)

# 3단계
calculate_stages(ocr_data) -> Dict
    # BodyCompositionAnalyzer로 Stage 2, 3 계산
    # 반환: {"stage2": "표준형", "stage3": "표준형"}

# 4단계
merge_data(confirmed_ocr_data, stage_results) -> Dict
    # OCR 데이터 + Stage 결과 병합

# 5단계
save_health_record(user_id, measurements, source) -> int
    # PostgreSQL에 저장

# 6단계
generate_llm_report(user_id, record_id) -> int
    # measurements 추출 → 프롬프트 생성 → LLM 호출 → 리포트 저장

# 전체 실행
run_full_workflow(user_id, sample_profile, source) -> Dict
    # 1~6단계 순차 실행
    # 반환: {"record_id": int, "report_id": int}
```

#### UserAuthManager
```python
class UserAuthManager:
    def register_or_login(self, username: str, email: str) -> Dict:
        # 이메일로 사용자 조회
        # 있으면 로그인, 없으면 회원가입
        # 반환: 사용자 정보
```

---

### 3. prompt_generator_measurements.py - 프롬프트 생성

**역할**: measurements 전체 데이터를 활용한 LLM 프롬프트 생성

**주요 함수**:
```python
def create_fitness_prompt_from_measurements(measurements: Dict) -> tuple[str, str]:
    """
    measurements의 모든 데이터를 읽기 쉽게 구조화하여 프롬프트 생성

    Args:
        measurements: {
            "성별": "남성",
            "나이": 28,
            "신장": 175.0,
            "체중": 72.5,
            "BMI": 23.7,
            "체지방률": 21.0,
            "골격근량": 35.6,
            "무기질": 3.5,
            "체수분": 45.2,
            ...
            "근육_부위별등급": {...},
            "체지방_부위별등급": {...},
            "stage2_근육보정체형": "근육형",
            "stage3_상하체밸런스": "하체발달형"
        }

    Returns:
        (system_prompt, user_prompt)
    """

    system_prompt = """당신은 전문 피트니스 트레이너입니다.
    사용자의 InBody 측정 데이터와 규칙 기반 분석 결과를 바탕으로
    맞춤형 운동/식단 추천을 제공하세요.

    다음 내용을 포함:
    1. 체형 분석 요약
    2. 운동 계획
    3. 식단 계획
    4. 생활 습관 조언
    """

    user_prompt = """
    ## 기본 정보
    - 성별: {성별}
    - 나이: {나이}세
    ...

    ## 체성분 분석
    - BMI: {BMI}
    - 체지방률: {체지방률}%
    ...

    ## 규칙 기반 체형 분석 결과
    - Stage 2: {stage2_근육보정체형}
    - Stage 3: {stage3_상하체밸런스}

    위 데이터를 종합하여 맞춤형 리포트를 작성해주세요.
    """
```

---

### 4. rule_based_bodytype/ - Stage 분석 알고리즘

**역할**: 체성분 데이터를 기반으로 체형 분류

**구조**:
```
rule_based_bodytype/
├── body_analysis/
│   ├── pipeline.py          # BodyCompositionAnalyzer (Facade)
│   ├── stages.py            # Stage1, Stage2, Stage3 분류기
│   ├── models.py            # BodyCompositionData 모델
│   ├── metrics.py           # BMI, 체지방, 근육 분류기
│   ├── segmental.py         # 부위별 데이터 정규화
│   └── constants.py         # 상수 정의
└── main_test.py             # 테스트 스크립트
```

**주요 클래스**:

#### BodyCompositionAnalyzer (pipeline.py)
```python
class BodyCompositionAnalyzer:
    def analyze_full_pipeline(self, raw_input: dict) -> dict:
        """
        전체 분석 파이프라인 실행

        Args:
            raw_input: {
                "sex": "남자",
                "age": 28,
                "height_cm": 175,
                "weight_kg": 72.5,
                "bmi": 23.7,
                "fat_rate": 21.0,
                "smm": 35.6,
                "muscle_seg": {...},
                "fat_seg": {...}
            }

        Returns:
            {
                "stage2": "근육형",
                "stage3": "하체발달형"
            }
        """
        # 1. 입력 데이터 검증 및 변환
        data = BodyCompositionData.from_dict(raw_input)

        # 2. 기본 지표 분류
        bmi_value, bmi_cat = BMIClassifier.classify(data.bmi)
        fat_cat = BodyFatClassifier.classify(data.fat_rate)
        smm_ratio, muscle_level = MuscleClassifier.classify(data.smm, data.weight_kg)

        # 3. Stage 1: 기초 체형 분류
        stage1_type = Stage1BodyTypeClassifier.classify(bmi_cat, fat_cat, muscle_level)

        # 4. Stage 2: 근육량 보정
        stage2_type = Stage2MuscleAdjuster.adjust(stage1_type, muscle_level)

        # 5. Stage 3: 상하체 밸런스 분석
        muscle_seg_normalized = DataNormalizer.normalize_muscle_segment(...)
        fat_seg_normalized = DataNormalizer.normalize_fat_segment(...)
        stage3_type = Stage3BalanceAnalyzer.classify(muscle_seg_normalized, fat_seg_normalized)

        return {
            "stage2": stage2_type,
            "stage3": stage3_type
        }
```

**Stage 설명**:
- **Stage 1**: BMI + 체지방률 → 기본 체형 (마른형, 표준형, 근육형, 비만형 등)
- **Stage 2**: Stage 1 + 근육량 → 보정 체형 (표준형, 근육형, 고근육체형, 비만형 등)
- **Stage 3**: 부위별 근육/지방 → 상하체 밸런스 (표준형, 상체발달형, 하체발달형, 상체비만형, 하체비만형)

---

### 5. LLM 클라이언트

#### claude_client.py
```python
class ClaudeClient:
    def __init__(self, model="claude-3-5-sonnet-20241022", max_tokens=8192):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = model
        self.max_tokens = max_tokens

    def generate_chat(self, system_prompt: str, user_prompt: str) -> str:
        """Claude API 호출"""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        return message.content[0].text

    def check_connection(self) -> bool:
        """API 연결 확인"""
        try:
            self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except:
            return False
```

#### openai_client.py
```python
class OpenAIClient:
    def __init__(self, model="gpt-4o-mini", max_tokens=8192):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.max_tokens = max_tokens

    def generate_chat(self, system_prompt: str, user_prompt: str) -> str:
        """OpenAI API 호출"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=self.max_tokens
        )
        return response.choices[0].message.content
```

#### ollama_client.py
```python
class OllamaClient:
    def __init__(self, model="qwen3:14b", base_url="http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    def generate_chat(self, system_prompt: str, user_prompt: str) -> str:
        """Ollama API 호출 (로컬)"""
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "stream": False
            }
        )
        return response.json()["message"]["content"]
```

**공통 인터페이스**:
- 모든 클라이언트는 `generate_chat(system, user)` 메서드 제공
- 동일한 방식으로 호출 가능 → 쉽게 교체 가능

---

## 데이터베이스 구조

### ERD

```
┌─────────────────┐
│     users       │
├─────────────────┤
│ id (PK)         │
│ username        │
│ email (UNIQUE)  │
│ created_at      │
└────────┬────────┘
         │ 1
         │
         │ N
┌────────┴────────┐
│ health_records  │
├─────────────────┤
│ id (PK)         │
│ user_id (FK)    │
│ source          │
│ measured_at     │
│ measurements    │ ← JSONB (모든 InBody 데이터 + Stage 결과)
│   (JSONB)       │
│ created_at      │
└────────┬────────┘
         │ 1
         │
         │ N
┌────────┴────────────┐
│ analysis_reports    │
├─────────────────────┤
│ id (PK)             │
│ user_id (FK)        │
│ record_id (FK)      │
│ llm_output (TEXT)   │ ← LLM 생성 리포트
│ model_version       │
│ generated_at        │
└─────────────────────┘

┌─────────────────┐
│  user_goals     │
├─────────────────┤
│ id (PK)         │
│ user_id (FK)    │
│ goal_type       │
│ started_at      │
│ ended_at        │
└─────────────────┘
```

### JSONB 활용

**measurements 구조**:
```json
{
  "성별": "남성",
  "나이": 28,
  "신장": 175.0,
  "체중": 72.5,
  "BMI": 23.7,
  "체지방률": 21.0,
  "골격근량": 35.6,
  "무기질": 3.5,
  "체수분": 45.2,
  "단백질": 12.8,
  "체지방": 15.2,
  "복부지방률": 0.85,
  "내장지방레벨": 8,
  "기초대사량": 1680,
  "비만도": 105.2,
  "적정체중": 68.9,
  "권장섭취열량": 2400,
  "체중조절": -3.6,
  "지방조절": -5.2,
  "근육조절": 1.6,
  "근육_부위별등급": {
    "왼팔": "표준",
    "오른팔": "표준",
    "복부": "표준",
    "왼다리": "표준이상",
    "오른다리": "표준이상"
  },
  "체지방_부위별등급": {
    "왼팔": "표준",
    "오른팔": "표준",
    "복부": "표준이상",
    "왼다리": "표준",
    "오른다리": "표준"
  },
  "stage2_근육보정체형": "근육형",
  "stage3_상하체밸런스": "하체발달형"
}
```

**JSONB 검색 예시**:
```python
# 특정 체형 검색
db.search_health_records_by_measurement(1, 'stage2_근육보정체형', '근육형')

# SQL로는
# SELECT * FROM health_records
# WHERE measurements->>'stage2_근육보정체형' = '근육형';
```

---

## 워크플로우 실행

### main_workflow.py - 메인 실행 파일

**구조**:
```python
def main():
    # 1. 인자 파싱
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--profile-id", required=True)
    parser.add_argument("--model", default="gpt-4o-mini")
    args = parser.parse_args()

    # 2. DB 연결
    db = Database()

    # 3. LLM 클라이언트 생성
    if args.model.startswith("claude-"):
        client = ClaudeClient(model=args.model)
    elif args.model.startswith("gpt-"):
        client = OpenAIClient(model=args.model)
    else:
        client = OllamaClient(model=args.model)

    # 4. 회원가입/로그인
    auth = UserAuthManager(db)
    user = auth.register_or_login(args.username, args.email)

    # 5. 프로필 로드
    profiles = load_sample_profiles()
    profile = next(p for p in profiles if p["id"] == args.profile_id)

    # 6. 워크플로우 실행
    workflow = InBodyAnalysisWorkflow(db, client, args.model)
    result = workflow.run_full_workflow(user["id"], profile)

    # 7. 결과 출력 및 저장
    display_report(db, result["report_id"])
    save_report_to_file(db, result["report_id"], args.output_dir)
```

---

## 코드 구조

### 프로젝트 파일 트리

```
/home/user/projects/ExplainMyBody/llm/
├── main_workflow.py ⭐               # 메인 실행 파일
├── workflow.py                       # 워크플로우 로직
├── database.py                       # PostgreSQL 관리
├── prompt_generator_measurements.py  # 프롬프트 생성
├── claude_client.py                  # Claude 클라이언트
├── openai_client.py                  # OpenAI 클라이언트
├── ollama_client.py                  # Ollama 클라이언트
├── models.py                         # Pydantic 모델 (레거시)
├── sample_profiles.json              # 테스트 프로필
├── .env                              # 환경변수
├── requirements.txt                  # 의존성
├── README.md                         # 프로젝트 개요
├── WORKFLOW_GUIDE.md                 # 워크플로우 가이드
├── POSTGRESQL_SETUP.md               # PostgreSQL 설정
├── ONBOARDING.md                     # 이 파일
├── outputs/                          # 출력 결과
└── rule_based_bodytype/              # Stage 분석 알고리즘
    └── body_analysis/
        ├── pipeline.py               # Analyzer
        ├── stages.py                 # Stage1, 2, 3
        ├── models.py                 # 데이터 모델
        ├── metrics.py                # 분류기
        ├── segmental.py              # 정규화
        └── constants.py              # 상수
```

### 레거시 파일 (참고용)

```
├── run_pipeline.py                   # 레거시 통합 파이프라인
├── run_pipeline_claude.py            # 레거시 Claude 파이프라인
├── run_pipeline_gpt.py               # 레거시 GPT 파이프라인
├── prompt_generator_claude.py        # 레거시 Claude 프롬프트
├── prompt_generator_gpt.py           # 레거시 GPT 프롬프트
├── rulebase.py                       # 레거시 규칙 분석
└── rulebase_wrapper.py               # 레거시 래퍼
```

---

## 개발 가이드

### 코드 스타일

- **Type Hints**: 모든 함수에 타입 힌트 사용
- **Docstrings**: 클래스와 주요 함수에 docstring 작성
- **Error Handling**: try-except로 예외 처리
- **Logging**: print 대신 logging 모듈 사용 권장

### 새로운 기능 추가

#### 1. 새로운 Stage 추가

`rule_based_bodytype/body_analysis/stages.py`에 새 클래스 추가:

```python
class Stage4CustomAnalyzer:
    @staticmethod
    def classify(data):
        # 새로운 분석 로직
        return "분석결과"
```

`pipeline.py`에서 호출:

```python
stage4_result = Stage4CustomAnalyzer.classify(data)
return {
    "stage2": stage2_type,
    "stage3": stage3_type,
    "stage4": stage4_result  # 추가
}
```

#### 2. 새로운 LLM 추가

`new_llm_client.py` 생성:

```python
class NewLLMClient:
    def __init__(self, model, api_key):
        self.model = model
        self.api_key = api_key

    def generate_chat(self, system_prompt, user_prompt):
        # 새 LLM API 호출
        return response_text

    def check_connection(self):
        # 연결 확인
        return True
```

`main_workflow.py`에 추가:

```python
elif args.model.startswith("new-"):
    client = NewLLMClient(model=args.model)
```

#### 3. 데이터베이스 테이블 추가

`database.py`의 `_init_database()` 메서드에 추가:

```python
cursor.execute("""
    CREATE TABLE IF NOT EXISTS new_table (
        id SERIAL PRIMARY KEY,
        ...
    )
""")
```

CRUD 메서드 추가:

```python
def create_new_record(self, data):
    with self.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO new_table ...")
```

---

## 문제 해결

### PostgreSQL 연결 오류

```bash
# 서비스 확인
sudo systemctl status postgresql

# 서비스 시작
sudo systemctl start postgresql

# Docker 사용 시
docker start explainmybody-postgres
docker logs explainmybody-postgres

# 연결 테스트
psql -U postgres -d explainmybody -c "SELECT 1;"
```

### API 키 오류

```bash
# .env 확인
cat .env

# 환경변수 로드 테스트
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('OPENAI_API_KEY'))"
```

### rule_based_bodytype 임포트 오류

```python
# workflow.py에서 경로 확인
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "rule_based_bodytype"))
from rule_based_bodytype.body_analysis.pipeline import BodyCompositionAnalyzer
```

### JSONB 검색 안 됨

```sql
-- GIN 인덱스 확인
SELECT indexname FROM pg_indexes WHERE tablename = 'health_records';

-- 인덱스 재생성
DROP INDEX idx_health_records_measurements_gin;
CREATE INDEX idx_health_records_measurements_gin ON health_records USING GIN (measurements);
```

---

## 다음 단계

### 학습 경로

1. **기본 실행**: `main_workflow.py` 여러 번 실행해보기
2. **코드 읽기**: `workflow.py` → `database.py` → `rule_based_bodytype/` 순서로
3. **프롬프트 수정**: `prompt_generator_measurements.py`에서 프롬프트 커스터마이징
4. **DB 탐색**: psql로 데이터 직접 확인
5. **새 기능 추가**: Stage 4 분석 또는 새로운 LLM 클라이언트 추가

### 실습 과제

1. **프롬프트 개선**: 리포트 형식을 마크다운으로 변경
2. **통계 기능**: 사용자별 평균 BMI 계산 함수 추가
3. **비교 기능**: 이전 측정 기록과 현재 기록 비교
4. **목표 추적**: user_goals 테이블 활용한 목표 관리 기능

---

## 유용한 명령어

```bash
# PostgreSQL 접속
psql -U postgres -d explainmybody

# 테이블 목록
\dt

# 테이블 구조
\d health_records

# 사용자 목록
SELECT id, username, email FROM users;

# 최근 기록 10개
SELECT id, user_id, measured_at, measurements->>'stage2_근육보정체형'
FROM health_records
ORDER BY measured_at DESC
LIMIT 10;

# 특정 체형 카운트
SELECT measurements->>'stage2_근육보정체형' as body_type, COUNT(*)
FROM health_records
GROUP BY body_type;
```

---

## 참고 자료

- [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) - 워크플로우 상세 가이드
- [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md) - PostgreSQL 설정 가이드
- [Pydantic 문서](https://docs.pydantic.dev/)
- [psycopg2 문서](https://www.psycopg.org/docs/)
- [PostgreSQL JSONB](https://www.postgresql.org/docs/current/datatype-json.html)
- [pgvector](https://github.com/pgvector/pgvector)

---

## 질문이 있으신가요?

프로젝트 관련 질문이나 도움이 필요하면 언제든지 팀에게 문의하세요!

**환영합니다, Serena! 🚀**
