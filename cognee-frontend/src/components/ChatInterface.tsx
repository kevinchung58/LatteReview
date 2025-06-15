import React, { useState, FormEvent, ChangeEvent } from 'react';
import { askQuery, QueryResponse } from '../services/apiService';

interface ChatMessage {
  id: string; // For key prop in React
  type: 'user' | 'ai';
  text: string;
  // Optional: include context items if you want to display them
  graphContext?: string[];
  vectorContext?: string[];
}

const ChatInterface: React.FC = () => {
  const [currentQuestion, setCurrentQuestion] = useState<string>('');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  const handleInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    setCurrentQuestion(event.target.value);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!currentQuestion.trim()) {
      setError('Please enter a question.');
      return;
    }

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      text: currentQuestion.trim(),
    };

    setChatHistory(prevHistory => [...prevHistory, userMessage]);
    setIsLoading(true);
    setError('');

    try {
      const response: QueryResponse = await askQuery(currentQuestion.trim());
      const aiMessage: ChatMessage = {
        id: `ai-${Date.now()}`,
        type: 'ai',
        text: response.answer,
        graphContext: response.graphContextItems,
        vectorContext: response.vectorContextItems,
      };
      setChatHistory(prevHistory => [...prevHistory, aiMessage]);
    } catch (err: any) {
      console.error('Query error:', err);
      const aiErrorMessage: ChatMessage = {
         id: `ai-error-${Date.now()}`,
         type: 'ai',
         text: err.message || 'Sorry, I encountered an error trying to answer your question.',
      };
      setChatHistory(prevHistory => [...prevHistory, aiErrorMessage]);
      setError(err.message || 'Failed to get an answer. Check console for details.');
    } finally {
      setIsLoading(false);
      setCurrentQuestion(''); // Clear input field
    }
  };

  return (
    <div>
      <div className="chat-history" style={{ maxHeight: '400px', overflowY: 'auto', border: '1px solid #ccc', padding: '10px', marginBottom: '10px' }}>
        {chatHistory.map((msg) => (
          <div key={msg.id} style={{ marginBottom: '8px', textAlign: msg.type === 'user' ? 'right' : 'left' }}>
            <div
              style={{
                display: 'inline-block',
                padding: '8px 12px',
                borderRadius: '10px',
                backgroundColor: msg.type === 'user' ? '#007bff' : '#e9ecef',
                color: msg.type === 'user' ? 'white' : 'black',
              }}
            >
              <p><strong>{msg.type === 'user' ? 'You' : 'AI'}:</strong> {msg.text}</p>
              {/* Optional: Display context for AI messages for debugging */}
              {/* {msg.type === 'ai' && msg.graphContext && (
                <details>
                  <summary>Graph Context ({msg.graphContext.length})</summary>
                  <pre style={{fontSize: '0.8em', whiteSpace: 'pre-wrap'}}>{JSON.stringify(msg.graphContext, null, 2)}</pre>
                </details>
              )} */}
              {/* {msg.type === 'ai' && msg.vectorContext && (
                <details>
                  <summary>Vector Context ({msg.vectorContext.length})</summary>
                  <pre style={{fontSize: '0.8em', whiteSpace: 'pre-wrap'}}>{JSON.stringify(msg.vectorContext, null, 2)}</pre>
                </details>
              )} */}
            </div>
          </div>
        ))}
        {isLoading && <p style={{textAlign: 'left', color: '#555'}}>AI is thinking...</p>}
      </div>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={currentQuestion}
          onChange={handleInputChange}
          placeholder="Ask a question..."
          disabled={isLoading}
          style={{ width: '80%', padding: '10px' }}
        />
        <button type="submit" disabled={isLoading} style={{ padding: '10px' }}>
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </form>
      {error && <p style={{ color: 'red', marginTop: '10px' }}>{error}</p>}
    </div>
  );
};

export default ChatInterface;
