import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Sidebar from './components/Sidebar'
import ChatArea from './components/ChatArea'
import RightPanel from './components/RightPanel'
import Header from './components/Header'
import LoginPage from './pages/LoginPage'
import AdminDashboard from './pages/AdminDashboard'
import FeedbackPage from './pages/FeedbackPage'


const ProtectedRoute = ({ children, requireAdmin }) => {
    const { token, loading, user } = useAuth();
    if (loading) return <div>Chargement...</div>;
    if (!token) return <Navigate to="/login" />;
    if (requireAdmin && user?.role !== 'admin') {
        return <Navigate to="/" />;
    }
    return children;
};

function ChatLayout({ currentConversationId, setCurrentConversationId }) {
    const [currentSources, setCurrentSources] = React.useState([]);
    const [prefilledMessage, setPrefilledMessage] = React.useState("");

    return (
        <div className="app-container">
            <Header />
            <main className="main-layout">
                <Sidebar
                    currentConversationId={currentConversationId}
                    onSelectConversation={setCurrentConversationId}
                />
                <ChatArea
                    conversationId={currentConversationId}
                    onResponse={(sources) => setCurrentSources(sources)}
                    onConversationCreated={(newId) => setCurrentConversationId(newId)}
                    prefilledMessage={prefilledMessage}
                    onMessageSent={() => setPrefilledMessage("")}
                />
                <RightPanel
                    sources={currentSources}
                    onFaqClick={(msg) => setPrefilledMessage(msg)}
                />
            </main>
        </div>
    );
}

function App() {
    const [currentConversationId, setCurrentConversationId] = React.useState(null);

    return (
        <AuthProvider>
            <Router>
                <Routes>
                    <Route path="/login" element={<LoginPage />} />

                    <Route path="/" element={
                        <ProtectedRoute>
                            <ChatLayout
                                currentConversationId={currentConversationId}
                                setCurrentConversationId={setCurrentConversationId}
                            />
                        </ProtectedRoute>
                    } />

                    <Route path="/admin" element={
                        <ProtectedRoute requireAdmin>
                            <AdminDashboard />
                        </ProtectedRoute>
                    } />

                    <Route path="/feedback" element={
                        <ProtectedRoute requireAdmin>
                            <div className="app-container" style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
                                <Header />
                                <div style={{ flex: 1, overflowY: 'auto' }}>
                                    <FeedbackPage />
                                </div>
                            </div>
                        </ProtectedRoute>
                    } />
                </Routes>
            </Router>
        </AuthProvider>
    )
}

export default App
