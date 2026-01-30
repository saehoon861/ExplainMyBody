import React, { useState, useEffect } from 'react';
import './LoadingAnimation.css';

const LoadingAnimation = ({ type = 'ocr' }) => {
    const [messageIndex, setMessageIndex] = useState(0);

    const ocrMessages = [
        { icon: '📸', text: '인바디 기록지를 스캔하는 중...' },
        { icon: '🔍', text: '텍스트를 하나하나 읽어보는 중...' },
        { icon: '📊', text: '데이터를 추출하고 있어요...' },
        { icon: '✨', text: '거의 다 됐어요!' }
    ];

    const analysisMessages = [
        { icon: '🤖', text: '당신의 인바디 기록을 분석 중이에요...' },
        { icon: '📈', text: '체성분 데이터를 꼼꼼히 살펴보는 중...' },
        { icon: '💪', text: '근육량과 체지방을 분석하고 있어요...' },
        { icon: '🧠', text: 'AI가 종합적인 분석을 작성 중...' },
        { icon: '✨', text: '곧 완료됩니다!' }
    ];

    const messages = type === 'ocr' ? ocrMessages : analysisMessages;

    useEffect(() => {
        const interval = setInterval(() => {
            setMessageIndex((prev) => (prev + 1) % messages.length);
        }, 2500);

        return () => clearInterval(interval);
    }, [messages.length]);

    return (
        <div className="loading-animation-overlay">
            <div className="loading-animation-container">
                <div className="loading-icon-wrapper">
                    <div className="loading-icon">{messages[messageIndex].icon}</div>
                    <div className="loading-pulse"></div>
                </div>

                <div className="loading-message">
                    {messages[messageIndex].text}
                </div>

                <div className="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>

                <div className="loading-progress-bar">
                    <div className="loading-progress-fill"></div>
                </div>
            </div>
        </div>
    );
};

export default LoadingAnimation;
