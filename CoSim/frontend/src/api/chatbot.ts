/**
 * Chatbot API Client
 * Handles communication with the RAG-powered chatbot service
 */

const CHATBOT_API_URL = import.meta.env.VITE_CHATBOT_API_URL || 'http://localhost:8006';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ChatRequest {
  message: string;
  conversation_history?: ChatMessage[];
  max_history?: number;
}

export interface Source {
  section: string;
  content_preview: string;
  relevance_score?: number;
}

export interface ChatResponse {
  response: string;
  sources: Source[];
  timestamp: string;
}

export interface HealthResponse {
  status: string;
  vector_store_stats: {
    total_documents: number;
    collection_name: string;
    persist_directory: string;
  };
}

/**
 * Send a chat query to the bot
 */
export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${CHATBOT_API_URL}/chat/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request)
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * Send feedback on a chatbot response
 */
export async function sendChatFeedback(
  messageId: string,
  helpful: boolean,
  comment?: string
): Promise<{ status: string; message: string }> {
  const response = await fetch(`${CHATBOT_API_URL}/chat/feedback`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message_id: messageId, helpful, comment })
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * Get suggested questions
 */
export async function getChatSuggestions(): Promise<string[]> {
  const response = await fetch(`${CHATBOT_API_URL}/chat/suggestions`);

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const data = await response.json();
  return data.suggestions;
}

/**
 * Check chatbot service health
 */
export async function checkChatbotHealth(): Promise<HealthResponse> {
  const response = await fetch(`${CHATBOT_API_URL}/health`);

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}
