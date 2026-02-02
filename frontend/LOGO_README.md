# ExplainMyBody Logo & PWA Icons

## 로고 파일

### SVG 파일
- `public/logo.svg` - 메인 로고 (512x512)
- `public/favicon.svg` - 파비콘 (32x32)

### React 컴포넌트
- `src/components/Logo.jsx` - React 로고 컴포넌트

## React 컴포넌트 사용법

```jsx
import Logo from './components/Logo';

// 아이콘만
<Logo variant="icon" size="small" />

// 풀 로고 (텍스트 포함)
<Logo variant="full" size="medium" />

// 사이즈: small, medium, large, icon
```

## PWA 아이콘 생성 방법

현재 `manifest.json`에는 PNG 아이콘이 필요합니다. SVG를 PNG로 변환해야 합니다.

### 온라인 변환 도구 사용

1. [CloudConvert](https://cloudconvert.com/svg-to-png) 또는 [Convertio](https://convertio.co/kr/svg-png/) 접속
2. `public/logo.svg` 업로드
3. 다음 크기로 변환:
   - 192x192px → `public/icon-192.png`
   - 512x512px → `public/icon-512.png`
   - 192x192px (safe zone 20% 추가) → `public/icon-maskable-192.png`
   - 512x512px (safe zone 20% 추가) → `public/icon-maskable-512.png`

### 커맨드라인 사용 (ImageMagick)

```bash
# ImageMagick 설치
sudo apt-get install imagemagick  # Ubuntu/Debian
brew install imagemagick          # macOS

# SVG → PNG 변환
convert public/logo.svg -resize 192x192 public/icon-192.png
convert public/logo.svg -resize 512x512 public/icon-512.png

# Maskable 아이콘 (safe zone 추가)
convert public/logo.svg -resize 154x154 -gravity center -extent 192x192 -background white public/icon-maskable-192.png
convert public/logo.svg -resize 410x410 -gravity center -extent 512x512 -background white public/icon-maskable-512.png
```

### Node.js 스크립트 사용

`package.json`에 추가:
```json
{
  "scripts": {
    "generate-icons": "node scripts/generate-icons.js"
  },
  "devDependencies": {
    "sharp": "^0.33.0"
  }
}
```

`scripts/generate-icons.js` 생성:
```javascript
const sharp = require('sharp');
const fs = require('fs');

const sizes = [
  { size: 192, name: 'icon-192.png' },
  { size: 512, name: 'icon-512.png' },
];

const maskableSizes = [
  { size: 192, name: 'icon-maskable-192.png' },
  { size: 512, name: 'icon-maskable-512.png' },
];

async function generateIcons() {
  const svgBuffer = fs.readFileSync('public/logo.svg');

  // 일반 아이콘
  for (const { size, name } of sizes) {
    await sharp(svgBuffer)
      .resize(size, size)
      .png()
      .toFile(`public/${name}`);
    console.log(`✓ Generated ${name}`);
  }

  // Maskable 아이콘 (safe zone 20%)
  for (const { size, name } of maskableSizes) {
    const iconSize = Math.round(size * 0.8);
    await sharp(svgBuffer)
      .resize(iconSize, iconSize)
      .extend({
        top: Math.round((size - iconSize) / 2),
        bottom: Math.round((size - iconSize) / 2),
        left: Math.round((size - iconSize) / 2),
        right: Math.round((size - iconSize) / 2),
        background: { r: 79, g: 70, b: 229, alpha: 1 }
      })
      .png()
      .toFile(`public/${name}`);
    console.log(`✓ Generated ${name}`);
  }
}

generateIcons().catch(console.error);
```

실행:
```bash
npm install
npm run generate-icons
```

## 디자인 가이드

### 색상 팔레트
- Primary: `#4f46e5` (Indigo 600)
- Secondary: `#818cf8` (Indigo 400)
- Background: `#ffffff`
- Text: `#1e293b`

### 로고 사용 원칙
1. **최소 크기**: 로고는 최소 32px 이상으로 사용
2. **여백**: 로고 주변에 충분한 여백 확보
3. **배경**: 흰색 또는 밝은 배경에서 사용 권장
4. **변형 금지**: 색상 변경, 비율 왜곡 금지

## PWA 설치 테스트

1. 개발 서버 실행: `npm run dev`
2. Chrome에서 접속
3. 주소창 오른쪽 설치 아이콘 클릭
4. 앱 설치 확인

## 참고 자료

- [PWA Maskable Icons](https://web.dev/maskable-icon/)
- [Web App Manifest](https://developer.mozilla.org/en-US/docs/Web/Manifest)
- [Favicon Generator](https://realfavicongenerator.net/)
