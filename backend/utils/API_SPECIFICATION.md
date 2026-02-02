# ExplainMyBody Backend API 명세서

> **프론트엔드 개발자용 API 문서**  
> 작성일: 2026-01-29  
> Base URL: `http://localhost:8000`

## 📋 목차

1. [개요](#개요)
2. [인증 API](#1-인증-api)
3. [사용자 API](#2-사용자-api)
4. [건강 기록 API](#3-건강-기록-api)
5. [분석 API](#4-분석-api)
6. [목표 API](#5-목표-api)
7. [주간 계획 API](#6-주간-계획-api)
8. [데이터 스키마](#데이터-스키마)
9. [에러 처리](#에러-처리)

---

## 개요

### 서버 정보
- **Base URL**: `http://localhost:8000`
- **API Prefix**: `/api`
- **자동 생성 문서**: 
  - Swagger UI: http://localhost:8000/docs
  - ReDoc: http://localhost:8000/redoc

### 공통 헤더
```
Content-Type: application/json
```

### 응답 형식
모든 API는 JSON 형식으로 응답합니다.

---

## 1. 인증 API

Base Path: `/api/auth`

### 1.1 이메일 중복 확인

**POST** `/api/auth/check-email`

이메일 사용 가능 여부를 확인합니다.

**Request Body:**
```json
{
  "email": "hong@example.com"
}
```

**Response (200 OK):**
```json
{
  "available": true,
  "message": "사용 가능한 이메일입니다."
}
```

**Error Response (409 Conflict):**
```json
{
  "detail": "이미 사용 중인 이메일입니다."
}
```

---

### 1.2 회원가입 (확장)

**POST** `/api/auth/register`

사용자 계정을 생성하고, 선택적으로 초기 신체 정보, 목표, 건강 상태 등을 함께 등록합니다.

**Request Body:**

> **참고**: `inbodyData`와 다른 선택 필드들은 회원가입 단계(Step 1~4)에서 수집된 정보를 포함합니다.

```json
{
  "username": "홍길동",
  "email": "hong@example.com",
  "password": "password123",
  "gender": "남성",
  "age": 30,
  "height": 175.5,
  "startWeight": 78.5,
  "targetWeight": 70.0,
  "goalType": "다이어트",
  "activityLevel": "중간",
  "preferredExercises": ["헬스", "달리기"],
  "goal": "여름까지 복근 만들기",
  "medicalConditions": ["허리디스크"],
  "medicalConditionsDetail": "무거운 것 들 때 조심해야 함",
  "inbodyData": {
    "weight": 78.5,
    "percent_body_fat": 25.0,
    "skeletal_muscle_mass": 32.0
  },
  "confirmPassword": "password123"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "username": "홍길동",
  "email": "hong@example.com",
  "created_at": "2026-01-29T10:00:00",
  "goal_type": "증량",
  "goal_description": "여름까지 복근 만들기",
  "start_weight": 78.5,
  "target_weight": 70.0
}
```

---

### 1.3 로그인

**POST** `/api/auth/login`

사용자 로그인을 처리합니다.

**Request Body:**
```json
{
  "email": "hong@example.com",
  "password": "password123"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "username": "홍길동",
  "email": "hong@example.com",
  "created_at": "2026-01-29T10:00:00",
  "goal_type": "증량",
  "goal_description": "여름까지 복근 만들기",
  "start_weight": 78.5,
  "target_weight": 70.0
}
```

---

### 1.4 현재 사용자 조회

**GET** `/api/auth/me?user_id={user_id}`

현재 로그인한 사용자 정보를 조회합니다. (JWT 도입 전 임시로 `user_id` 사용)

**Query Parameters:**
- `user_id` (integer, required): 사용자 ID

**Response (200 OK):**
```json
{
  "id": 1,
  "username": "홍길동",
  "email": "hong@example.com",
  "created_at": "2026-01-29T10:00:00",
  "goal_type": "다이어트",
  "goal_description": "여름까지 복근 만들기",
  "start_weight": 78.5,
  "target_weight": 70.0
}
```

---

### 1.5 로그아웃

**POST** `/api/auth/logout?user_id={user_id}`

사용자 로그아웃을 처리합니다.

**Query Parameters:**
- `user_id` (integer, required): 사용자 ID

**Response (200 OK):**
```json
{
  "message": "로그아웃 완료"
}
```

---

## 2. 사용자 API

Base Path: `/api/users`

### 2.1 사용자 정보 조회

**GET** `/api/users/{user_id}`

특정 사용자의 정보를 조회합니다.

**Path Parameters:**
- `user_id` (integer, required): 사용자 ID

**Response (200 OK):**
```json
{
  "id": 1,
  "username": "홍길동",
  "email": "hong@example.com",
  "created_at": "2026-01-29T10:00:00"
}
```

**Error Response (404):**
```json
{
  "detail": "사용자를 찾을 수 없습니다."
}
```

---

### 2.2 사용자 목록 조회

**GET** `/api/users/?skip={skip}&limit={limit}`

전체 사용자 목록을 조회합니다 (관리자용).

**Query Parameters:**
- `skip` (integer, optional, default: 0): 건너뛸 개수
- `limit` (integer, optional, default: 100): 조회할 최대 개수

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "username": "홍길동",
    "email": "hong@example.com",
    "created_at": "2026-01-29T10:00:00"
  },
  {
    "id": 2,
    "username": "김철수",
    "email": "kim@example.com",
    "created_at": "2026-01-29T11:00:00"
  }
]
```

---

### 2.3 사용자 통계 조회

**GET** `/api/users/{user_id}/statistics`

사용자의 건강 기록 및 분석 리포트 통계를 조회합니다.

**Path Parameters:**
- `user_id` (integer, required): 사용자 ID

**Response (200 OK):**
```json
{
  "user_id": 1,
  "total_records": 5,
  "total_reports": 3
}
```

---

### 2.4 사용자 목표 수정

**PUT** `/api/users/{user_id}/goal`

사용자의 목표 및 시작 체중, 목표 체중을 수정합니다.

**Path Parameters:**
- `user_id` (integer, required): 사용자 ID

**Request Body:**
```json
{
  "start_weight": 78.5,
  "target_weight": 70.0,
  "goal_type": "다이어트",
  "goal_description": "체지방 5% 감량 및 근육량 2kg 증량"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "username": "홍길동",
  "email": "hong@example.com",
  "created_at": "2026-01-29T10:00:00",
  "goal_type": "다이어트",
  "goal_description": "체지방 5% 감량 및 근육량 2kg 증량",
  "start_weight": 78.5,
  "target_weight": 70.0
}
```

---

## 3. 건강 기록 API

Base Path: `/api/health-records`

### 3.1 OCR 데이터 추출 (Step 1)

**POST** `/api/health-records/ocr/extract`

인바디 이미지에서 데이터를 추출합니다 (검증 없음).

> ⚠️ **중요**: 이 API는 OCR 원시 데이터만 반환합니다. 사용자가 데이터를 확인하고 수정한 후 `/ocr/validate`로 전송해야 합니다.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `image` (file, required): 인바디 이미지 파일

**Response (200 OK):**
```json
{
  "data": {
    "기본정보": {
      "신장": 170.0,
      "연령": 30,
      "성별": "남성"
    },
    "체성분": {
      "체수분": 41.7,
      "단백질": 11.4,
      "무기질": 3.99,
      "체지방": 20.6
    },
    "체중관리": {
      "체중": 77.7,
      "골격근량": 32.5,
      "체지방량": 20.6,
      "적정체중": null,
      "체중조절": null,
      "지방조절": -10.5,
      "근육조절": 0.0
    },
    "비만분석": {
      "BMI": 26.9,
      "체지방률": 26.5,
      "복부지방률": 0.93,
      "내장지방레벨": 8,
      "비만도": 122
    },
    "연구항목": {
      "제지방량": 57.1,
      "기초대사량": 1603,
      "권장섭취열량": 2267
    },
    "부위별근육분석": {
      "왼쪽팔": "표준",
      "오른쪽팔": "표준",
      "복부": "표준",
      "왼쪽하체": "표준",
      "오른쪽하체": "표준"
    },
    "부위별체지방분석": {
      "왼쪽팔": "표준이상",
      "오른쪽팔": "표준이상",
      "복부": "표준이상",
      "왼쪽하체": "표준이상",
      "오른쪽하체": "표준이상"
    }
  },
  "message": "OCR 추출 완료. 데이터를 확인하고 수정해주세요."
}
```

**Error Response (503):**
```json
{
  "detail": "OCR 엔진이 아직 로딩 중입니다. 잠시 후 다시 시도해주세요."
}
```

---

### 3.2 데이터 검증 및 저장 (Step 2)

**POST** `/api/health-records/ocr/validate?user_id={user_id}`

사용자가 검증/수정한 인바디 데이터를 저장하고 체형 분석을 수행합니다.

> ⚠️ **프론트엔드 검증 필수**:
> - 모든 필수 필드가 입력되어야 함
> - 이상치 값은 프론트엔드에서 차단
> - 백엔드는 Pydantic으로 최종 검증

**Query Parameters:**
- `user_id` (integer, required): 사용자 ID

**Request Body:**
```json
{
  "기본정보": {
    "신장": 170.0,
    "연령": 30,
    "성별": "남성"
  },
  "체성분": {
    "체수분": 41.7,
    "단백질": 11.4,
    "무기질": 3.99,
    "체지방": 20.6
  },
  "체중관리": {
    "체중": 77.7,
    "골격근량": 32.5,
    "체지방량": 20.6,
    "적정체중": 67.2,
    "체중조절": -10.5,
    "지방조절": -10.5,
    "근육조절": 0.0
  },
  "비만분석": {
    "BMI": 26.9,
    "체지방률": 26.5,
    "복부지방률": 0.93,
    "내장지방레벨": 8,
    "비만도": 122
  },
  "연구항목": {
    "제지방량": 57.1,
    "기초대사량": 1603,
    "권장섭취열량": 2267
  },
  "부위별근육분석": {
    "왼쪽팔": "표준",
    "오른쪽팔": "표준",
    "복부": "표준",
    "왼쪽하체": "표준",
    "오른쪽하체": "표준"
  },
  "부위별체지방분석": {
    "왼쪽팔": "표준이상",
    "오른쪽팔": "표준이상",
    "복부": "표준이상",
    "왼쪽하체": "표준이상",
    "오른쪽하체": "표준이상"
  }
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "user_id": 1,
  "measurements": {
    "기본정보": { ... },
    "체성분": { ... },
    "체중관리": { ... },
    "비만분석": { ... },
    "연구항목": { ... },
    "부위별근육분석": { ... },
    "부위별체지방분석": { ... },
    "body_type1": "비만형",
    "body_type2": "표준형"
  },
  "source": "ocr",
  "measured_at": "2026-01-29T10:00:00",
  "body_type1": "비만형",
  "body_type2": "표준형",
  "created_at": "2026-01-29T10:00:00"
}
```

**Error Response (422):**
```json
{
  "detail": {
    "message": "데이터 검증 실패. 입력값을 다시 확인해주세요.",
    "errors": [
      {
        "loc": ["기본정보", "신장"],
        "msg": "Input should be greater than 50",
        "type": "greater_than"
      }
    ]
  }
}
```

---

### 3.3 건강 기록 생성 (수동 입력)

**POST** `/api/health-records/?user_id={user_id}`

건강 기록을 수동으로 생성합니다.

**Query Parameters:**
- `user_id` (integer, required): 사용자 ID

**Request Body:**
```json
{
  "measurements": {
    "체중": 70.0,
    "BMI": 23.5,
    "체지방률": 18.5
  },
  "source": "manual",
  "measured_at": "2026-01-29T10:00:00"
}
```

**Response (201 Created):**
```json
{
  "id": 2,
  "user_id": 1,
  "measurements": {
    "체중": 70.0,
    "BMI": 23.5,
    "체지방률": 18.5
  },
  "source": "manual",
  "measured_at": "2026-01-29T10:00:00",
  "body_type1": null,
  "body_type2": null,
  "created_at": "2026-01-29T10:00:00"
}
```

---

### 3.4 건강 기록 조회

**GET** `/api/health-records/{record_id}`

특정 건강 기록을 조회합니다.

**Path Parameters:**
- `record_id` (integer, required): 건강 기록 ID

**Response (200 OK):**
```json
{
  "id": 1,
  "user_id": 1,
  "measurements": { ... },
  "source": "ocr",
  "measured_at": "2026-01-29T10:00:00",
  "body_type1": "비만형",
  "body_type2": "표준형",
  "created_at": "2026-01-29T10:00:00"
}
```

---

### 3.5 사용자 건강 기록 목록 조회

**GET** `/api/health-records/user/{user_id}?limit={limit}`

사용자의 모든 건강 기록을 조회합니다.

**Path Parameters:**
- `user_id` (integer, required): 사용자 ID

**Query Parameters:**
- `limit` (integer, optional, default: 10): 조회할 최대 개수

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "measurements": { ... },
    "source": "ocr",
    "measured_at": "2026-01-29T10:00:00",
    "body_type1": "비만형",
    "body_type2": "표준형",
    "created_at": "2026-01-29T10:00:00"
  },
  {
    "id": 2,
    "user_id": 1,
    "measurements": { ... },
    "source": "manual",
    "measured_at": "2026-01-28T10:00:00",
    "body_type1": null,
    "body_type2": null,
    "created_at": "2026-01-28T10:00:00"
  }
]
```

---

### 3.6 최신 건강 기록 조회

**GET** `/api/health-records/user/{user_id}/latest`

사용자의 가장 최신 건강 기록을 조회합니다.

**Path Parameters:**
- `user_id` (integer, required): 사용자 ID

**Response (200 OK):**
```json
{
  "id": 1,
  "user_id": 1,
  "measurements": { ... },
  "source": "ocr",
  "measured_at": "2026-01-29T10:00:00",
  "body_type1": "비만형",
  "body_type2": "표준형",
  "created_at": "2026-01-29T10:00:00"
}
```

---

### 3.7 LLM 분석용 데이터 준비

**GET** `/api/health-records/{record_id}/analysis/prepare?user_id={user_id}`

LLM 건강 상태 분석에 필요한 입력 데이터를 준비합니다.

> 💡 **사용 방법**: 이 API로 받은 `input_data`를 LLM API에 전달하여 건강 상태 분석을 요청합니다.

**Path Parameters:**
- `record_id` (integer, required): 건강 기록 ID

**Query Parameters:**
- `user_id` (integer, required): 사용자 ID

**Response (200 OK):**
```json
{
  "success": true,
  "message": "LLM input 데이터 준비 완료. 프론트엔드에서 LLM API를 호출하세요.",
  "input_data": {
    "record_id": 1,
    "user_id": 1,
    "measured_at": "2026-01-29T10:00:00",
    "measurements": {
      "기본정보": { ... },
      "체성분": { ... },
      "체중관리": { ... },
      "비만분석": { ... },
      "연구항목": { ... }
    },
    "body_type1": "비만형",
    "body_type2": "표준형"
  }
}
```

---

## 4. 분석 API

Base Path: `/api/analysis`

### 4.1 건강 기록 분석 실행

**POST** `/api/analysis/{record_id}?user_id={user_id}`

LLM을 사용하여 건강 기록을 분석합니다.

**Path Parameters:**
- `record_id` (integer, required): 건강 기록 ID

**Query Parameters:**
- `user_id` (integer, required): 사용자 ID

**Response (201 Created):**
```json
{
  "id": 1,
  "user_id": 1,
  "record_id": 1,
  "llm_output": "현재 체지방률이 26.5%로 정상 범위를 초과하고 있습니다. BMI 26.9는 과체중에 해당합니다...",
  "model_version": "gpt-4",
  "analysis_type": "status_analysis",
  "generated_at": "2026-01-29T10:00:00",
  "embedding_1536": [0.123, 0.456, ...]
}
```

---

### 4.2 분석 리포트 조회

**GET** `/api/analysis/{report_id}`

특정 분석 리포트를 조회합니다.

**Path Parameters:**
- `report_id` (integer, required): 리포트 ID

**Response (200 OK):**
```json
{
  "id": 1,
  "user_id": 1,
  "record_id": 1,
  "llm_output": "현재 체지방률이 26.5%로...",
  "model_version": "gpt-4",
  "analysis_type": "status_analysis",
  "generated_at": "2026-01-29T10:00:00",
  "embedding_1536": [0.123, 0.456, ...]
}
```

---

### 4.3 건강 기록별 분석 리포트 조회

**GET** `/api/analysis/record/{record_id}`

특정 건강 기록에 대한 분석 리포트를 조회합니다.

**Path Parameters:**
- `record_id` (integer, required): 건강 기록 ID

**Response (200 OK):**
```json
{
  "id": 1,
  "user_id": 1,
  "record_id": 1,
  "llm_output": "현재 체지방률이 26.5%로...",
  "model_version": "gpt-4",
  "analysis_type": "status_analysis",
  "generated_at": "2026-01-29T10:00:00",
  "embedding_1536": [0.123, 0.456, ...]
}
```

---

### 4.4 사용자 분석 리포트 목록 조회

**GET** `/api/analysis/user/{user_id}?limit={limit}`

사용자의 모든 분석 리포트를 조회합니다.

**Path Parameters:**
- `user_id` (integer, required): 사용자 ID

**Query Parameters:**
- `limit` (integer, optional, default: 10): 조회할 최대 개수

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "record_id": 1,
    "llm_output": "현재 체지방률이 26.5%로...",
    "model_version": "gpt-4",
    "analysis_type": "status_analysis",
    "generated_at": "2026-01-29T10:00:00",
    "embedding_1536": [0.123, 0.456, ...]
  },
  {
    "id": 2,
    "user_id": 1,
    "record_id": 2,
    "llm_output": "체중이 감소하고 있습니다...",
    "model_version": "gpt-4",
    "analysis_type": "status_analysis",
    "generated_at": "2026-01-28T10:00:00",
    "embedding_1536": [0.789, 0.012, ...]
  }
]
```

---

## 5. 목표 API

Base Path: `/api/goals`

### 5.1 목표 생성

**POST** `/api/goals/?user_id={user_id}`

사용자의 건강 목표를 생성합니다.

**Query Parameters:**
- `user_id` (integer, required): 사용자 ID

**Request Body:**
```json
{
  "goal_type": "체중감량",
  "goal_description": "3개월 내 체지방 5% 감량",
  "preferences": "채식 선호, 아침 운동 선호",
  "health_specifics": "무릎 부상 있음",
  "is_active": 1
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "user_id": 1,
  "goal_type": "체중감량",
  "goal_description": "3개월 내 체지방 5% 감량",
  "preferences": "채식 선호, 아침 운동 선호",
  "health_specifics": "무릎 부상 있음",
  "is_active": 1,
  "started_at": "2026-01-29T10:00:00",
  "ended_at": null
}
```

---

### 5.2 주간 계획 생성용 데이터 준비

**POST** `/api/goals/plan/prepare?user_id={user_id}`

LLM 주간 계획 생성에 필요한 입력 데이터를 준비합니다.

> 💡 **사용 방법**: 이 API로 받은 `input_data`를 LLM API에 전달하여 주간 계획을 생성합니다.

**Query Parameters:**
- `user_id` (integer, required): 사용자 ID

**Request Body:**
```json
{
  "record_id": 1,
  "user_goal_type": "체중감량",
  "user_goal_description": "3개월 내 체지방 5% 감량"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "LLM input 데이터 준비 완료. 프론트엔드에서 LLM API를 호출하세요.",
  "input_data": {
    "user_goal_type": "체중감량",
    "user_goal_description": "3개월 내 체지방 5% 감량",
    "record_id": 1,
    "user_id": 1,
    "measured_at": "2026-01-29T10:00:00",
    "measurements": {
      "기본정보": { ... },
      "체성분": { ... },
      "체중관리": { ... }
    },
    "body_type1": "비만형",
    "body_type2": "표준형",
    "status_analysis_result": "현재 체지방률이 26.5%로...",
    "status_analysis_id": 1
  }
}
```

---

### 5.3 목표 조회

**GET** `/api/goals/{goal_id}`

특정 목표를 조회합니다.

**Path Parameters:**
- `goal_id` (integer, required): 목표 ID

**Response (200 OK):**
```json
{
  "id": 1,
  "user_id": 1,
  "goal_type": "체중감량",
  "goal_description": "3개월 내 체지방 5% 감량",
  "preferences": "채식 선호, 아침 운동 선호",
  "health_specifics": "무릎 부상 있음",
  "is_active": 1,
  "started_at": "2026-01-29T10:00:00",
  "ended_at": null
}
```

---

### 5.4 활성 목표 조회

**GET** `/api/goals/user/{user_id}/active`

사용자의 현재 진행 중인 목표를 조회합니다.

**Path Parameters:**
- `user_id` (integer, required): 사용자 ID

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "goal_type": "체중감량",
    "goal_description": "3개월 내 체지방 5% 감량",
    "preferences": "채식 선호, 아침 운동 선호",
    "health_specifics": "무릎 부상 있음",
    "is_active": 1,
    "started_at": "2026-01-29T10:00:00",
    "ended_at": null
  }
]
```

---

### 5.5 모든 목표 조회

**GET** `/api/goals/user/{user_id}`

사용자의 모든 목표를 조회합니다 (완료된 목표 포함).

**Path Parameters:**
- `user_id` (integer, required): 사용자 ID

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "goal_type": "체중감량",
    "goal_description": "3개월 내 체지방 5% 감량",
    "preferences": "채식 선호, 아침 운동 선호",
    "health_specifics": "무릎 부상 있음",
    "is_active": 1,
    "started_at": "2026-01-29T10:00:00",
    "ended_at": null
  },
  {
    "id": 2,
    "user_id": 1,
    "goal_type": "근육증가",
    "goal_description": "6개월 내 근육량 5kg 증가",
    "preferences": null,
    "health_specifics": null,
    "is_active": 0,
    "started_at": "2025-12-01T10:00:00",
    "ended_at": "2026-01-15T10:00:00"
  }
]
```

---

### 5.6 목표 수정

**PATCH** `/api/goals/{goal_id}`

목표 정보를 수정합니다.

**Path Parameters:**
- `goal_id` (integer, required): 목표 ID

**Request Body:**
```json
{
  "goal_description": "3개월 내 체지방 7% 감량",
  "preferences": "채식 선호, 저녁 운동 선호"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user_id": 1,
  "goal_type": "체중감량",
  "goal_description": "3개월 내 체지방 7% 감량",
  "preferences": "채식 선호, 저녁 운동 선호",
  "health_specifics": "무릎 부상 있음",
  "is_active": 1,
  "started_at": "2026-01-29T10:00:00",
  "ended_at": null
}
```

---

### 5.7 목표 삭제

**DELETE** `/api/goals/{goal_id}`

목표를 삭제합니다.

**Path Parameters:**
- `goal_id` (integer, required): 목표 ID

**Response (200 OK):**
```json
{
  "message": "목표가 삭제되었습니다."
}
```

---

### 5.8 목표 완료 처리

**POST** `/api/goals/{goal_id}/complete`

목표를 완료 상태로 변경합니다.

**Path Parameters:**
- `goal_id` (integer, required): 목표 ID

**Response (200 OK):**
```json
{
  "id": 1,
  "user_id": 1,
  "goal_type": "체중감량",
  "goal_description": "3개월 내 체지방 5% 감량",
  "preferences": "채식 선호, 아침 운동 선호",
  "health_specifics": "무릎 부상 있음",
  "is_active": 1,
  "started_at": "2026-01-29T10:00:00",
  "ended_at": "2026-01-29T15:00:00"
}
```

---

## 6. 주간 계획 API

Base Path: `/api/weekly-plans`

### 6.1 주간 계획 생성

**POST** `/api/weekly-plans/?user_id={user_id}`

사용자의 주간 운동/식단 계획을 생성합니다.

**Query Parameters:**
- `user_id` (integer, required): 사용자 ID

**Request Body:**
```json
{
  "week_number": 1,
  "start_date": "2026-02-03",
  "end_date": "2026-02-09",
  "plan_data": {
    "weekly_summary": "체지방 감량을 위한 1주차 계획",
    "weekly_goal": "주 3회 유산소 운동, 저탄수화물 식단",
    "daily_plans": [
      {
        "day": "월요일",
        "exercise": "유산소 40분",
        "meals": {
          "breakfast": "오트밀, 과일",
          "lunch": "닭가슴살 샐러드",
          "dinner": "두부 스테이크"
        }
      }
    ],
    "tips": ["충분한 수분 섭취", "식사 후 가벼운 산책"]
  },
  "model_version": "gpt-4o-mini"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "user_id": 1,
  "week_number": 1,
  "start_date": "2026-02-03",
  "end_date": "2026-02-09",
  "plan_data": {
    "weekly_summary": "체지방 감량을 위한 1주차 계획",
    "weekly_goal": "주 3회 유산소 운동, 저탄수화물 식단",
    "daily_plans": [...],
    "tips": [...]
  },
  "model_version": "gpt-4o-mini",
  "created_at": "2026-01-29T14:00:00"
}
```

---

### 6.2 주간 계획 조회

**GET** `/api/weekly-plans/{plan_id}`

특정 주간 계획을 조회합니다.

**Path Parameters:**
- `plan_id` (integer, required): 계획 ID

**Response (200 OK):**
```json
{
  "id": 1,
  "user_id": 1,
  "week_number": 1,
  "start_date": "2026-02-03",
  "end_date": "2026-02-09",
  "plan_data": {
    "weekly_summary": "체지방 감량을 위한 1주차 계획",
    "weekly_goal": "주 3회 유산소 운동, 저탄수화물 식단",
    "daily_plans": [...],
    "tips": [...]
  },
  "model_version": "gpt-4o-mini",
  "created_at": "2026-01-29T14:00:00"
}
```

**Error Response (404):**
```json
{
  "detail": "주간 계획을 찾을 수 없습니다."
}
```

---

### 6.3 사용자별 주간 계획 목록 조회

**GET** `/api/weekly-plans/user/{user_id}?limit={limit}`

사용자의 모든 주간 계획을 조회합니다.

**Path Parameters:**
- `user_id` (integer, required): 사용자 ID

**Query Parameters:**
- `limit` (integer, optional, default: 10): 조회할 최대 개수

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "week_number": 1,
    "start_date": "2026-02-03",
    "end_date": "2026-02-09",
    "plan_data": {...},
    "model_version": "gpt-4o-mini",
    "created_at": "2026-01-29T14:00:00"
  },
  {
    "id": 2,
    "user_id": 1,
    "week_number": 2,
    "start_date": "2026-02-10",
    "end_date": "2026-02-16",
    "plan_data": {...},
    "model_version": "gpt-4o-mini",
    "created_at": "2026-02-05T10:00:00"
  }
]
```

---

### 6.4 특정 주차 계획 조회

**GET** `/api/weekly-plans/user/{user_id}/week/{week_number}`

특정 주차의 주간 계획을 조회합니다.

**Path Parameters:**
- `user_id` (integer, required): 사용자 ID
- `week_number` (integer, required): 주차 번호

**Response (200 OK):**
```json
{
  "id": 1,
  "user_id": 1,
  "week_number": 1,
  "start_date": "2026-02-03",
  "end_date": "2026-02-09",
  "plan_data": {
    "weekly_summary": "체지방 감량을 위한 1주차 계획",
    "weekly_goal": "주 3회 유산소 운동, 저탄수화물 식단",
    "daily_plans": [...],
    "tips": [...]
  },
  "model_version": "gpt-4o-mini",
  "created_at": "2026-01-29T14:00:00"
}
```

**Error Response (404):**
```json
{
  "detail": "사용자 1의 1주차 계획을 찾을 수 없습니다."
}
```

---

### 6.5 주간 계획 수정

**PATCH** `/api/weekly-plans/{plan_id}`

주간 계획 내용을 수정합니다.

**Path Parameters:**
- `plan_id` (integer, required): 계획 ID

**Request Body:**
```json
{
  "plan_data": {
    "weekly_summary": "수정된 1주차 계획",
    "weekly_goal": "주 4회 유산소 운동으로 증가",
    "daily_plans": [...]
  }
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user_id": 1,
  "week_number": 1,
  "start_date": "2026-02-03",
  "end_date": "2026-02-09",
  "plan_data": {
    "weekly_summary": "수정된 1주차 계획",
    "weekly_goal": "주 4회 유산소 운동으로 증가",
    "daily_plans": [...]
  },
  "model_version": "gpt-4o-mini",
  "created_at": "2026-01-29T14:00:00"
}
```

**Error Response (404):**
```json
{
  "detail": "주간 계획을 찾을 수 없습니다."
}
```

---

### 6.6 주간 계획 삭제

**DELETE** `/api/weekly-plans/{plan_id}`

주간 계획을 삭제합니다.

**Path Parameters:**
- `plan_id` (integer, required): 계획 ID

**Response (200 OK):**
```json
{
  "message": "주간 계획이 삭제되었습니다."
}
```

**Error Response (404):**
```json
{
  "detail": "주간 계획을 찾을 수 없습니다."
}
```

---

## 데이터 스키마

### InBodyData 구조

인바디 데이터는 다음과 같은 중첩 구조를 가집니다:

```json
{
  "기본정보": {
    "신장": 170.0,
    "연령": 30,
    "성별": "남성"
  },
  "체성분": {
    "체수분": 41.7,
    "단백질": 11.4,
    "무기질": 3.99,
    "체지방": 20.6
  },
  "체중관리": {
    "체중": 77.7,
    "골격근량": 32.5,
    "체지방량": 20.6,
    "적정체중": 67.2,
    "체중조절": -10.5,
    "지방조절": -10.5,
    "근육조절": 0.0
  },
  "비만분석": {
    "BMI": 26.9,
    "체지방률": 26.5,
    "복부지방률": 0.93,
    "내장지방레벨": 8,
    "비만도": 122
  },
  "연구항목": {
    "제지방량": 57.1,
    "기초대사량": 1603,
    "권장섭취열량": 2267
  },
  "부위별근육분석": {
    "왼쪽팔": "표준",
    "오른쪽팔": "표준",
    "복부": "표준",
    "왼쪽하체": "표준",
    "오른쪽하체": "표준"
  },
  "부위별체지방분석": {
    "왼쪽팔": "표준이상",
    "오른쪽팔": "표준이상",
    "복부": "표준이상",
    "왼쪽하체": "표준이상",
    "오른쪽하체": "표준이상"
  }
}
```

### 필드 검증 규칙

#### 기본정보
- `신장`: 50 < 값 < 300 (cm)
- `연령`: 0 < 값 < 150 (세)
- `성별`: "남성", "여성", "남", "여" (자동으로 "남성"/"여성"으로 정규화)

#### 체중관리
- `체중`: 10 < 값 < 500 (kg)
- `골격근량`: 0 < 값 < 200 (kg)

#### 비만분석
- `BMI`: 10 < 값 < 100
- `체지방률`: 0 ≤ 값 ≤ 100 (%)
- `복부지방률`: 0 ≤ 값 ≤ 10
- `내장지방레벨`: 1 ≤ 값 ≤ 20

---

## 에러 처리

### HTTP 상태 코드

| 코드 | 설명 |
|------|------|
| 200 | 성공 (조회, 수정, 삭제) |
| 201 | 생성 성공 |
| 400 | 잘못된 요청 |
| 401 | 인증 실패 (로그인 실패) |
| 404 | 리소스를 찾을 수 없음 |
| 422 | 데이터 검증 실패 |
| 503 | 서비스 일시 사용 불가 (OCR 엔진 로딩 중) |

### 에러 응답 형식

**401 Unauthorized:**
```json
{
  "detail": "이메일 또는 비밀번호가 올바르지 않습니다."
}
```

**404 Not Found:**
```json
{
  "detail": "사용자를 찾을 수 없습니다."
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "기본정보", "신장"],
      "msg": "Input should be greater than 50",
      "type": "greater_than"
    }
  ]
}
```

**503 Service Unavailable:**
```json
{
  "detail": "OCR 엔진이 아직 로딩 중입니다. 잠시 후 다시 시도해주세요."
}
```

---

## 주요 워크플로우

### 1. 인바디 OCR 등록 및 분석

```
1. POST /api/health-records/ocr/extract
   → 인바디 이미지 업로드
   → OCR 원시 데이터 받기

2. 프론트엔드에서 사용자가 데이터 확인 및 수정

3. POST /api/health-records/ocr/validate
   → 검증된 데이터 전송
   → 건강 기록 저장 + 체형 분석 자동 수행

4. GET /api/health-records/{record_id}/analysis/prepare
   → LLM 분석용 입력 데이터 준비

5. 프론트엔드에서 LLM API 호출 (별도)
   → 건강 상태 분석 결과 받기

6. POST /api/analysis/{record_id}
   → 분석 결과 저장
```


### 2. 목표 설정 및 주간 계획 생성

```
1. POST /api/goals/
   → 목표 생성

2. POST /api/goals/plan/prepare
   → 주간 계획 생성용 입력 데이터 준비
   → 최신 건강 기록 + 분석 결과 포함

3. 프론트엔드에서 LLM API 호출 (별도)
   → 주간 계획 생성 (plan_data 받기)

4. POST /api/weekly-plans/?user_id={user_id}
   → LLM이 생성한 주간 계획 저장
```

### 3. 주간 계획 조회 및 관리

```
1. GET /api/weekly-plans/user/{user_id}
   → 사용자의 모든 주간 계획 목록 조회

2. GET /api/weekly-plans/user/{user_id}/week/{week_number}
   → 특정 주차 계획 조회

3. PATCH /api/weekly-plans/{plan_id}
   → 계획 내용 수정

4. DELETE /api/weekly-plans/{plan_id}
   → 계획 삭제
```


---

## 참고사항

### 1. OCR 엔진 로딩
- 서버 시작 시 OCR 엔진이 백그라운드에서 로딩됩니다
- 로딩 중에는 `/api/health-records/ocr/extract` 호출 시 503 에러가 발생합니다
- 일반적으로 서버 시작 후 10-30초 내에 로딩이 완료됩니다

### 2. 데이터 검증
- OCR 추출 데이터는 검증 없이 반환됩니다 (null 값 포함 가능)
- 프론트엔드에서 사용자가 데이터를 확인하고 수정해야 합니다
- `/ocr/validate` 호출 시 Pydantic으로 최종 검증이 수행됩니다

### 3. 체형 분석
- `/ocr/validate` 호출 시 자동으로 체형 분석이 수행됩니다
- 필수 필드가 누락된 경우 체형 분석 없이 인바디 데이터만 저장됩니다
- 체형 분석 결과는 `body_type1` (1차), `body_type2` (2차)로 저장됩니다

### 4. LLM 통합
- LLM API 호출은 프론트엔드에서 직접 수행합니다
- 백엔드는 LLM 입력 데이터 준비 및 결과 저장만 담당합니다
- `/analysis/prepare`와 `/goals/plan/prepare`로 입력 데이터를 받아갑니다

---

## 문의

API 관련 문의사항이 있으시면 백엔드 팀에게 연락주세요.

**자동 생성 문서**: http://localhost:8000/docs
