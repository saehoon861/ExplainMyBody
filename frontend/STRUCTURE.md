# 프론트엔드 폴더 구조 (현업 스타일)

## 📁 폴더 구조

```
src/
├── pages/              # 페이지 컴포넌트 (라우트)
│   ├── Auth/           # 인증 관련 페이지
│   │   ├── Login.jsx
│   │   ├── Signup.jsx
│   │   ├── SignupSuccess.jsx
│   │   ├── SplashScreen.jsx
│   │   └── SplashScreen*.css
│   ├── Dashboard/      # 대시보드
│   │   └── Dashboard.jsx
│   ├── InBody/         # 인바디 OCR 분석
│   │   └── InBodyAnalysis.jsx
│   ├── Chatbot/        # AI 챗봇
│   │   ├── Chatbot.jsx
│   │   └── ChatbotSelector.jsx
│   ├── Exercise/       # 운동 가이드
│   │   ├── ExerciseGuide.jsx
│   │   └── WorkoutPlan.jsx
│   └── Profile/        # 프로필
│       └── Profile.jsx
│
├── components/         # 재사용 가능한 공통 컴포넌트
│   ├── common/         # 공통 UI 컴포넌트
│   │   ├── Logo.jsx
│   │   ├── LoadingSpinner.jsx
│   │   ├── LoadingSpinner.css
│   │   ├── CustomCursor.jsx
│   │   └── CustomCursor.css
│   └── layout/         # 레이아웃 컴포넌트
│       └── MainLayout.jsx
│
├── services/           # API 호출 로직 (백엔드 개발자용)
│   ├── api.js          # API 기본 설정
│   ├── authService.js  # 로그인, 회원가입 API
│   ├── inbodyService.js # 인바디 OCR API
│   └── chatService.js  # 챗봇 API
│
├── styles/             # 전역 스타일
│   ├── index.css       # 전역 스타일
│   ├── App.css
│   ├── AppLight.css
│   ├── Login.css
│   └── LoginLight.css
│
├── utils/              # 유틸리티 함수
├── assets/             # 이미지, 폰트 등 정적 자원
├── App.jsx             # 메인 앱 (라우팅)
└── main.jsx            # 진입점
```

## 🎯 설계 원칙

### 1. **pages/** - 페이지 컴포넌트
- 라우트에 직접 연결되는 페이지
- 도메인별로 폴더 분리 (Auth, Dashboard, InBody...)
- 각 페이지는 독립적으로 관리

### 2. **components/** - 재사용 컴포넌트
- 여러 페이지에서 공통으로 사용하는 컴포넌트
- `common/`: UI 컴포넌트 (Logo, LoadingSpinner...)
- `layout/`: 레이아웃 컴포넌트 (MainLayout...)

### 3. **services/** - API 호출 로직
- 백엔드 API 호출 로직을 한 곳에 모음
- 백엔드 개발자가 API 변경 시 여기만 보면 됨!
- 각 도메인별로 서비스 파일 분리

### 4. **styles/** - 전역 스타일
- 여러 페이지에서 공유하는 CSS
- 컴포넌트별 스타일은 해당 컴포넌트 폴더에 위치

## 🔄 백엔드 개발자를 위한 가이드

### API 엔드포인트 찾기
모든 API 호출은 `services/` 폴더에 있습니다:

```javascript
// 예시: 로그인 API 호출
// frontend/src/services/authService.js
export const login = async (email, password) => {
    return await apiRequest('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
    });
};
```

### API 변경 시 수정할 파일
1. **엔드포인트 변경**: `services/*.js` 파일 수정
2. **응답 형식 변경**: 해당 서비스 파일의 JSDoc 주석 업데이트

## 📝 import 경로 예시

```javascript
// 페이지 import
import Login from './pages/Auth/Login';
import Dashboard from './pages/Dashboard/Dashboard';

// 공통 컴포넌트 import
import Logo from './components/common/Logo';
import MainLayout from './components/layout/MainLayout';

// 서비스 import
import { login } from './services/authService';
import { extractInbodyData } from './services/inbodyService';

// 스타일 import
import './styles/AppLight.css';
```

## 🚀 장점

1. **명확한 구조**: 파일 역할이 명확하여 찾기 쉬움
2. **유지보수성**: 각 파일의 책임이 명확하여 수정 용이
3. **협업 친화적**: 백엔드 개발자도 API 로직을 쉽게 파악
4. **확장성**: 새로운 페이지/기능 추가가 용이
5. **재사용성**: 공통 컴포넌트와 서비스 로직의 재사용

## ⚡ 다음 단계 (선택사항)

향후 필요시 추가할 수 있는 폴더:
- `hooks/`: 커스텀 React 훅
- `contexts/`: Context API
- `constants/`: 상수 정의
- `types/`: TypeScript 타입 정의
