import React, { useState, useEffect } from 'react';
import './LoadingSpinner.css';

const LoadingSpinner = ({ message = "분석 중입니다..." }) => {
    return (
        <div className="loading-overlay">
            <div className="loading-content">
                <div className="fitness-animation">
                    <img src="/loading_pt.png" alt="Exercise Animation" className="exercise-silhouette" />
                    <div className="loading-ring"></div>
                </div>
                <p className="loading-message">{message}</p>
            </div>
        </div>
    );
};

export default LoadingSpinner;
