### 현재 실행폴더 확인 방법 ###



# 현재 작업 내용 경로 : \\outputs 폴더 안에 각 모델 및 LLM ai 생성 프롬프트 별 결과물 존재
        
         => 폴더명 : 운동계획 or 주간피드백 , 실행모델 , 프롬프트 생성한 ai 순으로 표시됩니다. 



# 각 모델마다 10명의 출력결과가 있는데, 신체정보 sample은 sample_profiles.json 에서 확인 가능.



# 경로 :  \\llm 폴더
         
         => LLM모델 실행 명령어.md 및 README.md 파일 확인




# 폴더 내 파일들 설명

claude_client.py, ollama_client.py, openai_client.py : 클로드, 챗지피티, ollama LLM 모델 클라이언트 설정 파일

models.py                                            : pydantic 적용을 위한 타입 지정 및 pydantic 자체 설정 파일

prompt_generator_claude.py, prompt_generator_gpt.py  : 클로드, 챗지피티 로 생성된 prompt를 LLM 모델에 넣는 실제 명령어 파일

rulebase.py, rulebase_wrapper.py                     : 규칙 기반 알고리즘 관련 파일

run_pipeline_claude.py, run_pipeline_gpt.py, run_pipeline.py : 실제 구동 파일. claude 실행시 claude prompt, gpt 실행시 gpt prompt (LLM 모델 실행용 파일)

클로드 코드로 생성한 프롬프트는 prompt_generator_claude.py안에서 확인가능하며 run_pipeline_claude.py로 구동해 LLM 실행 합니다. 
gpt 동일.


# 각 모델마다 10명의 출력결과가 있는데, 신체정보 sample은 sample_profiles.json 에서 확인 가능.



# ExplainMyBody

InBody 검사 결과지를 기반으로 한 체형 분석 및 맞춤 운동·식단 추천 챗봇


## Project Goal

본 프로젝트는 InBody 검사 결과지(이미지 또는 PDF)를 입력으로 받아, OCR 및 텍스트 파싱을 통해 핵심 신체 지표를 구조화하고, 규칙 기반 알고리즘과 LLM을 결합하여 체형 유형 분석, 맞춤 운동 추천, 주간 운동 계획 및 식단 가이드를 구체적인 근거를 기반으로 하여 개인 맞춤형 운동 에이전트를 구현하는 것을 목표로 하고 있다.


## Project Flow (Draft)

### 1. InBody 결과지 입력
- 사용자는 InBody 검사 결과지를 이미지 또는 PDF 형태로 업로드한다.

### 2. 입력 타입에 따른 데이터 처리
- Image 입력:
  - OCR 파이프라인을 통해 텍스트 추출
- PDF 입력:
  - 텍스트 파싱을 통해 수치 데이터 추출

### 3. 데이터 검증 및 사용자 보정
- 추출된 InBody 수치를 사용자에게 제공
- 사용자는 잘못 인식된 값이 있을 경우 직접 수정
- 개인 목표 및 특이사항을 자유 텍스트로 입력
  (예: 체중 감량, 특정 질환, 운동 제한)

### 4. 규칙 기반 체형 분석
- 검증된 InBody 수치를 기반으로 체형 분석 수행
- BMI, 체지방률, 골격근량 등 핵심 지표 활용
- 분석 결과를 구조화된 데이터 형태로 생성

### 5. 맞춤 운동·식단 및 주간 운동 스케줄 생성
- 체형 분석 결과와 사용자 목표를 입력으로 활용
- LLM을 통해 다음 내용을 생성:
  - 체형 유형에 대한 설명
  - 맞춤 운동 추천
  - 주간 단위 운동 스케줄
  - 기본 식단 가이드
- 추천 결과에 대한 간단한 근거 설명 제공

---

### 6. 주간 운동 스케줄 저장
- 생성된 주간 운동 스케줄을 시스템에 저장
- 요일별 운동 계획 기준으로 관리

---

### 7. 일일 운동 수행 기록
- 사용자는 오늘 수행한 운동의 완료 여부를 체크
- 간단한 메모 형태로 운동 기록을 남김
  (예: 힘들었던 점, 컨디션)

---

### 8. LLM 기반 주간 피드백 제공
- 사용자의 운동 기록을 바탕으로 피드백 및 새로운 계획 제공

---


## User-facing Features

- InBody 결과지를 기반으로 한 개인 체형 분석 제공
- 개인 목표 및 특이사항을 반영한 맞춤 운동·식단 추천
- 주간 단위 운동 스케줄 자동 생성
- 오늘 수행한 운동 기록 및 완료 여부 관리
- 운동 기록(완료 여부 + 간단 메모)
- 운동 기록 정보를 통해 피드백을 제공


## Current Status

### Decided

- 전체 시스템 파이프라인 구조
- 규칙 기반 체형 분석 + LLM 생성 구조
- OCR 모델: PaddleOCR 사용

### TBD (To Be Decided)

- LLM 모델 선정
- 개발 및 배포 환경


## Experimental Plan

- OCR
  - 후처리 및 사용자 보정 난이도

- InBody 레이아웃 유형별 OCR 실패 케이스 분석

- InBody 주요 지표를 기반으로 한
  규칙 기반 체형 분석 로직 검증
  - 동일 입력에 대해 일관된 결과를 생성하는지 확인
  - 체형 분류 기준의 명확성 및 해석 가능성 검토

- 규칙기반 알고리즘
  - 체형 분석 결과만 도출 할 것인지 혹은 체형 유형에 따른 운동 유형도 분류할 것인지
 
- LLM 적용 범위 정의
  - 체형 분석 결과 설명
  - 맞춤 운동·식단 추천 생성
  - 주간 피드백 제공
  
- 프롬프트 설계 및 관리 방식 검토
  - 분석 결과 및 사용자 입력을 컨텍스트로 포함하는 구조
  - 기능별 프롬프트 분리 설계

- RAG 적용 가능성 검토
  - 운동·식단 관련 기초 지식 문서를 참조 데이터로 구성
  - LangChain 사용 여부 및 필요성 평가


## Repository Structure (Initial)

```text
.
├── docs/              # 설계 및 실험 문서
├── experiments/       # 실험 코드
├── src/               # 메인 구현 코드 (예정)
├── README.md
├── requirements.txt
├── .env.example
└── LICENSE
'''