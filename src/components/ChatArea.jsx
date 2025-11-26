import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, Plus, ThumbsUp, ThumbsDown, Copy, Share2, RefreshCw, User, Sparkles, Check, FileText } from 'lucide-react';
import { chatService } from '../services/chatService';
import FeedbackModal from './FeedbackModal';
import ReactMarkdown from 'react-markdown';

export default function ChatArea({ conversationId, onResponse, onConversationCreated, prefilledMessage, onMessageSent }) {
    const [messages, setMessages] = useState([
        {
            id: 'init',
            role: 'assistant',
            content: "Bonjour ! Je suis l'assistant virtuel pour la documentation M3. Comment puis-je vous aider ?",
            sources: []
        }
    ]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [sessionId, setSessionId] = useState(null);
    const [copiedId, setCopiedId] = useState(null);
    const [feedbackInput, setFeedbackInput] = useState(null);
    const [isListening, setIsListening] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        if (prefilledMessage) {
            setInputValue(prefilledMessage);
        }
    }, [prefilledMessage]);

    useEffect(() => {
        if (conversationId) {
            loadMessages(conversationId);
        } else {
            setMessages([
                {
                    id: 'init',
                    role: 'assistant',
                    content: "Bonjour ! Je suis l'assistant virtuel pour la documentation M3. Comment puis-je vous aider ?",
                    sources: []
                }
            ]);
            setSessionId(null);
        }
    }, [conversationId]);

    const loadMessages = async (id) => {
        setIsLoading(true);
        try {
            const msgs = await chatService.getConversationMessages(id);
            setMessages(msgs);

            const lastMsg = msgs[msgs.length - 1];
            if (lastMsg && lastMsg.role === 'assistant' && lastMsg.sources && onResponse) {
                onResponse(lastMsg.sources);
            } else if (onResponse) {
                onResponse([]);
            }

        } catch (error) {
            console.error("Error loading messages:", error);
        } finally {
            setIsLoading(false);
        }
    };

    const processApiResponse = (data) => {
        if (data.session_id && !sessionId) {
            setSessionId(data.session_id);
        }

        const botMessage = {
            id: Date.now().toString() + '_bot',
            role: 'assistant',
            content: data.response,
            sources: data.sources || [],
            metadata: data.metadata,
            interaction_id: data.interaction_id
        };

        setMessages(prev => [...prev, botMessage]);

        if (onResponse && data.sources) {
            onResponse(data.sources);
        }

        if (data.conversation_id && data.conversation_id !== conversationId) {
            if (onConversationCreated) {
                onConversationCreated(data.conversation_id);
            }
        }
    };

    const handleSendMessage = async () => {
        if (!inputValue.trim() || isLoading) return;

        const userMessageText = inputValue;
        setInputValue('');
        if (onMessageSent) onMessageSent();

        const userMessage = {
            id: Date.now().toString(),
            role: 'user',
            content: userMessageText
        };

        setMessages(prev => [...prev, userMessage]);
        setIsLoading(true);

        try {
            const history = messages
                .filter(m => m.id !== 'init')
                .map(m => ({ role: m.role, content: m.content }));

            const data = await chatService.sendMessage(userMessageText, sessionId, history, conversationId);
            processApiResponse(data);

        } catch (error) {
            console.error("Error:", error);
            const errorMessage = {
                id: Date.now().toString() + '_error',
                role: 'assistant',
                content: "Désolé, une erreur est survenue lors de la communication avec le serveur. Assurez-vous que le backend Python est lancé.",
                isError: true
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleRegenerate = async () => {
        if (isLoading) return;

        const lastUserIndex = [...messages].map(m => m.role).lastIndexOf('user');
        if (lastUserIndex === -1) return;

        const lastUserMessage = messages[lastUserIndex];
        const newMessages = messages.slice(0, lastUserIndex + 1);
        setMessages(newMessages);
        setIsLoading(true);

        try {
            const history = newMessages
                .slice(0, lastUserIndex)
                .filter(m => m.id !== 'init')
                .map(m => ({ role: m.role, content: m.content }));

            const data = await chatService.sendMessage(lastUserMessage.content, sessionId, history, conversationId);
            processApiResponse(data);

        } catch (error) {
            console.error("Error:", error);
            const errorMessage = {
                id: Date.now().toString() + '_error',
                role: 'assistant',
                content: "Désolé, une erreur est survenue lors de la régénération.",
                isError: true
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleShare = async (text) => {
        if (navigator.share) {
            try {
                await navigator.share({
                    title: 'Réponse Chatbot M3',
                    text: text,
                });
            } catch (err) {
                console.error('Error sharing:', err);
            }
        } else {
            handleCopy(text, null);
        }
    };

    const handleCopy = (content, id) => {
        navigator.clipboard.writeText(content);
        if (id) {
            setCopiedId(id);
            setTimeout(() => setCopiedId(null), 2000);
        }
    };

    const initiateFeedback = (messageId, interactionId, type) => {
        setFeedbackInput({ messageId, interactionId, type, comment: '' });
    };

    const submitFeedback = async (comment) => {
        if (!feedbackInput) return;
        const { messageId, interactionId, type } = feedbackInput;

        try {
            await chatService.sendFeedback(interactionId, type, comment);

            setMessages(prev => prev.map(msg => {
                if (msg.id === messageId) {
                    return { ...msg, feedback: type, feedbackComment: comment };
                }
                return msg;
            }));
            setFeedbackInput(null);
        } catch (error) {
            console.error("Error sending feedback:", error);
        }
    };

    const cancelFeedback = () => {
        setFeedbackInput(null);
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const toggleListening = () => {
        if (isListening) {
            // Stop logic is usually handled by the browser automatically for non-continuous, 
            // but we can force state update here if needed.
            setIsListening(false);
        } else {
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                const recognition = new SpeechRecognition();
                recognition.lang = 'fr-FR';
                recognition.continuous = false;
                recognition.interimResults = false;

                recognition.onstart = () => setIsListening(true);
                recognition.onend = () => setIsListening(false);
                recognition.onerror = (event) => {
                    console.error("Speech recognition error", event.error);
                    setIsListening(false);
                };
                recognition.onresult = (event) => {
                    const transcript = event.results[0][0].transcript;
                    setInputValue(prev => prev + (prev ? ' ' : '') + transcript);
                };

                recognition.start();
            } else {
                alert("Votre navigateur ne supporte pas la reconnaissance vocale.");
            }
        }
    };

    return (
        <div className="chat-area">
            <div className="chat-messages">
                {messages.map((msg, index) => (
                    <div key={msg.id} className={`message ${msg.role === 'user' ? 'user' : 'bot'}`}>
                        <div className={`avatar ${msg.role === 'user' ? 'user-avatar' : 'bot-avatar'}`}>
                            {msg.role === 'user' ? <User size={20} /> : <Sparkles size={20} />}
                        </div>
                        <div className="message-content">
                            <div className="text-content">
                                <ReactMarkdown
                                    components={{
                                        strong: ({ node, ...props }) => <span style={{ color: '#F97316', fontWeight: 'bold' }} {...props} />
                                    }}
                                >
                                    {msg.content}
                                </ReactMarkdown>
                            </div>

                            {msg.role === 'user' && (
                                <div className="user-message-actions" style={{ marginTop: '5px', display: 'flex', justifyContent: 'flex-end', opacity: 0.7 }}>
                                    <button
                                        title="Copier"
                                        onClick={() => handleCopy(msg.content, msg.id)}
                                        style={{ background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', color: 'inherit' }}
                                    >
                                        {copiedId === msg.id ? <Check size={12} /> : <Copy size={12} />}
                                        {copiedId === msg.id && <span style={{ fontSize: '0.7rem', marginLeft: '4px' }}>Copié</span>}
                                    </button>
                                </div>
                            )}

                            {msg.sources && msg.sources.length > 0 && (
                                <div className="sources-notification" style={{
                                    marginTop: '12px',
                                    padding: '8px 12px',
                                    backgroundColor: '#FFF7ED',
                                    border: '1px solid #FED7AA',
                                    borderRadius: '8px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '10px',
                                    fontSize: '0.85rem',
                                    color: '#9A3412'
                                }}>
                                    <FileText size={16} color="#F97316" style={{ flexShrink: 0 }} />
                                    <span>
                                        Les documents sources sont disponibles dans la section <strong>Résultats PDF</strong>.
                                    </span>
                                </div>
                            )}

                            {!msg.isError && msg.role === 'assistant' && (
                                <div className="message-actions-container">
                                    <div className="message-actions">
                                        <button
                                            title="Utile"
                                            onClick={() => initiateFeedback(msg.id, msg.interaction_id, 'positif')}
                                            className={msg.feedback === 'positif' ? 'active-feedback' : ''}
                                        >
                                            <ThumbsUp size={14} />
                                        </button>
                                        <button
                                            title="Pas utile"
                                            onClick={() => initiateFeedback(msg.id, msg.interaction_id, 'negatif')}
                                            className={msg.feedback === 'negatif' ? 'active-feedback' : ''}
                                        >
                                            <ThumbsDown size={14} />
                                        </button>
                                        <button title="Copier" onClick={() => handleCopy(msg.content, msg.id)}>
                                            {copiedId === msg.id ? <Check size={14} color="green" /> : <Copy size={14} />}
                                        </button>
                                        {copiedId === msg.id && <span className="copy-notification" style={{ fontSize: '0.75rem', color: 'green', marginLeft: '5px' }}>Message copié</span>}
                                        <button title="Partager" onClick={() => handleShare(msg.content)}><Share2 size={14} /></button>
                                        {index === messages.length - 1 && (
                                            <button title="Régénérer" onClick={handleRegenerate}><RefreshCw size={14} /></button>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                ))}

                {isLoading && (
                    <div className="message bot">
                        <div className="avatar bot-avatar"><Sparkles size={20} /></div>
                        <div className="message-content">
                            <div className="typing-indicator">
                                <span></span><span></span><span></span>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="chat-input-area">
                <button className="icon-btn"><Plus size={20} /></button>
                <div className="input-wrapper" style={{ position: 'relative' }}>
                    {isListening && (
                        <div className="recording-badge">
                            <div className="recording-dot"></div>
                            Enregistrement...
                        </div>
                    )}
                    <input
                        type="text"
                        placeholder={isListening ? "Parlez maintenant..." : "Envoyer un message..."}
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={handleKeyPress}
                        disabled={isLoading}
                    />
                    <div className="input-actions">
                        <Mic
                            size={20}
                            className={`mic-icon ${isListening ? 'mic-recording' : ''}`}
                            onClick={toggleListening}
                            color={isListening ? "#EF4444" : "currentColor"}
                            style={{ cursor: 'pointer', transition: 'all 0.2s' }}
                        />
                        <button
                            className="send-btn"
                            onClick={handleSendMessage}
                            disabled={isLoading || !inputValue.trim()}
                        >
                            <Send size={18} />
                        </button>
                    </div>
                </div>
                <button className="icon-btn info-btn">i</button>
            </div>

            <FeedbackModal
                isOpen={!!feedbackInput}
                onClose={cancelFeedback}
                onSubmit={submitFeedback}
                type={feedbackInput?.type}
            />
        </div>
    );
}

function MessageSquare({ size }) {
    return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
    )
}
