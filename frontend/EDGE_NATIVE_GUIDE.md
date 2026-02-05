# 🚀 엣지 네이티브 아키텍처 구현 가이드

## 📊 현재 상태

### ✅ 이미 구현됨
- [x] PWA (Progressive Web App)
- [x] Service Worker (workbox)
- [x] Static Build (Vite)
- [x] 지능적 적응 (Intelligent Adaptation)
- [x] 반응형 디자인

### ❌ 구현 필요
- [ ] API 응답 캐싱
- [ ] 동적 코드 분할 (Code Splitting)
- [ ] 리소스 프리페칭 (Prefetching)
- [ ] Edge Functions
- [ ] CDN 최적화 설정
- [ ] 오프라인 지원 강화

---

## 🎯 구현 단계

## Phase 1: Service Worker 강화 (즉시 가능)

### 1.1 API 캐싱 전략 추가

현재 Service Worker는 정적 파일만 캐싱합니다. API 응답도 캐싱하도록 확장:

**파일**: `vite.config.js`

```javascript
import { VitePWA } from 'vite-plugin-pwa'

export default {
  plugins: [
    VitePWA({
      registerType: 'autoUpdate',
      workbox: {
        // 기존 정적 파일 캐싱
        globPatterns: ['**/*.{js,css,html,ico,png,svg,jpg}'],

        // API 캐싱 전략 추가
        runtimeCaching: [
          {
            // 건강 기록 API
            urlPattern: /^https:\/\/api\.explainmybody\.com\/health-records\/.*/i,
            handler: 'CacheFirst', // 캐시 우선
            options: {
              cacheName: 'health-records-cache',
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 60 * 60 * 24 * 7, // 7일
              },
              cacheableResponse: {
                statuses: [0, 200],
              },
            },
          },
          {
            // LLM API
            urlPattern: /^https:\/\/api\.explainmybody\.com\/llm\/.*/i,
            handler: 'NetworkFirst', // 네트워크 우선
            options: {
              cacheName: 'llm-cache',
              expiration: {
                maxEntries: 30,
                maxAgeSeconds: 60 * 60, // 1시간
              },
              networkTimeoutSeconds: 5,
            },
          },
          {
            // 이미지 CDN
            urlPattern: /^https:\/\/cdn\.explainmybody\.com\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'image-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60 * 24 * 30, // 30일
              },
            },
          },
        ],
      },
    }),
  ],
}
```

**캐싱 전략**:
- `CacheFirst`: 캐시 우선 (정적 데이터)
- `NetworkFirst`: 네트워크 우선 (동적 데이터)
- `StaleWhileRevalidate`: 캐시 반환 후 백그라운드 갱신

---

## Phase 2: 동적 코드 분할 (Code Splitting)

### 2.1 React.lazy를 사용한 라우트 분할

**파일**: `frontend/src/App.jsx`

```javascript
import React, { useState, Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LoadingSpinner from './components/common/LoadingSpinner';

// 즉시 로드 (중요한 페이지)
import Login from './pages/Auth/Login';
import MainLayout from './components/layout/MainLayout';

// 지연 로드 (덜 중요한 페이지)
const Dashboard = lazy(() => import('./pages/Dashboard/Dashboard'));
const InBodyAnalysis = lazy(() => import('./pages/InBody/InBodyAnalysis'));
const Chatbot = lazy(() => import('./pages/Chatbot/Chatbot'));
const ChatbotSelector = lazy(() => import('./pages/Chatbot/ChatbotSelector'));
const WorkoutPlan = lazy(() => import('./pages/Exercise/WorkoutPlan'));
const ExerciseGuide = lazy(() => import('./pages/Exercise/ExerciseGuide'));
const Profile = lazy(() => import('./pages/Profile/Profile'));

function App() {
  return (
    <Router>
      <Suspense fallback={<LoadingSpinner />}>
        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/login" element={<Login />} />

          <Route path="/dashboard" element={<MainLayout><Dashboard /></MainLayout>} />
          <Route path="/inbody" element={<MainLayout><InBodyAnalysis /></MainLayout>} />
          <Route path="/chatbot" element={<MainLayout><ChatbotSelector /></MainLayout>} />
          <Route path="/chatbot/:botType" element={<MainLayout><Chatbot /></MainLayout>} />
          <Route path="/workout-plan" element={<MainLayout><WorkoutPlan /></MainLayout>} />
          <Route path="/exercise-guide" element={<MainLayout><ExerciseGuide /></MainLayout>} />
          <Route path="/profile" element={<MainLayout><Profile /></MainLayout>} />
        </Routes>
      </Suspense>
    </Router>
  );
}
```

**효과**: 초기 번들 크기 50-60% 감소

---

### 2.2 Chart 라이브러리 동적 로드

**파일**: `frontend/src/pages/Dashboard/Dashboard.jsx`

```javascript
import { lazy, Suspense } from 'react';

// Chart 컴포넌트 분리
const ChartComponent = lazy(() => import('../components/InBodyChart'));

// Dashboard에서 사용
<Suspense fallback={<div>차트 로딩 중...</div>}>
  <ChartComponent data={chartData} />
</Suspense>
```

**효과**: recharts 라이브러리 (~200KB) 별도 로드

---

## Phase 3: 리소스 프리페칭

### 3.1 Link Prefetching Hook

**파일**: `frontend/src/hooks/usePrefetch.js`

