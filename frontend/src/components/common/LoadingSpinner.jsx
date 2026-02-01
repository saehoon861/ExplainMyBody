import React, { useState, useEffect } from 'react';
import './LoadingSpinner.css';

const LoadingSpinner = () => {
    return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] fade-in">
            <div className="relative w-32 h-32 mb-4 animate-bounce-slow">
                <img
                    src="/assets/loading-mascot.png"
                    alt="Loading..."
                    className="w-full h-full object-contain"
                />
            </div>
            <p className="text-gray-500 font-medium animate-pulse">열심히 준비 중이에요...</p>
            <style>{`
                @keyframes bounce-slow {
                    0%, 100% { transform: translateY(-5%); }
                    50% { transform: translateY(5%); }
                }
                .animate-bounce-slow {
                    animation: bounce-slow 2s infinite ease-in-out;
                }
            `}</style>
        </div>
    );
};

export default LoadingSpinner;
