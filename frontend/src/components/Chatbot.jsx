import React, { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, Activity, Dumbbell } from 'lucide-react';
import { useParams } from 'react-router-dom';

const BOT_CONFIG = {
    'inbody-analyst': {
        name: '인바디 분석관',
        icon: Activity,
        greeting: "안녕하세요! 인바디 분석 전문가입니다. 당신의 체성분 데이터를 분석하고 건강한 신체를 위한 조언을 드리겠습니다. 무엇이 궁금하신가요?",
        color: '#667eea',
        responses: {
            keywords: {
                '인바디': "최근 분석하신 인바디 결과에 따르면, 골격근량이 표준 이상으로 아주 훌륭합니다! 단백질 섭취를 조금 더 늘리시면 근성장에 더 도움이 될 거예요. 💪",
                '체지방': "체지방률을 건강하게 관리하려면 유산소 운동과 근력 운동을 병행하는 것이 좋습니다. 일주일에 3-4회, 30분 이상의 유산소 운동을 추천드려요.",
                '근육': "근육량 증가를 위해서는 충분한 단백질 섭취(체중 1kg당 1.6-2g)와 함께 점진적 과부하 원칙을 적용한 웨이트 트레이닝이 필요합니다.",
                '영양': "체성분 데이터를 기반으로 보면, 균형잡힌 영양 섭취가 중요합니다. 탄수화물:단백질:지방을 5:3:2 비율로 섭취하는 것을 권장드립니다."
            },
            default: "흥미로운 질문이네요! 체성분 분석 결과와 연관지어 더 자세한 조언을 드릴 수 있습니다. 구체적으로 어떤 부분이 궁금하신가요? ✨"
        }
    },
    'workout-planner': {
        name: '운동 플래너',
        icon: Dumbbell,
        greeting: "안녕하세요! 운동 계획 전문가입니다. 당신의 목표에 맞는 최적의 운동 루틴을 제안하고, 올바른 자세와 동기부여를 제공하겠습니다. 어떤 운동이 필요하신가요?",
        color: '#f5576c',
        responses: {
            keywords: {
                '운동': "오늘은 상체 위주의 웨이트 트레이닝을 추천드려요. 벤치 프레스와 풀업을 각각 3세트씩 진행해보는 건 어떨까요? 🏋️‍♂️",
                '플랜': "당신의 현재 체력 수준에 맞는 4주 운동 플랜을 제안드립니다. 1주차는 적응기, 2-3주차는 강도 증가, 4주차는 목표 달성 단계로 구성됩니다.",
                '하체': "하체 운동의 기본은 스쿼트입니다! 월요일과 목요일에 스쿼트 5세트, 런지 3세트, 레그 프레스 3세트를 진행해보세요. 💪",
                '상체': "상체 발달을 위해 푸시-풀 루틴을 추천합니다. 밀기 동작(벤치프레스, 숄더프레스)과 당기기 동작(풀업, 로우)을 번갈아 진행하세요.",
                '유산소': "효과적인 지방 연소를 위해 HIIT(고강도 인터벌 트레이닝)를 추천드립니다. 30초 전력질주 + 90초 회복을 8-10회 반복해보세요!",
                '스쿼트': "스쿼트의 올바른 자세: 발을 어깨 너비로 벌리고, 무릎이 발끝을 넘지 않도록 주의하며, 엉덩이를 뒤로 빼면서 앉습니다. 시선은 정면을 유지하세요! 🎯"
            },
            default: "좋은 질문입니다! 운동 목표와 현재 체력 수준을 고려해 맞춤형 조언을 드릴게요. 더 구체적으로 알려주시면 정확한 플랜을 제안할 수 있습니다! 💪"
        }
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
        const keywords = config.responses.keywords;

        for (const [keyword, response] of Object.entries(keywords)) {
            if (input.includes(keyword)) {
                return response;
            }
        }

        return config.responses.default;
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
