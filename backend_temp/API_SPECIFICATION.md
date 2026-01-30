# InBody OCR API Specification

The InBody OCR API provides endpoints for user management (signup/login), InBody image processing, and recording health data.

- **Base URL**: `http://localhost:5000`
- **Content-Type**: `application/json`

---

## 1. Authentication & User Management

### Sign Up
Registers a new user.

- **URL**: `/api/signup`
- **Method**: `POST`
- **Body**: [UserSignup](#usersignup)
- **Success Response**: `200 OK` - [UserResponse](#userresponse)
- **Error Response**: `400 Bad Request` (Email already exists), `500 Internal Server Error`

### Login
Authenticates a user and returns profile data.

- **URL**: `/api/login`
- **Method**: `POST`
- **Body**: [UserLogin](#userlogin)
- **Success Response**: `200 OK` - [UserResponse](#userresponse)
- **Error Response**: `401 Unauthorized` (Invalid credentials)

---

## 2. InBody Image Processing

### Process InBody Image
Uploads an InBody report image and extracts numerical data using OCR.

- **URL**: `/api/process`
- **Method**: `POST`
- **Body (Multipart/Form-Data)**:
    - `file`: Image file (`png`, `jpg`, `jpeg`, `webp`, `bmp`)
    - `auto_perspective`: `bool` (Default: `true`)
    - `skew_threshold`: `float` (Default: `15.0`)
- **Success Response**: `200 OK`
    ```json
    {
      "success": true,
      "data": {
        "raw": { "체중": "70.5", ... },
        "structured": { ... }
      }
    }
    ```
- **Error Response**: `400 Bad Request` (Invalid image), `500 Internal Server Error`

### Download OCR Results
Generates a JSON file for the provided data.

- **URL**: `/api/download`
- **Method**: `POST`
- **Body**: `Dict[str, Any]` (JSON data to be downloaded)
- **Success Response**: `200 OK` (File Download: `inbody_result.json`)

---

## 3. User Goal & Records

### Update Goals
Updates the user's health goals.

- **URL**: `/api/users/{user_id}/goal`
- **Method**: `PUT`
- **Path Parameters**: `user_id` (int)
- **Body**: [UserGoalUpdate](#usergoalupdate)
- **Success Response**: `200 OK` - [UserResponse](#userresponse)

### Update Daily Records
Records food intake or exercise for a specific date.

- **URL**: `/api/users/{user_id}/records`
- **Method**: `POST`
- **Path Parameters**: `user_id` (int)
- **Body**: [UserRecordUpdate](#userrecordupdate)
- **Success Response**: `200 OK` - [UserResponse](#userresponse)

---

## 4. Debug & System

### Health Check
- **URL**: `/api/health`
- **Method**: `GET`
- **Success Response**: `{"status": "healthy", "service": "..."}`

### List Users (Debug)
- **URL**: `/api/debug/users`
- **Method**: `GET`
- **Success Response**: JSON array of user profiles (excluding passwords)

---

## Data Models (Schemas)

### UserSignup
```json
{
  "email": "string",
  "password": "string",
  "gender": "string",
  "age": 0,
  "height": 0.0,
  "startWeight": 0.0,
  "targetWeight": 0.0,
  "goalType": "string",
  "activityLevel": "string",
  "goal": "string",
  "preferredExercises": ["string"],
  "medicalConditions": ["string"],
  "medicalConditionsDetail": "string",
  "inbodyData": {}
}
```

### UserLogin
```json
{
  "email": "string",
  "password": "string"
}
```

### UserGoalUpdate
```json
{
  "start_weight": 0.0,
  "target_weight": 0.0,
  "goal_type": "string",
  "goal_description": "string"
}
```

### UserRecordUpdate
```json
{
  "date": "YYYY-MM-DD",
  "food": [],
  "exercise": []
}
```

### UserResponse
```json
{
  "id": 0,
  "email": "string",
  "is_active": true,
  "gender": "string",
  "age": 0,
  "height": 0.0,
  "start_weight": 0.0,
  "target_weight": 0.0,
  "goal_type": "string",
  "activity_level": "string",
  "goal_description": "string",
  "inbody_data": {},
  "daily_records": {}
}
```
