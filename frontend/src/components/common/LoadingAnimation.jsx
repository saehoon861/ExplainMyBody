import React from 'react';
import '../../styles/LoginLight.css';

const LoadingAnimation = ({ message = "분석 중입니다...", progress = 0 }) => {
    return (
        <div className="ocr-processing-container fade-in" style={{ minHeight: '300px' }}>
            <div className="pushup-loader">
                <div className="character">
                    <div className="head"></div>
                    <div className="body">
                        <div className="arm arm-l"></div>
                        <div className="arm arm-r"></div>
                    </div>
                    <div className="leg leg-l"></div>
                    <div className="leg leg-r"></div>
                </div>
                <div className="ground"></div>
            </div>

            <div className="progress-status-container" style={{ width: '100%', maxWidth: '320px' }}>
                <div className={`progress-percentage ${progress === 100 ? 'complete' : ''}`}>
                    {progress === 100 ? '완료!' : `${Math.round(progress)}%`}
                </div>
                <div className="progress-bar-wrapper">
                    <div
                        className={`progress-bar-fill ${progress === 100 ? 'complete' : ''}`}
                        style={{ width: `${progress}%` }}
                    ></div>
                </div>
                <p className="loading-quote" style={{ marginTop: '12px', fontSize: '1rem' }}>
                    {message}
                </p>
                <span className="processing-hint">
                    AI가 최적의 운동 루틴을 계산하고 있습니다...
                </span>
            </div>
        </div>
    );
};

export default LoadingAnimation;
