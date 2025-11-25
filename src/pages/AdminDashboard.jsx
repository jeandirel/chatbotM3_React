import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { UserPlus, Trash2, Shield, ArrowLeft } from 'lucide-react';

export default function AdminDashboard() {
    const [users, setUsers] = useState([]);
    const [newUser, setNewUser] = useState({ username: '', password: '', role: 'user' });
    const { token, user } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        if (user?.role !== 'admin') {
            navigate('/');
            return;
        }
        fetchUsers();
    }, [user, navigate]);

    const fetchUsers = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/users', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setUsers(data);
            }
        } catch (err) {
            console.error(err);
        }
    };

    const handleCreateUser = async (e) => {
        e.preventDefault();
        try {
            const res = await fetch('http://localhost:8000/api/users', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(newUser)
            });
            if (res.ok) {
                setNewUser({ username: '', password: '', role: 'user' });
                fetchUsers();
            } else {
                alert('Erreur lors de la création');
            }
        } catch (err) {
            console.error(err);
        }
    };

    return (
        <div className="admin-container">
            <header className="admin-header">
                <button onClick={() => navigate('/')} className="back-btn">
                    <ArrowLeft size={20} /> Retour au Chat
                </button>
                <h1>Administration Utilisateurs</h1>
            </header>

            <div className="admin-content">
                <div className="create-user-card">
                    <h2><UserPlus size={20} /> Ajouter un utilisateur</h2>
                    <form onSubmit={handleCreateUser} className="create-form">
                        <input
                            type="text"
                            placeholder="Nom d'utilisateur"
                            value={newUser.username}
                            onChange={e => setNewUser({ ...newUser, username: e.target.value })}
                            required
                        />
                        <input
                            type="password"
                            placeholder="Mot de passe"
                            value={newUser.password}
                            onChange={e => setNewUser({ ...newUser, password: e.target.value })}
                            required
                        />
                        <select
                            value={newUser.role}
                            onChange={e => setNewUser({ ...newUser, role: e.target.value })}
                        >
                            <option value="user">Utilisateur</option>
                            <option value="admin">Administrateur</option>
                        </select>
                        <button type="submit">Créer</button>
                    </form>
                </div>

                <div className="users-list-card">
                    <h2>Liste des utilisateurs ({users.length})</h2>
                    <div className="users-table">
                        <div className="table-header">
                            <span>ID</span>
                            <span>Utilisateur</span>
                            <span>Rôle</span>
                            <span>Date création</span>
                        </div>
                        {users.map(u => (
                            <div key={u.id} className="table-row">
                                <span>{u.id}</span>
                                <span className="username-cell">{u.username}</span>
                                <span>
                                    <span className={`role-badge ${u.role}`}>
                                        {u.role === 'admin' && <Shield size={12} />} {u.role}
                                    </span>
                                </span>
                                <span>{new Date(u.created_at).toLocaleDateString()}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            <style>{`
                .admin-container {
                    padding: 2rem;
                    background-color: var(--bg-color);
                    min-height: 100vh;
                    font-family: 'Inter', sans-serif;
                }
                .admin-header {
                    display: flex;
                    align-items: center;
                    gap: 2rem;
                    margin-bottom: 2rem;
                }
                .admin-header h1 {
                    color: #9A3412;
                    margin: 0;
                }
                .back-btn {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    border: none;
                    background: none;
                    cursor: pointer;
                    font-size: 1rem;
                    color: var(--text-secondary);
                    transition: color 0.2s;
                }
                .back-btn:hover {
                    color: var(--primary-color);
                }
                .admin-content {
                    display: grid;
                    grid-template-columns: 1fr 2fr;
                    gap: 2rem;
                }
                .create-user-card, .users-list-card {
                    background: var(--card-bg);
                    padding: 1.5rem;
                    border-radius: var(--radius);
                    box-shadow: var(--shadow);
                    border: 1px solid var(--border-color);
                }
                .create-user-card h2, .users-list-card h2 {
                    color: #9A3412;
                    margin-top: 0;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                }
                .create-form {
                    display: flex;
                    flex-direction: column;
                    gap: 1rem;
                    margin-top: 1rem;
                }
                .create-form input, .create-form select {
                    padding: 0.8rem;
                    border: 1px solid var(--border-color);
                    border-radius: 8px;
                    background-color: #FFF7ED;
                    outline: none;
                }
                .create-form input:focus, .create-form select:focus {
                    border-color: var(--primary-color);
                }
                .create-form button {
                    background-color: var(--primary-color);
                    color: white;
                    padding: 0.8rem;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    font-weight: 600;
                    transition: background-color 0.2s;
                }
                .create-form button:hover {
                    background-color: var(--primary-hover);
                }
                .users-table {
                    margin-top: 1rem;
                }
                .table-header, .table-row {
                    display: grid;
                    grid-template-columns: 0.5fr 2fr 1fr 1.5fr;
                    padding: 1rem;
                    border-bottom: 1px solid var(--border-color);
                }
                .table-header {
                    font-weight: bold;
                    color: var(--text-secondary);
                }
                .table-row {
                    align-items: center;
                }
                .role-badge {
                    display: inline-flex;
                    align-items: center;
                    gap: 0.3rem;
                    padding: 0.2rem 0.6rem;
                    border-radius: 20px;
                    font-size: 0.85rem;
                    text-transform: capitalize;
                }
                .role-badge.admin {
                    background: #FFEDD5;
                    color: #C2410C;
                    border: 1px solid #FED7AA;
                }
                .role-badge.user {
                    background: #F3F4F6;
                    color: #6B7280;
                }
            `}</style>
        </div>
    );
}
