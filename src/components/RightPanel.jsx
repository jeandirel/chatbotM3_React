import React, { useState, useEffect } from 'react';
import { ChevronRight, FileText, Settings, Filter, Eye } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import PdfModal from './PdfModal';
import FaqModal from './FaqModal';
import { faqService } from '../services/faqService';

export default function RightPanel({ sources = [], onFaqClick }) {
    const { user } = useAuth();
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isFaqModalOpen, setIsFaqModalOpen] = useState(false);
    const [selectedPdf, setSelectedPdf] = useState(null);
    const [faqs, setFaqs] = useState([]);

    useEffect(() => {
        const loadFaqs = async () => {
            try {
                const data = await faqService.getFaqs();
                setFaqs(data);
            } catch (error) {
                console.error("Error loading FAQs:", error);
            }
        };
        loadFaqs();
    }, []);

    // Extract unique PDF files from sources
    const uniquePdfs = React.useMemo(() => {
        const pdfs = new Map();
        sources.forEach(source => {
            const relativePath = source.metadata?.source; // e.g. "Oxypharm/file.pdf"
            const displayName = source.metadata?.filename || relativePath?.split('/').pop() || 'Document inconnu';

            if (relativePath && !pdfs.has(relativePath)) {
                pdfs.set(relativePath, {
                    name: displayName,
                    url: `http://localhost:8000/static/${relativePath}`
                });
            }
        });
        return Array.from(pdfs.values());
    }, [sources]);

    const handleOpenPdf = (pdf) => {
        setSelectedPdf(pdf);
        setIsModalOpen(true);
    };

    const handleFaqClick = (question) => {
        if (onFaqClick) onFaqClick(question);
    };

    return (
        <div className="right-panel">
            <div className="panel-card">
                <div className="section-header">
                    <h3>Questions fréquemment posées</h3>
                    <ChevronRight size={16} />
                </div>
                <button
                    onClick={() => setIsFaqModalOpen(true)}
                    className="see-all"
                    style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, textAlign: 'left', fontFamily: 'inherit' }}
                >
                    voir toutes
                </button>
                <div className="faq-list">
                    {faqs.slice(0, 3).map((faq, index) => (
                        <button key={index} className="faq-item" onClick={() => handleFaqClick(faq.question)}>
                            {faq.question}
                        </button>
                    ))}
                    {faqs.length === 0 && <div style={{ fontSize: '0.8rem', color: '#6B7280', fontStyle: 'italic' }}>Chargement...</div>}
                </div>
            </div>

            <div className="panel-card">
                <div className="section-header">
                    <h3>Résultats PDF</h3>
                    <button className="filter-btn"><Filter size={14} /></button>
                </div>
                <div className="pdf-grid">
                    {uniquePdfs.length > 0 ? (
                        uniquePdfs.map((pdf, index) => (
                            <div key={index} className="pdf-item">
                                <div className="pdf-icon"><FileText size={20} /></div>
                                <span title={pdf.name}>{pdf.name.length > 20 ? pdf.name.substring(0, 20) + '...' : pdf.name}</span>
                                <button
                                    className="view-pdf-btn"
                                    onClick={() => handleOpenPdf(pdf)}
                                    title="Voir le PDF"
                                >
                                    <Eye size={16} />
                                </button>
                            </div>
                        ))
                    ) : (
                        <div className="no-results">Aucun PDF lié à cette réponse</div>
                    )}
                </div>
            </div>

            <div className="panel-section">
                <h3>Mode</h3>
                <div className="mode-toggle">
                    <span>Mode Standard</span>
                    <div className="toggle-switch">
                        <div className="toggle-knob"></div>
                    </div>
                </div>
            </div>

            <div className="panel-section">
                <h3>Administration</h3>
                {user?.role === 'admin' ? (
                    <Link to="/feedback" className="admin-btn">
                        <Settings size={16} /> Paramètres Admin
                    </Link>
                ) : (
                    <div className="admin-btn disabled">
                        <Settings size={16} /> Paramètres Admin
                    </div>
                )}
            </div>

            {selectedPdf && (
                <PdfModal
                    isOpen={isModalOpen}
                    onClose={() => setIsModalOpen(false)}
                    pdfUrl={selectedPdf.url}
                    title={selectedPdf.name}
                />
            )}

            <FaqModal
                isOpen={isFaqModalOpen}
                onClose={() => setIsFaqModalOpen(false)}
                onQuestionClick={handleFaqClick}
                faqs={faqs}
            />

            <style>{`
                .view-pdf-btn {
                    background: none;
                    border: none;
                    color: #6B7280;
                    cursor: pointer;
                    padding: 4px;
                    border-radius: 4px;
                    margin-left: auto;
                    display: flex;
                    align-items: center;
                }
                .view-pdf-btn:hover {
                    color: #ea580c;
                    background-color: #fff7ed;
                }
                .pdf-item {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    padding: 0.5rem;
                    background: #F9FAFB;
                    border-radius: 6px;
                    margin-bottom: 0.5rem;
                }
                .no-results {
                    font-size: 0.85rem;
                    color: #9CA3AF;
                    font-style: italic;
                    text-align: center;
                    padding: 1rem 0;
                }
                .admin-btn.disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }
            `}</style>
        </div>
    );
}
