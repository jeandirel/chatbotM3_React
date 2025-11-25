import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { User, Lock, ArrowRight } from 'lucide-react';

export default function LoginPage() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        try {
            await login(username, password);
            navigate('/');
        } catch (err) {
            setError('Identifiants incorrects');
        }
    };

    return (
        <div className="login-container">
            <div className="login-card glass-effect">
                <div className="login-header">
                    <h1>ChatbotM3</h1>
                    <p>Connectez-vous pour accéder à l'assistant</p>
                </div>

                <form onSubmit={handleSubmit} className="login-form">
                    <div className="input-group">
                        <User className="input-icon" size={20} />
                        <input
                            type="text"
                            placeholder="Nom d'utilisateur"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            required
                        />
                    </div>

                    <div className="input-group">
                        <Lock className="input-icon" size={20} />
                        <input
                            type="password"
                            placeholder="Mot de passe"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                    </div>

                    {error && <div className="error-message">{error}</div>}

                    <button type="submit" className="login-btn">
                        Se connecter <ArrowRight size={20} />
                    </button>
                </form>
            </div>

            <style>{`
                .login-container {
                    height: 100vh;
                    width: 100vw;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background-color: var(--bg-color);
                }
                
                .login-card {
                    background: var(--card-bg);
                    padding: 3rem;
                    border-radius: 20px;
                    box-shadow: var(--shadow);
                    border: 1px solid var(--border-color);
                    width: 100%;
                    max-width: 400px;
                    text-align: center;
                }

                .login-header h1 {
                    color: #9A3412; /* Dark Orange */
                    margin-bottom: 0.5rem;
                    font-size: 2rem;
                }

                .login-header p {
                    color: var(--text-secondary);
                    margin-bottom: 2rem;
                }

                .login-form {
                    display: flex;
                    flex-direction: column;
                    gap: 1.5rem;
                }

                .input-group {
                    position: relative;
                    display: flex;
                    align-items: center;
                }

                .input-icon {
                    position: absolute;
                    left: 1rem;
                    color: var(--primary-color);
                }

                .input-group input {
                    width: 100%;
                    padding: 1rem 1rem 1rem 3rem;
                    border: 2px solid var(--border-color);
                    border-radius: 10px;
                    font-size: 1rem;
                    transition: all 0.3s ease;
                    outline: none;
                    background-color: #FFF7ED; /* Light cream input bg */
                    color: var(--text-primary);
                }

                .input-group input:focus {
                    border-color: var(--primary-color);
                    box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.1);
                }

                .login-btn {
                    background-color: var(--primary-color);
                    color: white;
                    padding: 1rem;
                    border: none;
                    border-radius: 10px;
                    font-size: 1.1rem;
                    font-weight: 600;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 0.5rem;
                    transition: background-color 0.2s ease;
                }

                .login-btn:hover {
                    background-color: var(--primary-hover);
                }

                .error-message {
                    color: #DC2626;
                    font-size: 0.9rem;
                    background: #FEE2E2;
                    padding: 0.5rem;
                    border-radius: 5px;
                }
            `}</style>
        </div>
    );
}
