import React, { useState, useEffect } from 'react';
import { Download, X, Smartphone } from 'lucide-react';
import './PWAInstallPrompt.css';

const PWAInstallPrompt = () => {
    const [deferredPrompt, setDeferredPrompt] = useState(null);
    const [showPrompt, setShowPrompt] = useState(false);

    useEffect(() => {
        // PWA 설치 프롬프트 이벤트 캡처
        const handleBeforeInstallPrompt = (e) => {
            // 브라우저 기본 설치 프롬프트 방지
            e.preventDefault();
            // 나중에 사용하기 위해 이벤트 저장
            setDeferredPrompt(e);

            // 이미 설치했거나, 사용자가 "나중에" 선택한 경우 확인
            const installDismissed = localStorage.getItem('pwaInstallDismissed');
            const isStandalone = window.matchMedia('(display-mode: standalone)').matches
                || window.navigator.standalone
                || document.referrer.includes('android-app://');

            // 설치 안내 표시 조건
            if (!installDismissed && !isStandalone) {
                // 2초 후에 프롬프트 표시 (사용자가 앱을 둘러본 후)
                setTimeout(() => {
                    setShowPrompt(true);
                }, 2000);
            }
        };

        // 앱 설치 완료 이벤트
        const handleAppInstalled = () => {
            console.log('PWA가 성공적으로 설치되었습니다!');
            setShowPrompt(false);
            setDeferredPrompt(null);
        };

        window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
        window.addEventListener('appinstalled', handleAppInstalled);

        return () => {
            window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
            window.removeEventListener('appinstalled', handleAppInstalled);
        };
    }, []);

    const handleInstallClick = async () => {
        if (!deferredPrompt) {
            return;
        }

        // 설치 프롬프트 표시
        deferredPrompt.prompt();

        // 사용자의 응답 대기
        const { outcome } = await deferredPrompt.userChoice;
        console.log(`사용자 선택: ${outcome}`);

        // 프롬프트 사용 후 초기화
        setDeferredPrompt(null);
        setShowPrompt(false);

        if (outcome === 'accepted') {
            console.log('사용자가 PWA 설치를 수락했습니다');
        } else {
            console.log('사용자가 PWA 설치를 거부했습니다');
        }
    };

    const handleDismiss = () => {
        setShowPrompt(false);
        // 24시간 동안 프롬프트 표시 안 함
        const dismissTime = new Date().getTime() + (24 * 60 * 60 * 1000);
        localStorage.setItem('pwaInstallDismissed', dismissTime.toString());
    };

    // 프롬프트를 표시하지 않는 경우
    if (!showPrompt || !deferredPrompt) {
        return null;
    }

    return (
        <div className="pwa-install-overlay" onClick={handleDismiss}>
            <div className="pwa-install-prompt" onClick={(e) => e.stopPropagation()}>
                <button
                    className="pwa-close-btn"
                    onClick={handleDismiss}
                    aria-label="닫기"
                >
                    <X size={20} />
                </button>

                <div className="pwa-icon-container">
                    <div className="pwa-icon">
                        <Smartphone size={48} />
                    </div>
                    <div className="pwa-icon-glow"></div>
                </div>

                <div className="pwa-content">
                    <h2>ExplainMyBody 앱 설치</h2>
                    <p>
                        홈 화면에 추가하여<br />
                        언제 어디서나 빠르게 이용하세요!
                    </p>

                    <div className="pwa-features">
                        <div className="feature-item">
                            <span className="feature-icon">⚡</span>
                            <span>빠른 실행</span>
                        </div>
                        <div className="feature-item">
                            <span className="feature-icon">📱</span>
                            <span>앱처럼 사용</span>
                        </div>
                        <div className="feature-item">
                            <span className="feature-icon">🔔</span>
                            <span>알림 받기</span>
                        </div>
                    </div>
                </div>

                <div className="pwa-actions">
                    <button
                        className="pwa-dismiss-btn"
                        onClick={handleDismiss}
                    >
                        나중에
                    </button>
                    <button
                        className="pwa-install-btn"
                        onClick={handleInstallClick}
                    >
                        <Download size={20} />
                        설치하기
                    </button>
                </div>
            </div>
        </div>
    );
};

export default PWAInstallPrompt;
