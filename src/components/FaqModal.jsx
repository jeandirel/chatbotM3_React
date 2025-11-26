import React from 'react';
import { X, HelpCircle, MessageSquare } from 'lucide-react';

export default function FaqModal({ isOpen, onClose, onQuestionClick, faqs = [] }) {
    if (!isOpen) return null;

    const handleQuestionClick = (question) => {
        onQuestionClick(question);
        onClose();
    };

    return (
        <div className="modal-overlay">
            <div className="modal-content" style={{ maxWidth: '600px', maxHeight: '80vh', display: 'flex', flexDirection: 'column' }}>
                <div className="modal-header">
                    <h3><HelpCircle size={20} style={{ marginRight: '8px' }} /> Questions Fréquentes</h3>
                    <button onClick={onClose} className="close-btn"><X size={20} /></button>
                </div>

                <div className="modal-body" style={{ overflowY: 'auto' }}>
                    <div className="faq-grid" style={{ display: 'grid', gap: '10px' }}>
                        {faqs.length > 0 ? (
                            faqs.map((item, index) => (
                                <button
                                    key={index}
                                    className="faq-item-full"
                                    onClick={() => handleQuestionClick(item.question)}
                                    style={{
                                        display: 'flex', alignItems: 'center', gap: '10px',
                                        padding: '12px', border: '1px solid #E5E7EB', borderRadius: '8px',
                                        background: 'white', cursor: 'pointer', textAlign: 'left',
                                        transition: 'all 0.2s'
                                    }}
                                    onMouseEnter={(e) => { e.currentTarget.style.borderColor = '#F97316'; e.currentTarget.style.backgroundColor = '#FFF7ED'; }}
                                    onMouseLeave={(e) => { e.currentTarget.style.borderColor = '#E5E7EB'; e.currentTarget.style.backgroundColor = 'white'; }}
                                >
                                    <MessageSquare size={16} color="#F97316" />
                                    <div>
                                        <div style={{ fontWeight: 500, color: '#374151' }}>{item.question}</div>
                                        <div style={{ fontSize: '0.75rem', color: '#9CA3AF' }}>{item.category}</div>
                                    </div>
                                </button>
                            ))
                        ) : (
                            <div style={{ textAlign: 'center', padding: '2rem', color: '#6B7280' }}>
                                Aucune question fréquente disponible.
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
