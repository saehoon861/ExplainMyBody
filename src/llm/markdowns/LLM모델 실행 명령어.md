# ExplainMyBody LLM Pipeline 사용법

InBody 데이터를 기반으로 규칙 기반 분석과 LLM 추천을 생성하는 파이프라인 실행 가이드입니다.

## 목차
- [사전 준비](#사전-준비)
- [기본 사용법](#기본-사용법)
- [모델별 실행 명령어](#모델별-실행-명령어)
- [추가 옵션](#추가-옵션)

## 사전 준비

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. API 키 설정 (선택사항)
Claude 또는 OpenAI API를 사용하는 경우 `.env` 파일에 API 키를 설정해야 합니다.

```bash
# .env 파일 예시
ANTHROPIC_API_KEY=your_claude_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Ollama 서버 실행 (로컬 모델 사용 시)
```bash
ollama serve
```

## 기본 사용법

### 사용 가능한 프로필 목록 확인
```bash
python run_pipeline.py
python run_pipeline_claude.py
python run_pipeline_gpt.py
```

## 모델별 실행 명령어

### 1. Ollama (로컬 모델)

**단일 프로필 실행 (프로필 ID=1):**
```bash
python run_pipeline.py --model qwen3:14b --profile-id 1
```

**모든 프로필 실행:**
```bash
python run_pipeline.py --model qwen3:14b --all
```

**사용 가능한 모델:**
- `qwen3:14b` (기본값)
- 기타 Ollama에 설치된 모델

---

### 2. Claude API

**단일 프로필 실행:**
```bash
python run_pipeline_claude.py --model claude-3-5-sonnet-20241022 --profile-id 1
```

**모든 프로필 실행:**
```bash
python run_pipeline_claude.py --model claude-3-5-sonnet-20241022 --all
```

**사용 가능한 모델:**
- `claude-3-5-sonnet-20241022` (기본값)
- `claude-3-opus-20240229`
- 기타 Claude 모델

---

### 3. OpenAI/GPT API

**단일 프로필 실행:**
```bash
python run_pipeline_gpt.py --model gpt-4o-mini --profile-id 1
```

**모든 프로필 실행:**
```bash
python run_pipeline_gpt.py --model gpt-4o-mini --all
```

**사용 가능한 모델:**
- `gpt-4o-mini` (기본값)
- `gpt-4o`
- `gpt-4-turbo`
- 기타 OpenAI 모델

## 추가 옵션

### 출력 디렉토리 지정
```bash
python run_pipeline.py --profile-id 1 --output-dir outputs/custom_dir
```

### 로그 최소화 (조용히 실행)
```bash
python run_pipeline.py --profile-id 1 --quiet
```

### 최대 토큰 수 설정
```bash
python run_pipeline.py --profile-id 1 --max-tokens 8192
```

### 옵션 조합 예시
```bash
# Claude API로 모든 프로필 실행, 출력 디렉토리 지정, 조용히 실행
python run_pipeline_claude.py --model claude-3-5-sonnet-20241022 --all --output-dir outputs/claude_results --quiet --max-tokens 8192
```

## 출력 결과

실행 결과는 지정된 출력 디렉토리(기본값: `outputs/`)에 저장됩니다.

### 파일 형식
- **JSON 파일**: 전체 분석 결과 및 추천 데이터
  - 파일명 형식: `{이름}_{타임스탬프}.json`

- **Markdown 파일** (텍스트 응답인 경우):
  - 파일명 형식: `{이름}_{타임스탬프}_recommendations.md`

## 문제 해결

### Ollama 연결 오류
```
Error: Cannot connect to Ollama server.
Run: ollama serve
```
→ 터미널에서 `ollama serve` 명령어를 실행하여 Ollama 서버를 시작하세요.

### API 키 오류
```
Error: Cannot connect to Claude/OpenAI API.
Check your API key in .env file
```
→ `.env` 파일에 올바른 API 키가 설정되어 있는지 확인하세요.

### 프로필 ID를 찾을 수 없음
```
Error: Profile ID X not found.
```
→ `python run_pipeline.py` 명령어로 사용 가능한 프로필 목록을 확인하세요.

## 참고 사항

- 각 파이프라인 파일은 서로 다른 prompt generator를 사용합니다:
  - `run_pipeline.py` → `prompt_generator.py`
  - `run_pipeline_claude.py` → `prompt_generator_claude.py`
  - `run_pipeline_gpt.py` → `prompt_generator_gpt.py`

- 모든 입력 데이터는 Pydantic 모델을 통해 검증됩니다.

- LLM 응답은 JSON 형식으로 파싱을 시도하며, 실패 시 텍스트로 저장됩니다.
