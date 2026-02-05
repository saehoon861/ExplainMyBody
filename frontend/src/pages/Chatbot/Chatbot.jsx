import React, { useState, useRef, useEffect } from 'react';
import { Send, User } from 'lucide-react';
import { useParams } from 'react-router-dom';
import { sendChatbotMessage } from '../../services/chatService';

const BOT_CONFIG = {
    'inbody-analyst': {
        name: '인바디 분석 전문가',
        icon: '🧑‍⚕️',
        greeting: "안녕하세요! 인바디 분석 전문가입니다. 당신의 체성분 데이터를 분석하고 건강한 신체를 위한 조언을 드리겠습니다. 무엇이 궁금하신가요?",
        color: '#667eea',
        gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    },
    'workout-planner': {
        name: '운동 플래너 전문가',
        icon: '🏋️',
        greeting: "안녕하세요! 운동 플래너 전문가입니다. 당신의 목표에 맞는 최적의 운동 루틴을 제안하고, 올바른 자세와 동기부여를 제공하겠습니다. 어떤 운동이 필요하신가요?",
        color: '#f5576c',
        gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
    }
};

const Chatbot = () => {
    const { botType } = useParams();
    const config = BOT_CONFIG[botType] || BOT_CONFIG['inbody-analyst'];

    const [messages, setMessages] = useState([
        { id: 1, text: config.greeting, sender: 'bot' }
    ]);
    const [inputValue, setInputValue] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [threadId, setThreadId] = useState(null); // LangGraph 대화 스레드 ID
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!inputValue.trim()) return;

        const userMessage = {
            id: Date.now(),
            text: inputValue,
            sender: 'user'
        };

        setMessages(prev => [...prev, userMessage]);
        const currentInput = inputValue;
        setInputValue('');
        setIsTyping(true);

        try {
            // 백엔드 LLM API 호출
            const result = await sendChatbotMessage({
                bot_type: botType,
                message: currentInput,
                thread_id: threadId, // 이전 대화 이력 추적
                user_id: 1 // TODO: 실제 사용자 ID로 변경 (로그인 구현 후)
            });

            // Thread ID 저장 (대화 이력 유지)
            if (result.thread_id) {
                setThreadId(result.thread_id);
            }

            const botMessage = {
                id: Date.now() + 1,
                text: result.response,
                sender: 'bot'
            };
            setMessages(prev => [...prev, botMessage]);
        } catch (error) {
            console.error('챗봇 응답 오류:', error);
            // 오류 시 폴백 응답
            const errorMessage = {
                id: Date.now() + 1,
                text: "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                sender: 'bot'
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsTyping(false);
        }
    };

    return (
        <div className="chatbot-container fade-in">
            <header className="chatbot-header" style={{ borderBottomColor: config.color }}>
                <div className="bot-info">
                    <div className="bot-avatar" style={{
                        width: '48px',
                        height: '48px',
                        borderRadius: '16px',
                        background: config.gradient,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '24px',
                        boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
                        flexShrink: 0
                    }}>
                        {config.icon}
                    </div>
                    <div>
                        <h3>{config.name}</h3>
                        <span className="status-online">Online</span>
                    </div>
                </div>
            </header>

            <div className="chat-messages">
                {messages.map((msg) => (
                    <div key={msg.id} className={`message-bubble-wrapper ${msg.sender}`}>
                        {msg.sender === 'bot' ? (
                            <div className="avatar" style={{
                                width: '36px',
                                height: '36px',
                                borderRadius: '12px',
                                background: config.gradient,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontSize: '18px',
                                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                                flexShrink: 0
                            }}>
                                {config.icon}
                            </div>
                        ) : (
                            <div className="avatar">
                                <User size={20} />
                            </div>
                        )}
                        <div className="message-bubble">
                            <p style={{
                                whiteSpace: 'pre-wrap',
                                wordBreak: 'break-word',
                                margin: 0
                            }}>
                                {msg.text}
                            </p>
                        </div>
                    </div>
                ))}
                {isTyping && (
                    <div className="message-bubble-wrapper bot">
                        <div className="avatar" style={{
                            width: '36px',
                            height: '36px',
                            borderRadius: '12px',
                            background: config.gradient,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '18px',
                            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                            flexShrink: 0
                        }}>
                            {config.icon}
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
                <button type="submit" className="send-btn" disabled={!inputValue.trim()}>
                    <Send size={20} />
                </button>
            </form>
        </div>
    );
};

export default Chatbot;
