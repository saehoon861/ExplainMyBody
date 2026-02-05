# API Specification: User Details & Goals (v2)

기존 `/api/goals`가 **`/api/details`**로 변경되었습니다.
이 문서는 프론트엔드 개발자가 백엔드 코드 확인 없이 연동할 수 있도록 **모든 필드와 제약조건**을 명시합니다.

## Base URL
`/api/details`

---

## 1. Goal (목표) 관리

### 1-1. 목표 조회
- **URL**: `GET /api/details/{id}/goal`
- **Description**: 목표 설정 창에서 사용. 목표 관련 데이터만 추출하여 사용하세요.
- **Response** (200 OK):
  ```json
  {
    "id": 1,
    "user_id": 101,
    "goal_type": "다이어트",         // [표시] 목표 유형
    "goal_description": "건강하게 살빼기", // [표시] 재활 상세설명
    "target_weight": 70.5,          // [표시] 목표 체중 (Parsed)
    "start_weight": 80.0,           // [표시] 시작 체중 (Parsed)
    
    // 아래 필드는 무시 (Info 영역)
    "preferences": "...",
    "health_specifics": "...",
    "is_active": 1,
    "started_at": "2023-01-01T10:00:00",
    "ended_at": null
  }
  ```

### 1-2. 목표 수정
- **URL**: `PATCH /api/details/{id}/goal`
- **Description**: 목표 정보만 수정합니다. `preferences` 포함 시 에러 발생.
- **Request Body**:
  ```json
  {
    "goal_type": "근육 증가",
    "goal_description": "{\"target_weight\": 75.0, \"start_weight\": 70.0, \"description\": \"근육량 3kg 증량\"}"
  }
  ```
  > **Note**: `goal_description`은 현재 프론트엔드에서 JSON stringify해서 보내야 합니다. (기존 로직 유지)

- **Response** (200 OK): `UserDetailResponse` (위와 동일)

- **Error** (400 Bad Request):
  - `preferences` 또는 `health_specifics` 필드를 포함한 경우.
  ```json
  { "detail": "Goal 수정 엔드포인트에서는 'preferences' 필드를 수정할 수 없습니다. /info 엔드포인트를 사용하세요." }
  ```

---

## 2. Info (상세 정보) 관리

### 2-1. 상세 정보 조회
- **URL**: `GET /api/details/{id}/info`
- **Description**: 선호도/특이사항 설정 창에서 사용.
- **Response** (200 OK):
  ```json
  {
    "id": 1,
    "user_id": 101,
    "preferences": "채식 선호, 짠 음식 싫어함",   // [표시] 선호도
    "health_specifics": "무릎 통증 있음",           // [표시] 특이사항
    
    // 아래 필드는 무시 (Goal 영역)
    "goal_type": "...",
    "target_weight": 0.0,
    "start_weight": 0.0
  }
  ```

### 2-2. 상세 정보 수정
- **URL**: `PATCH /api/details/{id}/info`
- **Description**: 선호도/특이사항만 수정합니다. `goal_type` 포함 시 에러 발생.
- **Request Body**:
  ```json
  {
    "preferences": "매운 음식 잘 못 먹음",
    "health_specifics": "허리 디스크 초기"
  }
  ```

- **Response** (200 OK): `UserDetailResponse`

- **Error** (400 Bad Request):
  - `goal_type` 또는 `goal_description` 필드를 포함한 경우.
  ```json
  { "detail": "Info 수정 엔드포인트에서는 'goal_type' 필드를 수정할 수 없습니다. /goal 엔드포인트를 사용하세요." }
  ```

---

## 3. General (전체 관리)

### 3-1. 상세정보 생성
- **URL**: `POST /api/details/`
- **Request Body**:
  ```json
  {
    "goal_type": "체중 감량",
    "goal_description": "...",
    "preferences": "없음",
    "health_specifics": "없음",
    "is_active": 1
  }
  ```

### 3-2. 전체 조회
- **URL**: `GET /api/details/{id}`
- **Description**: 모든 필드를 제한 없이 조회.

### 3-3. 전체 수정
- **URL**: `PATCH /api/details/{id}`
- **Description**: 모든 필드를 제한 없이 수정 가능 (Admin 또는 통합 수정 페이지용).
- **Request Body**: 모든 필드 허용.

### 3-4. 삭제
- **URL**: `DELETE /api/details/{id}`
- **Description**: 해당 ID의 상세정보(목표 포함)를 삭제.

---

## 4. Collections (목록 조회)

- **GET /api/details/user/{user_id}/active**: 사용자의 '진행 중'인 목표 목록
- **GET /api/details/user/{user_id}**: 사용자의 전체 히스토리
