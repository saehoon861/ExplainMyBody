# 목업 모드 중앙 관리 설정

전체 애플리케이션의 목업 모드를 **한 곳**에서 관리할 수 있도록 환경 변수로 중앙화했습니다.

---

## 🎯 사용 방법

### `.env` 파일에서 목업 모드 켜기/끄기

```bash
# 목업 모드 ON (개발/테스트 시)
VITE_USE_MOCK_DATA=true

# 목업 모드 OFF (실제 API 사용)
VITE_USE_MOCK_DATA=false
```

### 변경 후 서버 재시작

환경 변수 변경 후에는 **반드시 프론트엔드 개발 서버를 재시작**해야 합니다:

```bash
# 터미널에서 Ctrl+C로 종료 후
npm run dev
```

---

## ✅ 적용된 파일들

다음 4개 파일이 중앙화된 환경 변수를 사용합니다:

1. **`Chatbot.jsx`** - 챗봇 대화 기능
2. **`ChatbotSelector.jsx`** - 챗봇 선택 화면
3. **`InBodyAnalysis.jsx`** - 인바디 분석 업로드
4. **`Dashboard.jsx`** - 대시보드 데이터 표시

더 이상 각 파일을 일일이 수정할 필요 없이, `.env` 파일 하나만 수정하면 됩니다!

---

## 🔧 환경별 설정 예시

### 로컬 개발 (목업 사용)
```bash
VITE_USE_MOCK_DATA=true
VITE_API_URL=http://localhost:5000
```

### 프로덕션 배포 (실제 API)
```bash
VITE_USE_MOCK_DATA=false
VITE_API_URL=https://api.yourdomain.com
```

---

## ⚠️ 주의사항

- `.env` 파일은 Git에 커밋하지 마세요 (이미 `.gitignore`에 포함되어 있음)
- 팀원과 공유할 때는 `.env.example` 파일을 사용하세요
- 환경 변수 변경 시 반드시 서버 재시작이 필요합니다
