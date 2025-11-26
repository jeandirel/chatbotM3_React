import React, { useState } from 'react';
import { X } from 'lucide-react';

export default function FeedbackModal({ isOpen, onClose, onSubmit, type }) {
    const [comment, setComment] = useState('');

    if (!isOpen) return null;

    const handleSubmit = () => {
        onSubmit(comment);
        setComment('');
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <h3>Donner un avis {type === 'positif' ? 'positif' : 'négatif'}</h3>
                    <button onClick={onClose} className="close-btn">
                        <X size={20} />
                    </button>
                </div>
                <div className="modal-body">
                    <p>Voulez-vous ajouter un commentaire ? (Optionnel)</p>
                    <textarea
                        value={comment}
                        onChange={(e) => setComment(e.target.value)}
                        placeholder="Votre commentaire..."
                        rows={4}
                        autoFocus
                    />
                </div>
                <div className="modal-footer">
                    <button onClick={onClose} className="btn-cancel">Annuler</button>
                    <button onClick={handleSubmit} className="btn-submit">Envoyer</button>
                </div>
            </div>
            <style>{`
                .modal-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background-color: rgba(0, 0, 0, 0.5);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    z-index: 1000;
                    backdrop-filter: blur(2px);
                }
                .modal-content {
                    background: white;
                    width: 90%;
                    max-width: 500px;
                    border-radius: 12px;
                    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
                    animation: modalSlideIn 0.3s ease-out;
                    overflow: hidden;
                }
                .modal-header {
                    padding: 1rem 1.5rem;
                    border-bottom: 1px solid #E5E7EB;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .modal-header h3 {
                    margin: 0;
                    color: #1F2937;
                    font-size: 1.1rem;
                    font-weight: 600;
                }
                .close-btn {
                    background: none;
                    border: none;
                    cursor: pointer;
                    color: #6B7280;
                    padding: 4px;
                    border-radius: 4px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .close-btn:hover {
                    background-color: #F3F4F6;
                }
                .modal-body {
                    padding: 1.5rem;
                }
                .modal-body p {
                    margin-top: 0;
                    color: #4B5563;
                    font-size: 0.9rem;
                    margin-bottom: 0.5rem;
                }
                .modal-body textarea {
                    width: 100%;
                    padding: 0.75rem;
                    border: 1px solid #D1D5DB;
                    border-radius: 8px;
                    font-family: inherit;
                    resize: vertical;
                    outline: none;
                    font-size: 0.95rem;
                    color: #1F2937;
                }
                .modal-body textarea:focus {
                    border-color: #F97316;
                    box-shadow: 0 0 0 2px #FED7AA;
                }
                .modal-footer {
                    padding: 1rem 1.5rem;
                    background-color: #F9FAFB;
                    display: flex;
                    justify-content: flex-end;
                    gap: 0.75rem;
                    border-top: 1px solid #E5E7EB;
                }
                .btn-cancel {
                    padding: 0.5rem 1rem;
                    background: white;
                    border: 1px solid #D1D5DB;
                    border-radius: 6px;
                    cursor: pointer;
                    color: #374151;
                    font-weight: 500;
                    transition: background-color 0.2s;
                }
                .btn-cancel:hover {
                    background-color: #F3F4F6;
                }
                .btn-submit {
                    padding: 0.5rem 1rem;
                    background: #F97316;
                    border: none;
                    border-radius: 6px;
                    cursor: pointer;
                    color: white;
                    font-weight: 500;
                    transition: background-color 0.2s;
                }
                .btn-submit:hover {
                    background: #EA580C;
                }
                @keyframes modalSlideIn {
                    from { opacity: 0; transform: translateY(20px); }
                    to { opacity: 1; transform: translateY(0); }
                }
            `}</style>
        </div>
    );
}
