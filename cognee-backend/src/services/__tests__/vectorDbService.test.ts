import { ChromaClient, Collection, OpenAIEmbeddingFunction } from 'chromadb';
import {
  getOrCreateCollection,
  addOrUpdateChunks,
  searchSimilarChunks,
  searchSimilarChunksWithText,
  _resetChromaClientForTesting // Assuming an export for resetting client
} from '../vectorDbService';
// Import CHROMA_URL and OPENAI_API_KEY to allow jest.mock to work on them
import { CHROMA_URL, OPENAI_API_KEY } from '../../config';

jest.mock('chromadb');

// Default mock values, can be changed by tests.
let mockChromaUrlValue = 'http://mock-chroma-url:8000';
let mockOpenAiKeyValue = 'mock-openai-key';

jest.mock('../../config', () => ({
  __esModule: true,
  get CHROMA_URL() { return mockChromaUrlValue; },
  get OPENAI_API_KEY() { return mockOpenAiKeyValue; },
}));

const mockCollectionAdd = jest.fn();
const mockCollectionQuery = jest.fn();
const mockGetOrCreateCollectionFn = jest.fn(); // Renamed to avoid conflict with module import
const mockGetCollectionFn = jest.fn();  // Renamed to avoid conflict

const mockCollection = {
  add: mockCollectionAdd,
  query: mockCollectionQuery,
} as unknown as Collection;

let mockChromaClientInstance: any;

beforeEach(() => {
  jest.clearAllMocks();
  _resetChromaClientForTesting(); // Ensure client is reset

  // Setup mock ChromaClient instance for each test
  mockChromaClientInstance = {
     getOrCreateCollection: mockGetOrCreateCollectionFn.mockResolvedValue(mockCollection),
     getCollection: mockGetCollectionFn.mockResolvedValue(mockCollection),
  };
  (ChromaClient as jest.Mock).mockImplementation(() => mockChromaClientInstance);

  // Mock OpenAIEmbeddingFunction if directly used or its instantiation needs mocking
  (OpenAIEmbeddingFunction as jest.Mock).mockImplementation(() => ({
     // mock implementation of embedding function if needed for tests
  }));

  // Reset mock values to defaults for config before each test
  mockChromaUrlValue = 'http://mock-chroma-url:8000';
  mockOpenAiKeyValue = 'mock-openai-key';
});

describe('VectorDB Service', () => {
  describe('getClient (implicitly tested, and error case)', () => {
     it('should throw if CHROMA_URL is not set', () => {
         mockChromaUrlValue = ''; // Set CHROMA_URL to empty for this test
         jest.resetModules(); // Reset modules to re-evaluate config and service state
         const { getClient: getClientFresh } = require('../vectorDbService'); // Re-require with new config

         expect(() => getClientFresh()).toThrow('CHROMA_URL is not set. Vector DB service cannot operate.');

         mockChromaUrlValue = 'http://mock-chroma-url:8000'; // Restore for other tests
         jest.resetModules(); // Reset again to restore normal state for other tests
     });
  });

  describe('getOrCreateCollection', () => {
    it('should call client.getOrCreateCollection', async () => {
      const collectionName = 'test_collection';
      await getOrCreateCollection(collectionName);
      expect(mockChromaClientInstance.getOrCreateCollection).toHaveBeenCalledWith({ name: collectionName });
    });
  });

  describe('addOrUpdateChunks', () => {
    it('should call collection.add with correct parameters', async () => {
      const collectionName = 'test_collection';
      const ids = ['id1'];
      const embeddings = [[0.1]];
      const documents = ['doc1'];
      const metadatas = [{ src: 's1' }];

      await addOrUpdateChunks(collectionName, ids, embeddings, documents, metadatas);
      expect(mockGetOrCreateCollectionFn).toHaveBeenCalledWith({ name: collectionName });
      expect(mockCollectionAdd).toHaveBeenCalledWith({ ids, embeddings, documents, metadatas });
    });

    it('should not call collection.add if ids array is empty', async () => {
     await addOrUpdateChunks('test_collection', [], [], [], []);
     expect(mockCollectionAdd).not.toHaveBeenCalled();
   });
  });

  describe('searchSimilarChunks', () => {
    it('should call collection.query with embeddings', async () => {
      const collectionName = 'test_collection';
      const queryEmbeddings = [[0.2]];
      const k = 3;
      mockCollectionQuery.mockResolvedValue({ documents: [['found_doc1']] });

      const result = await searchSimilarChunks(collectionName, queryEmbeddings, k);
      expect(mockGetOrCreateCollectionFn).toHaveBeenCalledWith({ name: collectionName });
      expect(mockCollectionQuery).toHaveBeenCalledWith({ queryEmbeddings, nResults: k });
      expect(result).toEqual([['found_doc1']]);
    });
    it('should return empty array for empty queryEmbeddings', async () => {
     const result = await searchSimilarChunks('test_collection', [], 5);
     expect(result).toEqual([]);
     expect(mockCollectionQuery).not.toHaveBeenCalled();
    });
  });

  describe('searchSimilarChunksWithText', () => {
     beforeEach(() => {
        // Ensure config is reset for each test in this block if manipulating mockOpenAiKeyValue
        jest.resetModules();
     });

     it('should call collection.query with queryTexts if embedder is available', async () => {
         mockOpenAiKeyValue = 'mock-key'; // Ensure embedder is available
         const { searchSimilarChunksWithText: searchFresh, _resetChromaClientForTesting: resetFresh } = require('../vectorDbService');
         resetFresh(); // Call the reset from the fresh module

         const collectionName = 'text_search_collection';
         const queryTexts = ['query text'];
         const k = 2;
         // Ensure the client mock is fresh for the re-required module
         (ChromaClient as jest.Mock).mockImplementation(() => ({
            getOrCreateCollection: mockGetOrCreateCollectionFn.mockResolvedValue(mockCollection),
            getCollection: mockGetCollectionFn.mockResolvedValue(mockCollection),
         }));
         mockCollectionQuery.mockResolvedValue({ documents: [['found_doc_by_text']] });

         const result = await searchFresh(collectionName, queryTexts, k);
         // getCollection is used by searchSimilarChunksWithText
         expect(mockGetCollectionFn).toHaveBeenCalledWith({name: collectionName, embeddingFunction: expect.any(Object)});
         expect(mockCollectionQuery).toHaveBeenCalledWith({ queryTexts, nResults: k });
         expect(result).toEqual([['found_doc_by_text']]);
     });

     it('should warn and return empty if embedder is not available', async () => {
         mockOpenAiKeyValue = ''; // Ensure embedder is NOT available
         const { searchSimilarChunksWithText: searchFresh, _resetChromaClientForTesting: resetFresh } = require('../vectorDbService');
         resetFresh();
         const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});

         const result = await searchFresh('test_collection', ['query'], 5);
         expect(result).toEqual([[]]); // Expecting array of empty arrays, one for each queryText
         expect(consoleWarnSpy).toHaveBeenCalledWith(expect.stringContaining('OpenAIEmbedder not available'));
         consoleWarnSpy.mockRestore();
     });
  });
});
