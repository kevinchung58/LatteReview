import React, { useState, FormEvent, ChangeEvent } from 'react';
import { askQuery, QueryResponse } from '../services/apiService';
import styles from './ChatInterface.module.css'; // Import CSS module

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
    <div className={styles.chatContainer}>
      <div className={styles.chatHistory} aria-live="polite">
        {chatHistory.map((msg) => (
          <div
            key={msg.id}
            className={`${styles.messageWrapper} ${msg.type === 'user' ? styles.userMessage : styles.aiMessage}`}
          >
            <div className={styles.messageContent}>
              <p className={styles.messageLabel}>{msg.type === 'user' ? 'You' : 'AI'}:</p>
              <p className={styles.messageText}>{msg.text}</p>
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
        {isLoading && <p className={styles.aiThinking}>AI is thinking...</p>}
      </div>
      <form onSubmit={handleSubmit} className={styles.chatForm}>
        <input
          type="text"
          value={currentQuestion}
          onChange={handleInputChange}
          placeholder="Ask a question..."
          aria-label="Ask a question" // Added aria-label
          disabled={isLoading}
          className={styles.chatInput} // Uses global input style, can be overridden by this class
        />
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </form>
      {/* Using global .text-error utility class from index.css */}
      {error && <p className="text-error" style={{ marginTop: '10px' }} aria-live="assertive">{error}</p>}
    </div>
  );
};

export default ChatInterface;
