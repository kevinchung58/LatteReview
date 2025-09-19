// src/components/__tests__/ChatInterface.test.tsx
import React from 'react';
import { render, screen, act, waitFor } from '@testing-library/react'; // waitFor added
import userEvent from '@testing-library/user-event';
import ChatInterface from '../ChatInterface'; // Adjust path as needed
import * as apiService from '../../services/apiService'; // To mock askQuery

// Mock the apiService.askQuery function
vi.mock('../../services/apiService', () => ({
  // Need to also mock other exports from apiService if ChatInterface uses them,
  // or if other components imported in tests use them. For now, just askQuery.
  askQuery: vi.fn(),
  // Mock other exports if they exist and are used by any part of the render tree
  ingestFile: vi.fn(),
  getGraphData: vi.fn(),
  getNodeNeighbors: vi.fn(),
}));

describe('ChatInterface Component', () => {
  beforeEach(() => {
    // Reset mocks before each test
    vi.resetAllMocks();
  });

  it('renders the input field, send button, and an empty chat history initially', () => {
    render(<ChatInterface />);
    expect(screen.getByPlaceholderText(/ask a question.../i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
    const chatHistory = screen.getByRole('log');
    expect(chatHistory).toBeInTheDocument();
    // Check for no messages. Children could be the "AI is thinking..." paragraph if isLoading starts true.
    // Assuming isLoading is initially false.
    expect(chatHistory.children.length).toBe(0);
  });

  it('allows typing in the input field', async () => {
    render(<ChatInterface />);
    const input = screen.getByPlaceholderText(/ask a question.../i) as HTMLInputElement;
    await userEvent.type(input, 'Hello AI');
    expect(input.value).toBe('Hello AI');
  });

  it('submits a question, displays user message, and streams AI response', async () => {
    let onTokenCallback: (token: string) => void = () => {};
    let onCompleteCallback: () => void = () => {};

    (apiService.askQuery as vi.Mock).mockImplementation(
      // Simplified: removed async from mock implementation as it just assigns callbacks
      (question, onToken, onComplete, onError) => {
        onTokenCallback = onToken;
        onCompleteCallback = onComplete;
        // Simulate async nature of API call setup if any, before streaming starts
        // For this mock, we can call onToken and onComplete synchronously via act() later
      }
    );

    render(<ChatInterface />);
    const input = screen.getByPlaceholderText(/ask a question.../i);
    const sendButton = screen.getByRole('button', { name: /send/i });

    await userEvent.type(input, 'What is Cognee?');
    await userEvent.click(sendButton);

    // Check user message is displayed
    expect(screen.getByText('You:')).toBeInTheDocument();
    expect(screen.getByText('What is Cognee?')).toBeInTheDocument();
    expect(input).toHaveValue(''); // Input cleared

    // Check initial AI message (empty or placeholder)
    // Need to wait for the initial empty AI message to be added to history
    await waitFor(() => {
        const aiMessages = screen.getAllByText('AI:'); // Will find all elements starting with "AI:"
        expect(aiMessages.length).toBe(1);
        const aiMessageContainer = aiMessages[0].closest('div[class*="messageContent"]');
        expect(aiMessageContainer?.querySelector('p[class*="messageText"]')?.textContent).toBe(''); // Initially empty text
    });


    // Simulate receiving tokens
    act(() => {
      onTokenCallback('Cognee ');
    });
    // Message text should update
    // Re-query the element as its content has changed
    let aiMessageContainer = screen.getAllByText((content, element) => element?.tagName.toLowerCase() === 'p' && element.className.includes('messageLabel') && content.startsWith('AI:'))[0].closest('div[class*="messageContent"]');
    expect(aiMessageContainer?.querySelector('p[class*="messageText"]')?.textContent).toBe('Cognee ');


    act(() => {
      onTokenCallback('is a ');
    });
    aiMessageContainer = screen.getAllByText((content, element) => element?.tagName.toLowerCase() === 'p' && element.className.includes('messageLabel') && content.startsWith('AI:'))[0].closest('div[class*="messageContent"]');
    expect(aiMessageContainer?.querySelector('p[class*="messageText"]')?.textContent).toBe('Cognee is a ');

    act(() => {
      onTokenCallback('project.');
    });
    aiMessageContainer = screen.getAllByText((content, element) => element?.tagName.toLowerCase() === 'p' && element.className.includes('messageLabel') && content.startsWith('AI:'))[0].closest('div[class*="messageContent"]');
    expect(aiMessageContainer?.querySelector('p[class*="messageText"]')?.textContent).toBe('Cognee is a project.');

    // Simulate stream completion
    act(() => {
      onCompleteCallback();
    });
    // Check loading state is cleared
    expect(screen.getByRole('button', { name: /send/i })).toBeEnabled();
    expect(screen.queryByText(/ai is thinking.../i)).not.toBeInTheDocument();
  });

  it('handles API error during streaming', async () => {
     let onErrorCallback: (error: Error) => void = () => {};
     (apiService.askQuery as vi.Mock).mockImplementation(
         (question, onToken, onComplete, onError) => { // Removed async
             onErrorCallback = onError;
         }
     );

     render(<ChatInterface />);
     const input = screen.getByPlaceholderText(/ask a question.../i);
     const sendButton = screen.getByRole('button', { name: /send/i });

     await userEvent.type(input, 'Error test');
     await userEvent.click(sendButton);

     // Wait for the initial empty AI message
     await waitFor(() => {
        expect(screen.getAllByText('AI:').length).toBe(1);
     });

     act(() => {
         onErrorCallback(new Error('Stream failed'));
     });

     // Check that the AI message now contains the error
     const aiMessageContainer = screen.getAllByText((content, element) => element?.tagName.toLowerCase() === 'p' && element.className.includes('messageLabel') && content.startsWith('AI:'))[0].closest('div[class*="messageContent"]');
     expect(aiMessageContainer?.querySelector('p[class*="messageText"]')?.textContent).toContain('Error: Stream failed');

     // Check that the general error display at the bottom of the form is also shown
     expect(screen.getByText(/failed to get an answer stream/i)).toBeInTheDocument();
  });

 it('shows error if submitting an empty question', async () => {
     render(<ChatInterface />);
     const sendButton = screen.getByRole('button', { name: /send/i });
     await userEvent.click(sendButton);
     expect(apiService.askQuery).not.toHaveBeenCalled();
     expect(screen.getByText(/please enter a question/i)).toBeInTheDocument();
 });
});
