import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, Plus, ThumbsUp, ThumbsDown, Copy, Share2, RefreshCw, User, Sparkles } from 'lucide-react';
import { chatService } from '../services/chatService';

export default function ChatArea({ conversationId, onResponse, onConversationCreated }) {
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
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

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
            // Transform messages if needed or ensure backend returns compatible format
            // Backend returns: [{role, content, id, ...}, ...]
            setMessages(msgs);

            // If last message has sources, update parent
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

        // Notify parent if new conversation was created
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

        // Add user message
        const userMessage = {
            id: Date.now().toString(),
            role: 'user',
            content: userMessageText
        };

        setMessages(prev => [...prev, userMessage]);
        setIsLoading(true);

        try {
            // Prepare history (excluding the just added message)
            // Filter out init message if it's not relevant, or keep it?
            // Usually we only send user/assistant messages from history
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

        // Find last user message
        const lastUserIndex = [...messages].map(m => m.role).lastIndexOf('user');
        if (lastUserIndex === -1) return;

        const lastUserMessage = messages[lastUserIndex];

        // Remove messages after the last user message (the bot response we want to replace)
        const newMessages = messages.slice(0, lastUserIndex + 1);
        setMessages(newMessages);
        setIsLoading(true);

        try {
            // History is everything before the last user message
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
            navigator.clipboard.writeText(text);
            // Could add a toast here
        }
    };

    const handleFeedback = async (messageId, interactionId, feedbackType) => {
        if (!interactionId) return;

        try {
            await chatService.sendFeedback(interactionId, feedbackType);

            // Update UI to show feedback state
            setMessages(prev => prev.map(msg => {
                if (msg.id === messageId) {
                    return { ...msg, feedback: feedbackType };
                }
                return msg;
            }));
        } catch (error) {
            console.error("Error sending feedback:", error);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
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
                            <div className="text-content" style={{ whiteSpace: 'pre-wrap' }}>
                                {msg.content}
                            </div>

                            {msg.sources && msg.sources.length > 0 && (
                                <div className="sources-section">
                                    <div className="sources-title">Sources:</div>
                                    <ul className="sources-list">
                                        {msg.sources.map((source, idx) => (
                                            <li key={idx} className="source-item">
                                                <span className="source-name">
                                                    {source.metadata?.source || 'Document inconnu'}
                                                </span>
                                                {source.metadata?.page && (
                                                    <span className="source-page"> (Page {source.metadata.page})</span>
                                                )}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {!msg.isError && msg.role === 'assistant' && (
                                <div className="message-actions">
                                    <button
                                        title="Utile"
                                        onClick={() => handleFeedback(msg.id, msg.interaction_id, 'positif')}
                                        className={msg.feedback === 'positif' ? 'active-feedback' : ''}
                                    >
                                        <ThumbsUp size={14} />
                                    </button>
                                    <button
                                        title="Pas utile"
                                        onClick={() => handleFeedback(msg.id, msg.interaction_id, 'negatif')}
                                        className={msg.feedback === 'negatif' ? 'active-feedback' : ''}
                                    >
                                        <ThumbsDown size={14} />
                                    </button>
                                    <button title="Copier" onClick={() => navigator.clipboard.writeText(msg.content)}><Copy size={14} /></button>
                                    <button title="Partager" onClick={() => handleShare(msg.content)}><Share2 size={14} /></button>
                                    {index === messages.length - 1 && (
                                        <button title="Régénérer" onClick={handleRegenerate}><RefreshCw size={14} /></button>
                                    )}
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
                <div className="input-wrapper">
                    <input
                        type="text"
                        placeholder="Envoyer un message..."
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={handleKeyPress}
                        disabled={isLoading}
                    />
                    <div className="input-actions">
                        <Mic size={20} className="mic-icon" />
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