```javascript
import { useEffect } from 'react';

export const usePrefetch = (routes) => {
  useEffect(() => {
    if ('requestIdleCallback' in window) {
      // 브라우저가 한가할 때 프리페치
      requestIdleCallback(() => {
        routes.forEach((route) => {
          const link = document.createElement('link');
          link.rel = 'prefetch';
          link.as = 'script';
          link.href = route;
          document.head.appendChild(link);
        });
      });
    }
  }, [routes]);
};

// 사용 예시
function Dashboard() {
  // 대시보드에서 자주 가는 페이지 프리페치
  usePrefetch([
    '/src/pages/Chatbot/Chatbot.jsx',
    '/src/pages/InBody/InBodyAnalysis.jsx',
  ]);

  return <div>Dashboard Content</div>;
}
```

---

### 3.2 Intersection Observer를 사용한 스마트 프리페치

```javascript
import { useEffect, useRef } from 'react';

export const useLinkPrefetch = () => {
  useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const link = entry.target;
          const href = link.getAttribute('href');

          // 링크가 보이면 해당 페이지 프리페치
          const prefetchLink = document.createElement('link');
          prefetchLink.rel = 'prefetch';
          prefetchLink.href = href;
          document.head.appendChild(prefetchLink);
        }
      });
    });

    // 모든 링크 관찰
    document.querySelectorAll('a[href^="/"]').forEach((link) => {
      observer.observe(link);
    });

    return () => observer.disconnect();
  }, []);
};
```

---

## Phase 4: CDN 배포 최적화

### 4.1 Cloudflare Pages 배포

**설정 파일**: `cloudflare-pages.toml` (프로젝트 루트)

```toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

[build.environment]
  NODE_VERSION = "20"

# 캐싱 설정
[[headers]]
  for = "/assets/*"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"

[[headers]]
  for = "/*.js"
  [headers.values]
    Cache-Control = "public, max-age=604800"

[[headers]]
  for = "/*.css"
  [headers.values]
    Cache-Control = "public, max-age=604800"

[[headers]]
  for = "/index.html"
  [headers.values]
    Cache-Control = "public, max-age=0, must-revalidate"
```

**배포 단계**:
1. Cloudflare Pages 가입
2. GitHub 연동
3. 프로젝트 선택
4. 빌드 설정: `npm run build`, `dist`
5. 배포 완료!

---

### 4.2 Vercel 배포 (대안)

**설정 파일**: `vercel.json`

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ],
  "headers": [
    {
      "source": "/assets/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    },
    {
      "source": "/(.*).js",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=604800"
        }
      ]
    }
  ]
}
```

---

## Phase 5: Edge Functions (선택적)

### 5.1 Cloudflare Workers 예시

API 요청을 엣지에서 처리하여 레이턴시 감소:

**파일**: `workers/api-proxy.js`

```javascript
export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // API 프록시
    if (url.pathname.startsWith('/api/')) {
      const cache = caches.default;

      // 캐시 확인
      let response = await cache.match(request);

      if (!response) {
        // 오리진 서버로 요청
        response = await fetch(`https://api.explainmybody.com${url.pathname}`, {
          headers: request.headers,
          method: request.method,
          body: request.body,
        });

        // 응답 캐싱 (GET 요청만)
        if (request.method === 'GET' && response.ok) {
          response = new Response(response.body, response);
          response.headers.set('Cache-Control', 'max-age=3600');
          await cache.put(request, response.clone());
        }
      }

      return response;
    }

    return fetch(request);
  },
};
```

---

## 📈 성능 개선 예측

### Before (현재)
- 초기 로드: ~690KB (gzipped: ~210KB)
- FCP (First Contentful Paint): ~2.5s
- TTI (Time to Interactive): ~4.0s

### After (엣지 네이티브)
- 초기 로드: ~200KB (gzipped: ~60KB) ⬇️ 70%
- FCP: ~0.8s ⬇️ 68%
- TTI: ~1.5s ⬇️ 62%
- API 응답: ~50ms (엣지 캐싱) ⬇️ 80%

---

## 🛠️ 구현 순서

### 즉시 시작 가능 (로컬에서)
1. ✅ **Code Splitting** (App.jsx 수정)
2. ✅ **API 캐싱** (vite.config.js 수정)
3. ✅ **Prefetching** (훅 추가)

### CDN 배포 필요
4. 🌐 **Cloudflare Pages** 또는 **Vercel** 배포
5. 🌐 **커스텀 도메인** 연결

### 고급 기능 (선택)
6. ⚡ **Edge Functions** (Cloudflare Workers)
7. ⚡ **Edge SSR** (Vercel Edge Runtime)

---

## 📝 체크리스트

- [ ] vite.config.js에 API 캐싱 전략 추가
- [ ] App.jsx에 React.lazy 적용
- [ ] LoadingSpinner 컴포넌트 확인
- [ ] usePrefetch 훅 생성
- [ ] Chart 컴포넌트 분리
- [ ] Cloudflare Pages 계정 생성
- [ ] GitHub 연동
- [ ] 배포 테스트
- [ ] 성능 측정 (Lighthouse)
- [ ] 모니터링 설정

---

## 🔗 참고 자료

- [Vite Code Splitting](https://vitejs.dev/guide/features.html#code-splitting)
- [Workbox Strategies](https://developer.chrome.com/docs/workbox/modules/workbox-strategies/)
- [Cloudflare Pages](https://pages.cloudflare.com/)
- [Vercel](https://vercel.com/)
- [Web.dev: Code Splitting](https://web.dev/code-splitting/)

---

**구현 일자**: 2026-01-30
**문서 버전**: 1.0
