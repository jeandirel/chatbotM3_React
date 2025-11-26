import React, { useState, useRef, useEffect } from 'react';
import { Search, User, Settings, LogOut, UserCircle, Home } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Link, useLocation } from 'react-router-dom';
import ProfileModal from './ProfileModal';

export default function Header() {
    const { user, logout } = useAuth();
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [isProfileOpen, setIsProfileOpen] = useState(false);
    const menuRef = useRef(null);
    const location = useLocation();
    const isFeedbackPage = location.pathname === '/feedback';

    useEffect(() => {
        function handleClickOutside(event) {
            if (menuRef.current && !menuRef.current.contains(event.target)) {
                setIsMenuOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [menuRef]);

    return (
        <header className="main-header">
            <div className="search-bar">
                <Search size={20} className="search-icon" />
                <input type="text" placeholder="Rechercher dans la documentation..." />
            </div>

            <div className="header-actions" style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                {isFeedbackPage && (
                    <Link to="/" className="icon-btn" title="Retour au chat" style={{ width: '36px', height: '36px', textDecoration: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <Home size={20} />
                    </Link>
                )}

                {user?.role === 'admin' && !isFeedbackPage && (
                    <Link to="/feedback" className="icon-btn" title="Administration Feedback" style={{ width: '36px', height: '36px', textDecoration: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <Settings size={20} />
                    </Link>
                )}

                <div className="user-menu-container" ref={menuRef} style={{ position: 'relative' }}>
                    <div
                        className="user-profile"
                        onClick={() => setIsMenuOpen(!isMenuOpen)}
                        style={{
                            display: 'flex',
                            gap: '10px',
                            alignItems: 'center',
                            cursor: 'pointer',
                            padding: '6px 12px',
                            borderRadius: '20px',
                            backgroundColor: isMenuOpen ? '#FFF7ED' : 'transparent',
                            transition: 'background-color 0.2s'
                        }}
                    >
                        <span style={{ fontWeight: 500 }}>{user?.username}</span>
                        <div style={{
                            width: '32px', height: '32px',
                            background: '#FFEDD5', borderRadius: '50%',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            color: '#F97316'
                        }}>
                            <User size={18} />
                        </div>
                    </div>

                    {isMenuOpen && (
                        <div className="dropdown-menu" style={{
                            position: 'absolute',
                            top: '120%',
                            right: 0,
                            width: '200px',
                            backgroundColor: 'white',
                            borderRadius: '12px',
                            boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
                            border: '1px solid #FED7AA',
                            padding: '8px',
                            zIndex: 100,
                            animation: 'fade-in 0.2s ease-out'
                        }}>
                            <div className="menu-header" style={{ padding: '8px 12px', borderBottom: '1px solid #F3F4F6', marginBottom: '8px' }}>
                                <div style={{ fontSize: '0.9rem', fontWeight: 600 }}>{user?.username}</div>
                                <div style={{ fontSize: '0.75rem', color: '#6B7280', textTransform: 'capitalize' }}>{user?.role}</div>
                            </div>

                            <button
                                onClick={() => { setIsProfileOpen(true); setIsMenuOpen(false); }}
                                className="menu-item"
                                style={{
                                    width: '100%', textAlign: 'left', padding: '10px 12px',
                                    background: 'none', border: 'none', cursor: 'pointer',
                                    display: 'flex', alignItems: 'center', gap: '10px',
                                    color: '#374151', borderRadius: '8px',
                                    transition: 'background 0.2s'
                                }}
                                onMouseEnter={(e) => e.target.style.backgroundColor = '#FFF7ED'}
                                onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
                            >
                                <UserCircle size={18} />
                                Mon Profil
                            </button>

                            <button
                                onClick={logout}
                                className="menu-item"
                                style={{
                                    width: '100%', textAlign: 'left', padding: '10px 12px',
                                    background: 'none', border: 'none', cursor: 'pointer',
                                    display: 'flex', alignItems: 'center', gap: '10px',
                                    color: '#EF4444', borderRadius: '8px',
                                    marginTop: '4px'
                                }}
                                onMouseEnter={(e) => e.target.style.backgroundColor = '#FEF2F2'}
                                onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
                            >
                                <LogOut size={18} />
                                Déconnexion
                            </button>
                        </div>
                    )}
                </div>
            </div>

            <ProfileModal isOpen={isProfileOpen} onClose={() => setIsProfileOpen(false)} />
        </header>
    );
}
