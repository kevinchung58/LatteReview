import { addDocuments, createRetriever } from '../vector-store';
import { Chroma } from '@langchain/community/vectorstores/chroma';
import { GoogleGenerativeAIEmbeddings } from '@langchain/google-genai';
import { Document } from '@langchain/core/documents';
import { VectorStoreRetriever } from '@langchain/core/vectorstores';

jest.mock('@langchain/community/vectorstores/chroma');
jest.mock('@langchain/google-genai');

describe('Vector Store Toolkit', () => {
  const mockCollectionName = 'test-collection';
  const mockDocuments = [new Document({ pageContent: 'Test content' })];
  let mockChromaInstance: Partial<Chroma>;

  beforeEach(() => {
    (GoogleGenerativeAIEmbeddings as jest.Mock).mockClear();
    (Chroma as jest.Mock).mockClear();

    mockChromaInstance = {
      addDocuments: jest.fn().mockResolvedValue(undefined),
      asRetriever: jest.fn().mockReturnValue({ /* mock retriever */ } as unknown as VectorStoreRetriever<Chroma>),
    };
    (Chroma as jest.Mock).mockImplementation(() => mockChromaInstance);
  });

  test('addDocuments should initialize Chroma and call addDocuments', async () => {
    await addDocuments(mockDocuments, mockCollectionName);
    expect(GoogleGenerativeAIEmbeddings).toHaveBeenCalled();
    expect(Chroma).toHaveBeenCalledWith(
      expect.any(GoogleGenerativeAIEmbeddings), // Check that an embeddings instance is passed
      { collectionName: mockCollectionName, url: process.env.CHROMA_URL || 'http://localhost:8000' }
    );
    expect(mockChromaInstance.addDocuments).toHaveBeenCalledWith(mockDocuments);
  });

  test('createRetriever should initialize Chroma and call asRetriever', async () => {
    const retriever = await createRetriever(mockCollectionName, 10);
    expect(GoogleGenerativeAIEmbeddings).toHaveBeenCalled();
    expect(Chroma).toHaveBeenCalled();
    expect(mockChromaInstance.asRetriever).toHaveBeenCalledWith({ k: 10 });
    expect(retriever).toBeDefined();
  });

  test('addDocuments should default collection name if not provided', async () => {
    await addDocuments(mockDocuments); // No collectionName
    expect(Chroma).toHaveBeenCalledWith(
      expect.any(GoogleGenerativeAIEmbeddings),
      expect.objectContaining({ collectionName: process.env.CHROMA_COLLECTION_NAME || 'cognee_main_collection' })
    );
  });
});
