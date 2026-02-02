import React from 'react';

const Logo = ({ size = 'medium', variant = 'full', showSubtitle = true }) => {
    const sizes = {
        small: { width: 60, fontSize: 20, subtitleSize: 8 },
        medium: { width: 100, fontSize: 36, subtitleSize: 11 },
        large: { width: 160, fontSize: 56, subtitleSize: 16 },
        icon: { width: 48, fontSize: 16, subtitleSize: 0 }
    };

    const config = sizes[size] || sizes.medium;

    // Generate unique IDs to prevent conflicts
    const uniqueId = React.useId();
    const gradientId = `gradient-${uniqueId}`;

    if (variant === 'icon') {
        return (
            <svg
                width={config.width}
                height={config.width}
                viewBox="0 0 128 128"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
            >
                <defs>
                    <linearGradient id={gradientId} x1="0" y1="0" x2="128" y2="128">
                        <stop offset="0%" stopColor="#4f46e5"/>
                        <stop offset="100%" stopColor="#818cf8"/>
                    </linearGradient>
                </defs>

                {/* Background */}
                <rect width="128" height="128" rx="24" fill={`url(#${gradientId})`}/>

                {/* Minimal wave */}
                <path d="M 24 38 Q 48 32, 64 38 Q 80 44, 104 38"
                      stroke="white"
                      strokeWidth="4"
                      fill="none"
                      strokeLinecap="round"
                      opacity="0.6"/>

                {/* IBA Text */}
                <text
                    x="64"
                    y="88"
                    fontFamily="Arial, sans-serif"
                    fontSize={config.fontSize}
                    fontWeight="900"
                    fill="white"
                    textAnchor="middle"
                    letterSpacing="-1"
                >
                    IBA
                </text>
            </svg>
        );
    }

    return (
        <svg
            width={config.width}
            height={config.width * (showSubtitle ? 0.5 : 0.4)}
            viewBox="0 0 400 200"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
        >
            <defs>
                <linearGradient id={gradientId} x1="0" y1="0" x2="400" y2="200">
                    <stop offset="0%" stopColor="#4f46e5"/>
                    <stop offset="100%" stopColor="#818cf8"/>
                </linearGradient>
            </defs>

            {/* Icon Part with waves */}
            <g>
                <circle cx="70" cy="100" r="50" fill={`url(#${gradientId})`}/>

                {/* Waves inside circle */}
                <path d="M 35 85 Q 52 80, 70 85 Q 88 90, 105 85"
                      stroke="white"
                      strokeWidth="3"
                      fill="none"
                      strokeLinecap="round"
                      opacity="0.6"/>

                <text
                    x="70"
                    y="115"
                    fontFamily="Arial, sans-serif"
                    fontSize="28"
                    fontWeight="900"
                    fill="white"
                    textAnchor="middle"
                    letterSpacing="-1"
                >
                    IBA
                </text>
            </g>

            {/* Main Text */}
            <text
                x="140"
                y="95"
                fontFamily="Arial, sans-serif"
                fontSize={config.fontSize}
                fontWeight="800"
                fill={`url(#${gradientId})`}
            >
                InBody
            </text>
            <text
                x="140"
                y={95 + config.fontSize * 0.9}
                fontFamily="Arial, sans-serif"
                fontSize={config.fontSize * 0.7}
                fontWeight="600"
                fill="#64748b"
            >
                Analysis
            </text>

            {showSubtitle && config.subtitleSize > 0 && (
                <text
                    x="140"
                    y={95 + config.fontSize * 1.7}
                    fontFamily="Arial, sans-serif"
                    fontSize={config.subtitleSize}
                    fontWeight="500"
                    fill="#94a3b8"
                >
                    AI 기반 건강 관리
                </text>
            )}
        </svg>
    );
};

export default Logo;
