import { createRAGChain, createConversationalChain } from '../query-engine';
import { ChatGoogleGenerativeAI } from '@langchain/google-genai';
import { RetrievalQAChain, ConversationalRetrievalQAChain } from 'langchain/chains';
import { VectorStoreRetriever } from '@langchain/core/vectorstores';

jest.mock('@langchain/google-genai');
jest.mock('langchain/chains');

describe('Query Engine Toolkit', () => {
  let mockRetriever: VectorStoreRetriever;

  beforeEach(() => {
    (ChatGoogleGenerativeAI as jest.Mock).mockClear();
    (RetrievalQAChain.fromLLM as jest.Mock).mockClear();
    (ConversationalRetrievalQAChain.fromLLM as jest.Mock).mockClear();

    mockRetriever = {} as VectorStoreRetriever; // Simple mock

    // Mock the static fromLLM methods
    (RetrievalQAChain.fromLLM as jest.Mock).mockReturnValue({ /* mock chain */ });
    (ConversationalRetrievalQAChain.fromLLM as jest.Mock).mockReturnValue({ /* mock chain */ });
  });

  test('createRAGChain should initialize LLM and create RetrievalQAChain', () => {
    createRAGChain(mockRetriever);
    expect(ChatGoogleGenerativeAI).toHaveBeenCalled();
    expect(RetrievalQAChain.fromLLM).toHaveBeenCalledWith(
      expect.any(ChatGoogleGenerativeAI),
      mockRetriever,
      expect.objectContaining({ returnSourceDocuments: true })
    );
  });

  test('createConversationalChain should initialize LLM and create ConversationalRetrievalQAChain', () => {
    createConversationalChain(mockRetriever);
    expect(ChatGoogleGenerativeAI).toHaveBeenCalled();
    expect(ConversationalRetrievalQAChain.fromLLM).toHaveBeenCalledWith(
      expect.any(ChatGoogleGenerativeAI),
      mockRetriever,
      expect.objectContaining({ returnSourceDocuments: true })
    );
  });
});
