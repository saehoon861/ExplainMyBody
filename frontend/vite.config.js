import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'mask-icon.svg'],
      manifest: {
        name: 'ExplainMyBody',
        short_name: 'EMB',
        description: '인바디 리포트 정밀 분석 서비스',
        theme_color: '#0f172a',
        background_color: '#0f172a',
        display: 'standalone',
        icons: [
          { src: 'pwa-192x192.png', sizes: '192x192', type: 'image/png' },
          { src: 'pwa-512x512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' }
        ]
      },
      devOptions: {
        enabled: false // 개발 모드 캐시 방지
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,jpg}'],
        runtimeCaching: [
          // OCR 및 이미지 업로드 엔드포인트는 캐싱하지 않음
          {
            urlPattern: /\/api\/health-records\/ocr\/.*/i,
            handler: 'NetworkOnly',
            options: { cacheName: 'ocr-no-cache' }
          },
          {
            urlPattern: /^https:\/\/api\.explainmybody\.com\/health-records\/ocr\/.*/i,
            handler: 'NetworkOnly',
            options: { cacheName: 'ocr-api-no-cache' }
          },
          // 나머지 API는 NetworkFirst 캐싱
          {
            urlPattern: /^https:\/\/api\.explainmybody\.com\/.*/i,
            handler: 'NetworkFirst',
            options: { cacheName: 'api-cache' }
          },
          {
            urlPattern: /\/api\/.*/i,
            handler: 'NetworkFirst',
            options: { cacheName: 'local-api-cache' }
          }
        ]
      }
    })
  ],
  server: {
    // 1. 외부 접속 허용 (에러 해결 핵심)
    allowedHosts: [
      'bowl-jon-ideal-harder.trycloudflare.com',
      'itchy-olives-matter.loca.lt'
    ],
    // 2. 백엔드 연결 설정 (CORS 및 경로 관리)
    proxy: {
      '/api': {
        // 프론트엔드에서 /api 요청 시 로컬 백엔드로 전달
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        // 백엔드(FastAPI) 코드에 /api 경로가 없다면 아래 rewrite 활성화
        // rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})