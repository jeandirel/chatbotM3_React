const API_URL = 'http://localhost:8000/api';

export const faqService = {
    getFaqs: async () => {
        const response = await fetch(`${API_URL}/faq`);
        if (!response.ok) throw new Error('Failed to fetch FAQs');
        return response.json();
    },

    createFaq: async (question, category, token) => {
        const response = await fetch(`${API_URL}/faq`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ question, category })
        });
        if (!response.ok) throw new Error('Failed to create FAQ');
        return response.json();
    },

    deleteFaq: async (id, token) => {
        const response = await fetch(`${API_URL}/faq/${id}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) throw new Error('Failed to delete FAQ');
        return response.json();
    }
};
