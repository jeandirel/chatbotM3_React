import React, { useState, useEffect } from 'react';
import { MessageSquare, Plus, Search, Trash2, Calendar } from 'lucide-react';
import { chatService } from '../services/chatService';

export default function Sidebar({ currentConversationId, onSelectConversation }) {
    const [conversations, setConversations] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        loadConversations();
    }, [currentConversationId]);

    const loadConversations = async () => {
        try {
            const data = await chatService.getConversations();
            // Sort by date desc
            const sorted = data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
            setConversations(sorted);
        } catch (error) {
            console.error("Failed to load conversations:", error);
        }
    };

    const handleNewChat = () => {
        onSelectConversation(null);
    };

    const handleDeleteConversation = async (e, id) => {
        e.stopPropagation();
        if (window.confirm("Voulez-vous vraiment supprimer cette conversation ?")) {
            try {
                await chatService.deleteConversation(id);
                loadConversations();
                if (currentConversationId === id) {
                    onSelectConversation(null);
                }
            } catch (error) {
                console.error("Failed to delete conversation:", error);
            }
        }
    };

    const getRelativeTime = (dateString) => {
        const now = new Date();

        let dateObj = new Date(dateString);
        // If dateString is ISO but doesn't end in Z and doesn't have offset, assume it's UTC
        if (dateString && !dateString.endsWith('Z') && !dateString.includes('+')) {
            dateObj = new Date(dateString + 'Z');
        }

        const diffInSeconds = Math.floor((now - dateObj) / 1000);

        if (diffInSeconds < 60) return "À l'instant";
        if (diffInSeconds < 3600) return `Il y a ${Math.floor(diffInSeconds / 60)} min`;
        if (diffInSeconds < 86400) return `Il y a ${Math.floor(diffInSeconds / 3600)} h`;
        return `Il y a ${Math.floor(diffInSeconds / 86400)} jours`;
    };

    const groupConversations = (convs) => {
        const groups = {
            today: [],
            yesterday: [],
            thisWeek: [],
            older: []
        };

        const now = new Date();
        const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const startOfYesterday = new Date(startOfToday);
        startOfYesterday.setDate(startOfYesterday.getDate() - 1);
        const startOfThisWeek = new Date(startOfToday);
        startOfThisWeek.setDate(startOfThisWeek.getDate() - 7);

        convs.forEach(conv => {
            if (!conv.title.toLowerCase().includes(searchTerm.toLowerCase())) return;

            // Handle UTC date for grouping too
            let date = new Date(conv.created_at);
            if (conv.created_at && !conv.created_at.endsWith('Z') && !conv.created_at.includes('+')) {
                date = new Date(conv.created_at + 'Z');
            }

            if (date >= startOfToday) {
                groups.today.push(conv);
            } else if (date >= startOfYesterday) {
                groups.yesterday.push(conv);
            } else if (date >= startOfThisWeek) {
                groups.thisWeek.push(conv);
            } else {
                groups.older.push(conv);
            }
        });

        return groups;
    };

    const groupedConversations = groupConversations(conversations);

    const renderGroup = (title, items, timeFormatFn) => {
        if (items.length === 0) return null;
        return (
            <div className="history-group">
                <div className="group-header">
                    <Calendar size={14} className="group-icon" />
                    <h3>{title}</h3>
                </div>
                {items.map(conv => (
                    <div
                        key={conv.id}
                        className={`history-item ${currentConversationId === conv.id ? 'active' : ''}`}
                        onClick={() => onSelectConversation(conv.id)}
                    >
                        <div className="history-icon-wrapper">
                            <MessageSquare size={18} />
                        </div>
                        <div className="history-content">
                            <h4>{conv.title}</h4>
                            <span className="time">
                                {timeFormatFn ? timeFormatFn(conv.created_at) : new Date(conv.created_at).toLocaleDateString()}
                            </span>
                        </div>
                        <button
                            className="delete-btn"
                            onClick={(e) => handleDeleteConversation(e, conv.id)}
                            title="Supprimer"
                        >
                            <Trash2 size={14} />
                        </button>
                    </div>
                ))}
            </div>
        );
    };

    return (
        <div className="sidebar">
            <div className="sidebar-header">
                <div className="header-title">
                    <MessageSquare size={20} className="header-icon" />
                    <h2>Historique</h2>
                </div>
                <div className="search-input">
                    <Search size={16} className="search-icon" />
                    <input
                        type="text"
                        placeholder="Rechercher..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
            </div>
            <div className="history-list">
                {conversations.length === 0 ? (
                    <div className="no-history">Aucune conversation</div>
                ) : (
                    <>
                        {renderGroup("Aujourd'hui", groupedConversations.today, getRelativeTime)}
                        {renderGroup("Hier", groupedConversations.yesterday, () => "Hier")}
                        {renderGroup("Cette semaine", groupedConversations.thisWeek, getRelativeTime)}
                        {renderGroup("Plus ancien", groupedConversations.older, null)}
                    </>
                )}
            </div>
            <div className="sidebar-footer">
                <button className="new-chat-btn" onClick={handleNewChat}>
                    <Plus size={18} />
                    Nouvelle conversation
                </button>
            </div>
            <style>{`
                .history-group {
                    margin-bottom: 1.5rem;
                }
                .group-header {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    margin-bottom: 0.5rem;
                    padding-left: 0.5rem;
                    color: #d97706; /* Orange-600 */
                }
                .group-header h3 {
                    font-size: 0.85rem;
                    font-weight: 600;
                    text-transform: uppercase;
                    margin: 0;
                }
                .history-item {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    cursor: pointer;
                    padding: 0.75rem;
                    border-radius: 8px;
                    margin-bottom: 0.5rem;
                    background: white;
                    border: 1px solid #fed7aa; /* Orange-200 */
                    transition: all 0.2s;
                    gap: 12px;
                }
                .history-icon-wrapper {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    width: 32px;
                    height: 32px;
                    background-color: #f97316; /* Orange-500 */
                    border-radius: 50%;
                    color: white;
                    flex-shrink: 0;
                }
                .history-item.active .history-icon-wrapper {
                    background-color: #ea580c; /* Orange-600 */
                    color: white;
                }
                .history-item:hover {
                    border-color: #f97316; /* Orange-500 */
                    box-shadow: 0 2px 4px rgba(249, 115, 22, 0.1);
                }
                .history-item.active {
                    background: #fff7ed; /* Orange-50 */
                    border-color: #f97316;
                    border-left: 4px solid #f97316;
                }
                .history-content {
                    flex: 1;
                    overflow: hidden;
                }
                .history-content h4 {
                    margin: 0 0 4px 0;
                    font-size: 0.9rem;
                    color: #1f2937;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }
                .history-content .time {
                    font-size: 0.75rem;
                    color: #f97316; /* Orange-500 */
                }
                .delete-btn {
                    background: none;
                    border: none;
                    color: #9CA3AF;
                    cursor: pointer;
                    padding: 4px;
                    opacity: 0;
                    transition: opacity 0.2s;
                }
                .history-item:hover .delete-btn {
                    opacity: 1;
                }
                .delete-btn:hover {
                    color: #EF4444;
                }
                .no-history {
                    padding: 1rem;
                    text-align: center;
                    color: #9CA3AF;
                    font-size: 0.9rem;
                }
            `}</style>
        </div>
    );
}
