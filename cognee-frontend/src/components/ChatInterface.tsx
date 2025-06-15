import React, { useState, FormEvent, ChangeEvent, useRef } from 'react'; // Added useRef
import { askQuery } from '../services/apiService'; // QueryResponse no longer directly used by handleSubmit
import styles from './ChatInterface.module.css'; // Import CSS module

interface ChatMessage {
  id: string; // For key prop in React
  type: 'user' | 'ai';
  text: string;
  // Optional: include context items if you want to display them
  // These would need to be sent via SSE if desired with streaming text
  // graphContext?: string[];
  // vectorContext?: string[];
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
    setCurrentQuestion(''); // Clear input field immediately after sending

    const aiMessageId = `ai-${Date.now()}`;
    const initialAiMessage: ChatMessage = {
      id: aiMessageId,
      type: 'ai',
      text: '', // Start with empty text, tokens will append here
    };
    setChatHistory(prevHistory => [...prevHistory, initialAiMessage]);

    const onToken = (token: string) => {
      setChatHistory(prevHistory =>
        prevHistory.map(msg =>
          msg.id === aiMessageId ? { ...msg, text: msg.text + token } : msg
        )
      );
    };

    const onComplete = () => {
      console.log('Streaming complete.');
      setIsLoading(false);
    };

    const onError = (error: Error) => {
      console.error('Streaming error:', error);
      setChatHistory(prevHistory =>
        prevHistory.map(msg =>
          msg.id === aiMessageId
            ? { ...msg, text: msg.text + `\n\nError: ${error.message || 'Failed to get full response.'}` }
            : msg
        )
      );
      setError(error.message || 'Failed to get an answer stream.');
      setIsLoading(false);
    };

    // No await here, as askQuery now uses callbacks for stream handling
    askQuery(userMessage.text, onToken, onComplete, onError);
    // The function itself is async due to operations inside it, but we don't await the stream here.
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
