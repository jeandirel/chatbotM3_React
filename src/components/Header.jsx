import React from 'react';
import { Search, User, Settings, MessageSquare } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';

export default function Header() {
    const { user } = useAuth();
    return (
        <header className="main-header">
            <div className="search-bar">
                <Search size={20} className="search-icon" />
                <input type="text" placeholder="search for documents (FAQs)" />
            </div>
            <div className="user-profile" style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                <span>{user?.username}</span>
                <User size={20} />
                {user?.role === 'admin' && (
                    <Link to="/feedback" title="Feedback" style={{ color: 'inherit', display: 'flex', alignItems: 'center' }}>
                        <Settings size={20} />
                    </Link>
                )}
            </div>
        </header>
    );
}
