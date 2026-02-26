# 테스트 실행 가이드

## 테스트 구조

- **tests/unit**  
  → 순수 로직 단위 테스트 (LLM, DB mock)

- **tests/integration**  
  → 서비스 간 연결 테스트 (LLM 서비스, agent graph, repository 등)

- **tests/e2e** (선택)  
  → API부터 프론트 연동까지 전체 시나리오

## 실행 방법

### 유닛 테스트
```bash
pytest tests/unit
```

### 통합 테스트
```bash
pytest tests/integration
```

### 전체 테스트
```bash
pytest tests
```

### 상세 출력
```bash
pytest tests -v
```

### 특정 테스트 파일 실행
```bash
pytest tests/unit/test_prompt_generator.py
pytest tests/integration/test_llm_pipeline.py
```

### 커버리지와 함께 실행
```bash
pytest tests --cov=services --cov=repositories --cov-report=html
```

## 테스트 작성 가이드

### 유닛 테스트
- 외부 의존성(DB, LLM API)은 Mock 사용
- 단일 함수/클래스의 동작만 검증
- 빠른 실행 속도 유지

### 통합 테스트
- 여러 컴포넌트 간의 상호작용 검증
- Mock은 최소화하되 외부 API는 Mock 사용
- 실제 시나리오에 가까운 테스트
