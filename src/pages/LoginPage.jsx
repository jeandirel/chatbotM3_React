import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { User, Lock, Mail, ArrowRight, Loader } from 'lucide-react';

export default function LoginPage() {
    const [isLogin, setIsLogin] = useState(true);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [email, setEmail] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            if (isLogin) {
                await login(username, password);
                navigate('/');
            } else {
                // Register
                const response = await fetch('http://localhost:8000/api/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, email, password })
                });

                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.detail || "Erreur lors de l'inscription");
                }

                // Auto login after register
                await login(username, password);
                navigate('/');
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="login-container">
            <div className="login-card">
                <div className="login-header">
                    <div className="logo-circle">
                        <User size={32} color="#F97316" />
                    </div>
                    <h2>{isLogin ? 'Connexion' : 'Créer un compte'}</h2>
                    <p>{isLogin ? 'Accédez à votre assistant documentaire' : 'Rejoignez la plateforme M3'}</p>
                </div>

                <form onSubmit={handleSubmit} className="login-form">
                    {error && <div className="error-message">{error}</div>}

                    <div className="form-group">
                        <label>Nom d'utilisateur</label>
                        <div className="input-wrapper">
                            <User size={18} />
                            <input
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                placeholder="Votre identifiant"
                                required
                            />
                        </div>
                    </div>

                    {!isLogin && (
                        <div className="form-group">
                            <label>Email professionnel</label>
                            <div className="input-wrapper">
                                <Mail size={18} />
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="nom@cerp-rouen.fr"
                                    required
                                />
                            </div>
                        </div>
                    )}

                    <div className="form-group">
                        <label>Mot de passe</label>
                        <div className="input-wrapper">
                            <Lock size={18} />
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                required
                            />
                        </div>
                    </div>

                    <button type="submit" className="login-btn" disabled={isLoading}>
                        {isLoading ? <Loader className="spin" size={20} /> : (
                            <>
                                {isLogin ? 'Se connecter' : "S'inscrire"}
                                <ArrowRight size={18} />
                            </>
                        )}
                    </button>
                </form>

                <div className="login-footer">
                    <p>
                        {isLogin ? "Pas encore de compte ? " : "Déjà un compte ? "}
                        <button onClick={() => setIsLogin(!isLogin)} className="toggle-btn">
                            {isLogin ? "Créer un compte" : "Se connecter"}
                        </button>
                    </p>
                </div>
            </div>

            <style>{`
                .login-container {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    min-height: 100vh;
                    background: linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%);
                    padding: 20px;
                }
                .login-card {
                    background: white;
                    padding: 2.5rem;
                    border-radius: 16px;
                    box-shadow: 0 10px 25px -5px rgba(249, 115, 22, 0.1), 0 8px 10px -6px rgba(249, 115, 22, 0.1);
                    width: 100%;
                    max-width: 400px;
                }
                .login-header {
                    text-align: center;
                    margin-bottom: 2rem;
                }
                .logo-circle {
                    width: 64px;
                    height: 64px;
                    background: #FFF7ED;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 1rem;
                }
                .login-header h2 {
                    color: #1F2937;
                    font-size: 1.5rem;
                    margin-bottom: 0.5rem;
                }
                .login-header p {
                    color: #6B7280;
                    font-size: 0.9rem;
                }
                .form-group {
                    margin-bottom: 1.25rem;
                }
                .form-group label {
                    display: block;
                    font-size: 0.875rem;
                    font-weight: 500;
                    color: #374151;
                    margin-bottom: 0.5rem;
                }
                .input-wrapper {
                    position: relative;
                    display: flex;
                    align-items: center;
                }
                .input-wrapper svg {
                    position: absolute;
                    left: 12px;
                    color: #9CA3AF;
                }
                .input-wrapper input {
                    width: 100%;
                    padding: 10px 12px 10px 40px;
                    border: 1px solid #E5E7EB;
                    border-radius: 8px;
                    font-size: 0.95rem;
                    transition: all 0.2s;
                }
                .input-wrapper input:focus {
                    outline: none;
                    border-color: #F97316;
                    box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.1);
                }
                .login-btn {
                    width: 100%;
                    padding: 12px;
                    background: #F97316;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-weight: 600;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                    transition: background 0.2s;
                    margin-top: 1rem;
                }
                .login-btn:hover {
                    background: #EA580C;
                }
                .login-btn:disabled {
                    opacity: 0.7;
                    cursor: not-allowed;
                }
                .error-message {
                    background: #FEF2F2;
                    color: #EF4444;
                    padding: 10px;
                    border-radius: 8px;
                    font-size: 0.875rem;
                    margin-bottom: 1rem;
                    text-align: center;
                }
                .spin {
                    animation: spin 1s linear infinite;
                }
                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
                .login-footer {
                    margin-top: 1.5rem;
                    text-align: center;
                    font-size: 0.9rem;
                    color: #6B7280;
                }
                .toggle-btn {
                    background: none;
                    border: none;
                    color: #F97316;
                    font-weight: 600;
                    cursor: pointer;
                    padding: 0;
                }
                .toggle-btn:hover {
                    text-decoration: underline;
                }
            `}</style>
        </div>
    );
}
