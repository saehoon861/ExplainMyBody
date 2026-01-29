import React, { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, Sparkles } from 'lucide-react';

const Chatbot = () => {
    const [messages, setMessages] = useState([
        { id: 1, text: "안녕하세요! 당신의 건강 파트너 ExplainMyBody AI입니다. 무엇을 도와드릴까요?", sender: 'bot' }
    ]);
    const [inputValue, setInputValue] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = (e) => {
        e.preventDefault();
        if (!inputValue.trim()) return;

        const userMessage = {
            id: Date.now(),
            text: inputValue,
            sender: 'user'
        };

        setMessages(prev => [...prev, userMessage]);
        setInputValue('');
        setIsTyping(true);

        // 시뮬레이션된 AI 응답
        setTimeout(() => {
            const botMessage = {
                id: Date.now() + 1,
                text: getMockResponse(inputValue),
                sender: 'bot'
            };
            setMessages(prev => [...prev, botMessage]);
            setIsTyping(false);
        }, 1500);
    };

    const getMockResponse = (input) => {
        if (input.includes('인바디')) return "최근 분석하신 인바디 결과에 따르면, 골격근량이 표준 이상으로 아주 훌륭합니다! 단백질 섭취를 조금 더 늘리시면 근성장에 더 도움이 될 거예요. 💪";
        if (input.includes('운동')) return "오늘은 상체 위주의 웨이트 트레이닝을 추천드려요. 벤치 프레스와 풀업을 각각 3세트씩 진행해보는 건 어떨까요? 🏋️‍♂️";
        return "흥미로운 질문이네요! 당신의 신체 상태와 목표에 맞춰 더 자세한 조언을 해드릴 수 있어요. 궁금한 점이 있다면 더 말씀해주세요. ✨";
    };

    return (
        <div className="chatbot-container fade-in">
            <header className="chatbot-header">
                <div className="bot-info">
                    <div className="bot-avatar">
                        <Sparkles size={18} />
                    </div>
                    <div>
                        <h3>AI 건강 코치</h3>
                        <span className="status-online">Online</span>
                    </div>
                </div>
            </header>

            <div className="chat-messages">
                {messages.map((msg) => (
                    <div key={msg.id} className={`message-bubble-wrapper ${msg.sender}`}>
                        <div className="avatar">
                            {msg.sender === 'bot' ? <Bot size={20} /> : <User size={20} />}
                        </div>
                        <div className="message-bubble">
                            <p>{msg.text}</p>
                        </div>
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
                <button type="submit" className="send-btn" disabled={!inputValue.trim()}>
                    <Send size={20} />
                </button>
            </form>
        </div>
    );
};

export default Chatbot;
