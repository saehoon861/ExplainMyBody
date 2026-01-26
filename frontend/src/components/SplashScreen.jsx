import React, { useEffect, useState } from 'react';
import './SplashScreen.css';

const SplashScreen = ({ onFinish }) => {
    const [fadeOut, setFadeOut] = useState(false);

    useEffect(() => {
        const timer = setTimeout(() => {
            setFadeOut(true);
            setTimeout(onFinish, 800); // 페이드 아웃 애니메이션 시간 후 종료
        }, 2800); // 2.8초 동안 로고 및 서브타이틀 노출

        return () => clearTimeout(timer);
    }, [onFinish]);

    return (
        <div className={`splash-container ${fadeOut ? 'fade-out' : ''}`}>
            <div className="splash-content">
                <div className="logo-glitch-container">
                    <h1 className="splash-logo">ExplainMyBody</h1>
                    <div className="logo-glow"></div>
                </div>
                <div className="loading-bar-container">
                    <div className="loading-bar"></div>
                </div>
                <p className="splash-subtitle">내 몸을 이해하는 가장 스마트한 방법</p>
            </div>
        </div>
    );
};

export default SplashScreen;
