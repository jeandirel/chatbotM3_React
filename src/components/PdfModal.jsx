import React from 'react';
import { X, ExternalLink } from 'lucide-react';

export default function PdfModal({ isOpen, onClose, pdfUrl, title }) {
    if (!isOpen) return null;

    return (
        <div className="pdf-modal-overlay" onClick={onClose}>
            <div className="pdf-modal-content" onClick={e => e.stopPropagation()}>
                <div className="pdf-modal-header">
                    <h3>{title}</h3>
                    <div className="pdf-modal-actions">
                        <a href={pdfUrl} target="_blank" rel="noopener noreferrer" title="Ouvrir dans un nouvel onglet">
                            <ExternalLink size={20} />
                        </a>
                        <button onClick={onClose} title="Fermer">
                            <X size={20} />
                        </button>
                    </div>
                </div>
                <div className="pdf-modal-body">
                    <iframe
                        src={pdfUrl}
                        title="PDF Viewer"
                        width="100%"
                        height="100%"
                        style={{ border: 'none' }}
                    />
                </div>
            </div>
            <style>{`
                .pdf-modal-overlay {
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

                .pdf-modal-content {
                    background: white;
                    width: 90%;
                    height: 90%;
                    max-width: 1200px;
                    border-radius: 12px;
                    display: flex;
                    flex-direction: column;
                    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
                    animation: modalSlideIn 0.3s ease-out;
                }

                @keyframes modalSlideIn {
                    from {
                        opacity: 0;
                        transform: translateY(20px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }

                .pdf-modal-header {
                    padding: 1rem 1.5rem;
                    border-bottom: 1px solid #E5E7EB;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }

                .pdf-modal-header h3 {
                    margin: 0;
                    color: #1F2937;
                    font-size: 1.1rem;
                    font-weight: 600;
                }

                .pdf-modal-actions {
                    display: flex;
                    gap: 1rem;
                    align-items: center;
                }

                .pdf-modal-actions button, .pdf-modal-actions a {
                    background: none;
                    border: none;
                    color: #6B7280;
                    cursor: pointer;
                    padding: 0.25rem;
                    border-radius: 4px;
                    transition: all 0.2s;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }

                .pdf-modal-actions button:hover, .pdf-modal-actions a:hover {
                    background-color: #F3F4F6;
                    color: #1F2937;
                }

                .pdf-modal-body {
                    flex: 1;
                    padding: 0;
                    background: #F9FAFB;
                    border-bottom-left-radius: 12px;
                    border-bottom-right-radius: 12px;
                    overflow: hidden;
                }
            `}</style>
        </div>
    );
}
