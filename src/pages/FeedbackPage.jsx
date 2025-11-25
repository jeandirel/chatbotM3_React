import React, { useState, useEffect } from 'react';
import { chatService } from '../services/chatService';
import {
    ThumbsUp, ThumbsDown, MessageSquare, Search, Filter, Calendar,
    User, Clock, FileText, ChevronDown, ChevronUp, BarChart2, List, Database
} from 'lucide-react';

export default function FeedbackPage() {
    const [interactions, setInteractions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('stats'); // stats, users, raw

    // Filters
    const [periodFilter, setPeriodFilter] = useState('all'); // all, 24h, week, month
    const [userFilter, setUserFilter] = useState('all');
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        loadInteractions();
    }, []);

    const loadInteractions = async () => {
        try {
            const data = await chatService.getInteractions();
            // Sort by timestamp desc
            data.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
            setInteractions(data);
        } catch (error) {
            console.error("Error loading interactions:", error);
        } finally {
            setLoading(false);
        }
    };

    // --- Filtering Logic ---
    const getFilteredInteractions = () => {
        let filtered = interactions;
        const now = new Date();

        // Period Filter
        if (periodFilter === '24h') {
            const cutoff = new Date(now - 24 * 60 * 60 * 1000);
            filtered = filtered.filter(i => new Date(i.timestamp) >= cutoff);
        } else if (periodFilter === 'week') {
            const cutoff = new Date(now - 7 * 24 * 60 * 60 * 1000);
            filtered = filtered.filter(i => new Date(i.timestamp) >= cutoff);
        } else if (periodFilter === 'month') {
            const cutoff = new Date(now - 30 * 24 * 60 * 60 * 1000);
            filtered = filtered.filter(i => new Date(i.timestamp) >= cutoff);
        }

        // User Filter
        if (userFilter !== 'all') {
            filtered = filtered.filter(i => {
                const sessionId = i.metadata?.user_session_id;
                return sessionId === userFilter;
            });
        }

        // Search Filter
        if (searchTerm) {
            const term = searchTerm.toLowerCase();
            filtered = filtered.filter(i =>
                i.query.toLowerCase().includes(term) ||
                i.response.toLowerCase().includes(term)
            );
        }

        return filtered;
    };

    const filteredData = getFilteredInteractions();

    // --- Stats Calculation ---
    const calculateStats = () => {
        const total = filteredData.length;
        const withFeedback = filteredData.filter(i => i.feedback);
        const positive = withFeedback.filter(i => i.feedback === 'positif').length;
        const negative = withFeedback.filter(i => i.feedback === 'négatif').length;

        return {
            total,
            feedbackCount: withFeedback.length,
            feedbackRate: total > 0 ? Math.round((withFeedback.length / total) * 100) : 0,
            positive,
            positiveRate: withFeedback.length > 0 ? Math.round((positive / withFeedback.length) * 100) : 0,
            negative,
            negativeRate: withFeedback.length > 0 ? Math.round((negative / withFeedback.length) * 100) : 0
        };
    };

    const stats = calculateStats();

    // --- User Stats Calculation ---
    const calculateUserStats = () => {
        const userMap = {};

        interactions.forEach(i => {
            const sessionId = i.metadata?.user_session_id || 'Unknown';
            if (!userMap[sessionId]) {
                userMap[sessionId] = {
                    id: sessionId,
                    interactions: 0,
                    feedbacks: 0,
                    positive: 0,
                    negative: 0,
                    lastActive: i.timestamp
                };
            }
            const user = userMap[sessionId];
            user.interactions++;
            if (i.feedback) {
                user.feedbacks++;
                if (i.feedback === 'positif') user.positive++;
                if (i.feedback === 'négatif') user.negative++;
            }
            if (new Date(i.timestamp) > new Date(user.lastActive)) {
                user.lastActive = i.timestamp;
            }
        });

        return Object.values(userMap).sort((a, b) => b.interactions - a.interactions);
    };

    const userStats = calculateUserStats();
    const uniqueUsers = userStats.map(u => u.id);

    // --- Components ---

    const StatCard = ({ title, value, subtext, color }) => (
        <div className="stat-card" style={{ borderLeft: `4px solid ${color}` }}>
            <h3>{title}</h3>
            <div className="stat-value" style={{ color }}>{value}</div>
            {subtext && <div className="stat-subtext">{subtext}</div>}
        </div>
    );

    const ProgressBar = ({ label, value, color }) => (
        <div className="progress-container">
            <div className="progress-label">
                <span>{label}</span>
                <span>{value}%</span>
            </div>
            <div className="progress-bar-bg">
                <div
                    className="progress-bar-fill"
                    style={{ width: `${value}%`, backgroundColor: color }}
                />
            </div>
        </div>
    );

    return (
        <div className="feedback-page">
            <div className="page-header">
                <h1><BarChart2 size={28} /> Dashboard Feedback</h1>
                <div className="filters-bar">
                    <div className="filter-group">
                        <Calendar size={16} />
                        <select value={periodFilter} onChange={e => setPeriodFilter(e.target.value)}>
                            <option value="all">Toutes les périodes</option>
                            <option value="24h">Dernières 24h</option>
                            <option value="week">Dernière semaine</option>
                            <option value="month">Dernier mois</option>
                        </select>
                    </div>
                    <div className="filter-group">
                        <User size={16} />
                        <select value={userFilter} onChange={e => setUserFilter(e.target.value)}>
                            <option value="all">Tous les utilisateurs</option>
                            {uniqueUsers.map(u => (
                                <option key={u} value={u}>
                                    {u.length > 12 ? u.substring(0, 12) + '...' : u}
                                </option>
                            ))}
                        </select>
                    </div>
                    <button className="refresh-btn" onClick={loadInteractions}>
                        🔄 Rafraîchir
                    </button>
                </div>
            </div>

            <div className="tabs-header">
                <button
                    className={`tab-btn ${activeTab === 'stats' ? 'active' : ''}`}
                    onClick={() => setActiveTab('stats')}
                >
                    <BarChart2 size={18} /> Statistiques
                </button>
                <button
                    className={`tab-btn ${activeTab === 'users' ? 'active' : ''}`}
                    onClick={() => setActiveTab('users')}
                >
                    <User size={18} /> Utilisateurs
                </button>
                <button
                    className={`tab-btn ${activeTab === 'raw' ? 'active' : ''}`}
                    onClick={() => setActiveTab('raw')}
                >
                    <Database size={18} /> Données Brutes
                </button>
            </div>

            <div className="tab-content">
                {activeTab === 'stats' && (
                    <div className="stats-view">
                        <div className="stats-grid">
                            <StatCard
                                title="Total Interactions"
                                value={stats.total}
                                color="#F97316"
                            />
                            <StatCard
                                title="Taux de Feedback"
                                value={`${stats.feedbackRate}%`}
                                subtext={`${stats.feedbackCount}/${stats.total}`}
                                color="#3B82F6"
                            />
                            <StatCard
                                title="Positifs"
                                value={stats.positive}
                                subtext={`${stats.positiveRate}%`}
                                color="#10B981"
                            />
                            <StatCard
                                title="Négatifs"
                                value={stats.negative}
                                subtext={`${stats.negativeRate}%`}
                                color="#EF4444"
                            />
                        </div>

                        <div className="charts-section">
                            <div className="chart-card">
                                <h3>Répartition des Feedbacks</h3>
                                <div className="chart-content">
                                    <ProgressBar
                                        label="👍 Positif"
                                        value={stats.positiveRate}
                                        color="#10B981"
                                    />
                                    <ProgressBar
                                        label="👎 Négatif"
                                        value={stats.negativeRate}
                                        color="#EF4444"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'users' && (
                    <div className="users-view">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>Session ID</th>
                                    <th>Interactions</th>
                                    <th>Feedbacks</th>
                                    <th>Positifs</th>
                                    <th>Négatifs</th>
                                    <th>Dernière Activité</th>
                                </tr>
                            </thead>
                            <tbody>
                                {userStats.map(user => (
                                    <tr key={user.id}>
                                        <td title={user.id}>{user.id.substring(0, 12)}...</td>
                                        <td>{user.interactions}</td>
                                        <td>{user.feedbacks}</td>
                                        <td className="text-green">{user.positive}</td>
                                        <td className="text-red">{user.negative}</td>
                                        <td>{new Date(user.lastActive).toLocaleString()}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {activeTab === 'raw' && (
                    <div className="raw-view">
                        <div className="search-bar-raw">
                            <Search size={18} />
                            <input
                                type="text"
                                placeholder="Rechercher dans les questions/réponses..."
                                value={searchTerm}
                                onChange={e => setSearchTerm(e.target.value)}
                            />
                        </div>
                        <div className="interactions-list">
                            {filteredData.map(interaction => (
                                <InteractionItem key={interaction.id} data={interaction} />
                            ))}
                        </div>
                    </div>
                )}
            </div>

            <style>{`
                .feedback-page {
                    padding: 2rem;
                    max-width: 1400px;
                    margin: 0 auto;
                    color: #1F2937;
                }
                
                .page-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 2rem;
                }

                .page-header h1 {
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                    color: #9A3412;
                    margin: 0;
                }

                .filters-bar {
                    display: flex;
                    gap: 1rem;
                }

                .filter-group {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    background: white;
                    padding: 0.5rem 1rem;
                    border-radius: 8px;
                    border: 1px solid #E5E7EB;
                }

                .filter-group select {
                    border: none;
                    outline: none;
                    background: transparent;
                    font-size: 0.9rem;
                    color: #374151;
                }

                .refresh-btn {
                    padding: 0.5rem 1rem;
                    background: #FFF7ED;
                    border: 1px solid #FED7AA;
                    color: #9A3412;
                    border-radius: 8px;
                    cursor: pointer;
                    font-weight: 500;
                }

                .tabs-header {
                    display: flex;
                    gap: 1rem;
                    margin-bottom: 1.5rem;
                    border-bottom: 1px solid #E5E7EB;
                    padding-bottom: 1px;
                }

                .tab-btn {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    padding: 0.75rem 1.5rem;
                    background: none;
                    border: none;
                    border-bottom: 2px solid transparent;
                    color: #6B7280;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .tab-btn:hover {
                    color: #9A3412;
                }

                .tab-btn.active {
                    color: #9A3412;
                    border-bottom-color: #9A3412;
                }

                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
                    gap: 1.5rem;
                    margin-bottom: 2rem;
                }

                .stat-card {
                    background: white;
                    padding: 1.5rem;
                    border-radius: 12px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }

                .stat-card h3 {
                    margin: 0 0 0.5rem 0;
                    font-size: 0.9rem;
                    color: #6B7280;
                    font-weight: 500;
                }

                .stat-value {
                    font-size: 2rem;
                    font-weight: 700;
                }

                .stat-subtext {
                    margin-top: 0.25rem;
                    font-size: 0.85rem;
                    color: #9CA3AF;
                }

                .chart-card {
                    background: white;
                    padding: 1.5rem;
                    border-radius: 12px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    max-width: 600px;
                }

                .progress-container {
                    margin-bottom: 1rem;
                }

                .progress-label {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 0.25rem;
                    font-size: 0.9rem;
                    font-weight: 500;
                }

                .progress-bar-bg {
                    height: 8px;
                    background: #F3F4F6;
                    border-radius: 4px;
                    overflow: hidden;
                }

                .progress-bar-fill {
                    height: 100%;
                    border-radius: 4px;
                    transition: width 0.5s ease;
                }

                .data-table {
                    width: 100%;
                    border-collapse: collapse;
                    background: white;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }

                .data-table th, .data-table td {
                    padding: 1rem;
                    text-align: left;
                    border-bottom: 1px solid #E5E7EB;
                }

                .data-table th {
                    background: #F9FAFB;
                    font-weight: 600;
                    color: #374151;
                }

                .text-green { color: #10B981; font-weight: 600; }
                .text-red { color: #EF4444; font-weight: 600; }

                .search-bar-raw {
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                    background: white;
                    padding: 0.75rem 1rem;
                    border-radius: 8px;
                    border: 1px solid #E5E7EB;
                    margin-bottom: 1.5rem;
                }

                .search-bar-raw input {
                    border: none;
                    outline: none;
                    width: 100%;
                    font-size: 1rem;
                }

                .interaction-item {
                    background: white;
                    border-radius: 8px;
                    border: 1px solid #E5E7EB;
                    margin-bottom: 1rem;
                    overflow: hidden;
                }

                .interaction-summary {
                    padding: 1rem;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    cursor: pointer;
                    background: #F9FAFB;
                }

                .interaction-summary:hover {
                    background: #F3F4F6;
                }

                .interaction-details {
                    padding: 1.5rem;
                    border-top: 1px solid #E5E7EB;
                }

                .detail-row {
                    margin-bottom: 1rem;
                }

                .detail-label {
                    font-weight: 600;
                    color: #374151;
                    margin-bottom: 0.25rem;
                    display: block;
                }

                .detail-content {
                    background: #F3F4F6;
                    padding: 0.75rem;
                    border-radius: 6px;
                    font-size: 0.95rem;
                    line-height: 1.5;
                }

                .feedback-badge {
                    display: inline-flex;
                    align-items: center;
                    gap: 0.25rem;
                    padding: 0.25rem 0.5rem;
                    border-radius: 9999px;
                    font-size: 0.85rem;
                    font-weight: 500;
                }

                .feedback-badge.positif { background: #D1FAE5; color: #065F46; }
                .feedback-badge.négatif { background: #FEE2E2; color: #991B1B; }

                .sources-list {
                    margin-top: 1rem;
                    padding-top: 1rem;
                    border-top: 1px dashed #E5E7EB;
                }
            `}</style>
        </div>
    );
}

const InteractionItem = ({ data }) => {
    const [expanded, setExpanded] = useState(false);

    return (
        <div className="interaction-item">
            <div className="interaction-summary" onClick={() => setExpanded(!expanded)}>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    <span style={{ color: '#6B7280', fontSize: '0.9rem' }}>
                        {new Date(data.timestamp).toLocaleString()}
                    </span>
                    <span style={{ fontWeight: 500 }}>
                        {data.query.length > 60 ? data.query.substring(0, 60) + '...' : data.query}
                    </span>
                </div>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    {data.feedback && (
                        <span className={`feedback-badge ${data.feedback}`}>
                            {data.feedback === 'positif' ? <ThumbsUp size={14} /> : <ThumbsDown size={14} />}
                            {data.feedback}
                        </span>
                    )}
                    {expanded ? <ChevronUp size={20} color="#9CA3AF" /> : <ChevronDown size={20} color="#9CA3AF" />}
                </div>
            </div>

            {expanded && (
                <div className="interaction-details">
                    <div className="detail-row">
                        <span className="detail-label">Question</span>
                        <div className="detail-content">{data.query}</div>
                    </div>
                    <div className="detail-row">
                        <span className="detail-label">Réponse</span>
                        <div className="detail-content">{data.response}</div>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                        <div className="detail-row">
                            <span className="detail-label">Session ID</span>
                            <div className="detail-content" style={{ fontSize: '0.85rem' }}>
                                {data.metadata?.user_session_id || 'N/A'}
                            </div>
                        </div>
                        <div className="detail-row">
                            <span className="detail-label">Métadonnées</span>
                            <div className="detail-content" style={{ fontSize: '0.85rem' }}>
                                Mode: {data.metadata?.mode || 'N/A'}<br />
                                Confiance: {data.metadata?.confidence?.toFixed(2) || 'N/A'}
                            </div>
                        </div>
                    </div>

                    {data.sources && data.sources.length > 0 && (
                        <div className="sources-list">
                            <span className="detail-label">Sources ({data.sources.length})</span>
                            {data.sources.map((src, idx) => (
                                <div key={idx} style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: '#4B5563' }}>
                                    <strong>{src.metadata?.source || `Source ${idx + 1}`}</strong>: {src.text?.substring(0, 150)}...
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};
