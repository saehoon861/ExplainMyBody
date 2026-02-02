/**
 * PWA 아이콘 자동 생성 스크립트
 *
 * 사용법:
 * 1. npm install sharp 설치
 * 2. node scripts/generate-icons.js 실행
 *
 * 생성되는 파일:
 * - icon-192.png
 * - icon-512.png
 * - icon-maskable-192.png
 * - icon-maskable-512.png
 * - favicon.png (16x16)
 */

const fs = require('fs');
const path = require('path');

// Check if sharp is installed
let sharp;
try {
    sharp = require('sharp');
} catch (error) {
    console.error('❌ sharp 패키지가 설치되지 않았습니다.');
    console.error('다음 명령어로 설치해주세요: npm install sharp');
    process.exit(1);
}

const publicDir = path.join(__dirname, '..', 'public');
const logoPath = path.join(publicDir, 'logo.svg');

// 생성할 아이콘 설정
const icons = [
    { size: 16, name: 'favicon.png', maskable: false },
    { size: 192, name: 'icon-192.png', maskable: false },
    { size: 512, name: 'icon-512.png', maskable: false },
    { size: 192, name: 'icon-maskable-192.png', maskable: true },
    { size: 512, name: 'icon-maskable-512.png', maskable: true },
];

async function generateIcons() {
    console.log('🎨 PWA 아이콘 생성 시작...\n');

    // SVG 파일 확인
    if (!fs.existsSync(logoPath)) {
        console.error(`❌ 로고 파일을 찾을 수 없습니다: ${logoPath}`);
        process.exit(1);
    }

    const svgBuffer = fs.readFileSync(logoPath);

    for (const { size, name, maskable } of icons) {
        try {
            const outputPath = path.join(publicDir, name);

            if (maskable) {
                // Maskable 아이콘: 20% safe zone 추가
                const iconSize = Math.round(size * 0.8);
                const padding = Math.round((size - iconSize) / 2);

                await sharp(svgBuffer)
                    .resize(iconSize, iconSize)
                    .extend({
                        top: padding,
                        bottom: padding,
                        left: padding,
                        right: padding,
                        background: { r: 79, g: 70, b: 229, alpha: 1 } // #4f46e5
                    })
                    .png()
                    .toFile(outputPath);
            } else {
                // 일반 아이콘
                await sharp(svgBuffer)
                    .resize(size, size)
                    .png()
                    .toFile(outputPath);
            }

            console.log(`✅ ${name} (${size}x${size}${maskable ? ', maskable' : ''})`);
        } catch (error) {
            console.error(`❌ ${name} 생성 실패:`, error.message);
        }
    }

    console.log('\n🎉 모든 아이콘이 성공적으로 생성되었습니다!');
    console.log(`📁 저장 위치: ${publicDir}\n`);
}

// 실행
generateIcons().catch(error => {
    console.error('❌ 오류 발생:', error);
    process.exit(1);
});
