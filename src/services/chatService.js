const API_URL = 'http://localhost:8000';

export const chatService = {
  async sendMessage(message, sessionId, history, conversationId = null) {
    const token = localStorage.getItem('token');
    const headers = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}/api/chat`, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify({
        message,
        session_id: sessionId,
        conversation_id: conversationId,
        history: history
      })
    });

    if (!response.ok) {
      if (response.status === 401) {
        // Token expired or invalid
        localStorage.removeItem('token');
        window.location.href = '/login';
        throw new Error('Unauthorized');
      }
      throw new Error('Network response was not ok');
    }

    return response.json();
  },

  async checkHealth() {
    try {
      const response = await fetch(`${API_URL}/health`);
      return response.ok;
    } catch (error) {
      return false;
    }
  },

  async sendFeedback(interactionId, feedback, comment = null) {
    const token = localStorage.getItem('token');
    const headers = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}/api/feedback/${interactionId}`, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify({
        feedback,
        feedback_value: feedback === 'positif' ? 1 : 0,
        feedback_comment: comment
      })
    });

    if (!response.ok) {
      throw new Error('Failed to submit feedback');
    }
    return response.json();
  },

  async getInteractions() {
    const token = localStorage.getItem('token');
    const headers = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}/api/interactions`, {
      headers: headers
    });

    if (!response.ok) {
      throw new Error('Failed to fetch interactions');
    }
    return response.json();
  },

  async getConversations() {
    const token = localStorage.getItem('token');
    const headers = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}/api/conversations`, {
      headers: headers
    });

    if (!response.ok) {
      throw new Error('Failed to fetch conversations');
    }
    return response.json();
  },

  async createConversation(title) {
    const token = localStorage.getItem('token');
    const headers = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}/api/conversations`, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify({ title })
    });

    if (!response.ok) {
      throw new Error('Failed to create conversation');
    }
    return response.json();
  },

  async getConversationMessages(conversationId) {
    const token = localStorage.getItem('token');
    const headers = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}/api/conversations/${conversationId}/messages`, {
      headers: headers
    });

    if (!response.ok) {
      throw new Error('Failed to fetch messages');
    }
    return response.json();
  },

  async deleteConversation(conversationId) {
    const token = localStorage.getItem('token');
    const headers = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}/api/conversations/${conversationId}`, {
      method: 'DELETE',
      headers: headers
    });

    if (!response.ok) {
      throw new Error('Failed to delete conversation');
    }
    return response.json();
  }
};
