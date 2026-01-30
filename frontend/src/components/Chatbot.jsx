import React, { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, Activity, Dumbbell } from 'lucide-react';
import { useParams } from 'react-router-dom';

const BOT_CONFIG = {
    'inbody-analyst': {
        name: '인바디 분석관',
        icon: Activity,
        greeting: "안녕하세요! 인바디 분석 전문가입니다. 당신의 체성분 데이터를 분석하고 건강한 신체를 위한 조언을 드리겠습니다. 무엇이 궁금하신가요?",
        suggestedActions: ["인바디 결과 분석하기", "내 강점이 뭐야?", "지방을 줄이려면?"],
        color: '#667eea'
    },
    'workout-planner': {
        name: '운동 플래너',
        icon: Dumbbell,
        greeting: "안녕하세요! 운동 계획 전문가입니다. 당신의 목표에 맞는 최적의 운동 루틴을 제안하고, 올바른 자세와 동기부여를 제공하겠습니다. 어떤 운동이 필요하신가요?",
        suggestedActions: ["오늘의 운동 추천", "상체 루틴", "하체 루틴"],
        color: '#f5576c'
    }
};

const Chatbot = () => {
    const { botType } = useParams();
    const config = BOT_CONFIG[botType] || BOT_CONFIG['inbody-analyst'];

    const [messages, setMessages] = useState([
        { id: 1, text: config.greeting, sender: 'bot', actions: config.suggestedActions }
    ]);
    const [inputValue, setInputValue] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [threadId, setThreadId] = useState(null);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const performSend = async (text) => {
        if (!text.trim()) return;

        const userMessage = {
            id: Date.now(),
            text: text,
            sender: 'user'
        };

        setMessages(prev => [...prev, userMessage]);
        setInputValue('');
        setIsTyping(true);

        try {
            // 실제 백엔드 API 호출
            const response = await fetch('http://localhost:5000/api/analysis/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: 1, // 실제 유저 ID 연동 필요 (현재는 Mock)
                    message: text,
                    thread_id: threadId,
                    record_id: 1 // 실제 선택된 기록 ID 연동 필요
                }),
            });

            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();

            if (data.success) {
                const botMessage = {
                    id: Date.now() + 1,
                    text: data.response,
                    sender: 'bot'
                };
                setMessages(prev => [...prev, botMessage]);
                setThreadId(data.thread_id);
            }
        } catch (error) {
            console.error('Error calling AI API:', error);
            const errorMessage = {
                id: Date.now() + 1,
                text: "죄송합니다. AI 응답을 가져오는 중에 문제가 발생했습니다. (서버 연결 확인 필요)",
                sender: 'bot'
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsTyping(false);
        }
    };

    const handleSend = (e) => {
        e.preventDefault();
        performSend(inputValue);
    };

    const handleActionClick = (action) => {
        performSend(action);
    };

    const BotIcon = config.icon;

    return (
        <div className="chatbot-container fade-in">
            <header className="chatbot-header" style={{ borderBottomColor: config.color }}>
                <div className="bot-info">
                    <div className="bot-avatar" style={{ background: config.color }}>
                        <BotIcon size={20} strokeWidth={2} />
                    </div>
                    <div>
                        <h3>{config.name}</h3>
                        <span className="status-online">Online</span>
                    </div>
                </div>
            </header>

            <div className="chat-messages">
                {messages.map((msg) => (
                    <div key={msg.id} className="message-group">
                        <div className={`message-bubble-wrapper ${msg.sender}`}>
                            <div className="avatar">
                                {msg.sender === 'bot' ? <Bot size={20} /> : <User size={20} />}
                            </div>
                            <div className="message-bubble">
                                <p style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</p>
                            </div>
                        </div>
                        {msg.actions && msg.actions.length > 0 && (
                            <div className="suggested-actions" style={{ marginLeft: '44px', marginTop: '8px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                                {msg.actions.map((action, idx) => (
                                    <button
                                        key={idx}
                                        className="action-pill"
                                        onClick={() => handleActionClick(action)}
                                        style={{
                                            padding: '8px 16px',
                                            borderRadius: '20px',
                                            border: `1px solid ${config.color}`,
                                            background: 'white',
                                            color: config.color,
                                            fontSize: '0.85rem',
                                            fontWeight: '600',
                                            cursor: 'pointer'
                                        }}
                                    >
                                        {action}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
                {isTyping && (
                    <div className="message-bubble-wrapper bot">
                        <div className="avatar">
                            <Bot size={20} />
                        </div>
                        <div className="message-bubble typing">
                            <span className="dot"></span>
                            <span className="dot"></span>
                            <span className="dot"></span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <form className="chat-input-area" onSubmit={handleSend}>
                <input
                    type="text"
                    placeholder="메시지를 입력하세요..."
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                />
                <button type="submit" className="send-btn" disabled={!inputValue.trim()} style={{ background: config.color }}>
                    <Send size={20} />
                </button>
            </form>
        </div>
    );
};

export default Chatbot;
