import OpenAI from 'openai';
import { extractSPO, SPOTriple } from '../llmService';
// import { OPENAI_API_KEY } from '../../config'; // Not used directly, but llmService uses it

// Mock the OpenAI SDK
jest.mock('openai');

// Mock config to control OPENAI_API_KEY for tests
// This will be the default mock for most tests in this suite
let mockApiKey = 'test-api-key'; // This will be used by the getter in the mock below
jest.mock('../../config', () => ({
  __esModule: true,
  get OPENAI_API_KEY() { return mockApiKey; } // Use a getter to allow dynamic changes by reassigning mockApiKey
}));

const mockChatCompletionsCreate = jest.fn(); // Renamed for clarity
let originalApiKeyForFileScope: string | undefined; // For llmService.test.ts file scope

describe('LLM Service - extractSPO', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Mock for extractSPO
    (OpenAI as jest.Mock).mockImplementation(() => ({
      chat: {
        completions: {
          create: mockChatCompletionsCreate,
        },
      },
      // embeddings: { create: jest.fn() } // Add a default embeddings mock if OpenAI is constructed early
    }));
    mockApiKey = 'test-api-key'; // Default for extractSPO tests
    originalApiKeyForFileScope = mockApiKey; // Store it if needed by other describe blocks directly
  });

  // afterEach for extractSPO if needed, or rely on file-level afterEach if we add one

  describe('With API Key', () => {
    // mockApiKey is 'test-api-key' here due to beforeEach

    it('should call OpenAI API and return parsed SPO triples', async () => {
      const mockLLMResponse: SPOTriple[] = [{ subject: 'S', relation: 'R', object: 'O' }];
      mockChatCompletionsCreate.mockResolvedValue({
        choices: [{ message: { content: JSON.stringify(mockLLMResponse) } }],
      });

      const textChunk = 'Some text';
      const result = await extractSPO(textChunk);

      expect(OpenAI).toHaveBeenCalledWith({ apiKey: 'test-api-key' });
      expect(mockChatCompletionsCreate).toHaveBeenCalledWith(expect.objectContaining({
        model: 'gpt-3.5-turbo',
        messages: expect.arrayContaining([
          expect.objectContaining({ role: 'user', content: expect.stringContaining(textChunk) })
        ]),
      }));
      expect(result).toEqual(mockLLMResponse);
    });

    it('should handle empty or malformed JSON response from LLM', async () => {
      mockChatCompletionsCreate.mockResolvedValue({ choices: [{ message: { content: 'Not a JSON' } }] });
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {}); // Suppress console.error for this test
      const result = await extractSPO('Some text');
      expect(result).toEqual([]);
      expect(consoleErrorSpy).toHaveBeenCalledWith(expect.stringContaining('LLM response was not a valid array of SPO triples or had incorrect structure:'), 'Not a JSON');
      consoleErrorSpy.mockRestore();
    });

    it('should handle LLM API errors', async () => {
      mockChatCompletionsCreate.mockRejectedValue(new Error('API Error'));
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {}); // Suppress console.error
      const result = await extractSPO('Some text');
      expect(result).toEqual([]);
      expect(consoleErrorSpy).toHaveBeenCalledWith('Error calling OpenAI API or parsing response:', 'API Error');
      consoleErrorSpy.mockRestore();
    });

    it('should correctly parse JSON wrapped in markdown', async () => {
        const mockLLMResponse: SPOTriple[] = [{ subject: 'S', relation: 'R', object: 'O' }];
        mockChatCompletionsCreate.mockResolvedValue({
          choices: [{ message: { content: '```json\n' + JSON.stringify(mockLLMResponse) + '\n```' } }],
        });
        const result = await extractSPO('Some text');
        expect(result).toEqual(mockLLMResponse);
    });
  });

  describe('Without API Key for SPO extraction', () => {
    beforeAll(() => {
      mockApiKey = ''; // Set API key to empty for this block
    });

    afterAll(() => {
        mockApiKey = 'test-api-key'; // Restore default API key
    });

    it('should return mock data if API key is missing and text matches mock condition', async () => {
      jest.resetModules();
      const { extractSPO: extractSPOFresh } = require('../llmService');
      const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});
      const consoleLogSpy = jest.spyOn(console, 'log').mockImplementation(() => {});

      const result = await extractSPOFresh('Elon Musk test');

      expect(result).toEqual([
        { subject: 'Elon Musk', relation: 'founded', object: 'SpaceX (mocked)' },
        { subject: 'SpaceX (mocked)', relation: 'launched', object: 'Falcon 9 (mocked)' },
      ]);
      expect(consoleWarnSpy).toHaveBeenCalledWith(expect.stringContaining('OPENAI_API_KEY is not set'));
      expect(consoleLogSpy).toHaveBeenCalledWith(expect.stringContaining('OpenAI client not initialized. Returning mock SPO data'));

      consoleWarnSpy.mockRestore();
      consoleLogSpy.mockRestore();
    });

    it('should return empty array if API key is missing and text does not match mock condition', async () => {
        jest.resetModules();
        const { extractSPO: extractSPOFresh } = require('../llmService');
        const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});
        const consoleLogSpy = jest.spyOn(console, 'log').mockImplementation(() => {});

        const result = await extractSPOFresh('Some other text');
        expect(result).toEqual([]);
        expect(consoleWarnSpy).toHaveBeenCalledWith(expect.stringContaining('OPENAI_API_KEY is not set'));
        expect(consoleLogSpy).toHaveBeenCalledWith(expect.stringContaining('OpenAI client not initialized. Returning mock SPO data'));

        consoleWarnSpy.mockRestore();
        consoleLogSpy.mockRestore();
    });
  });
});

// Append new tests for generateEmbeddings
describe('LLM Service - generateEmbeddings', () => {
    const mockEmbeddingsCreate = jest.fn();
    // originalApiKeyForFileScope should be used here to ensure proper restoration
    // It's better to manage mockApiKey state carefully for each describe block if they interfere.

    beforeEach(() => {
        jest.clearAllMocks();
        (OpenAI as jest.Mock).mockImplementation(() => ({
            chat: { // Keep chat mock for safety, though not directly used by generateEmbeddings
                completions: { create: mockChatCompletionsCreate }
            },
            embeddings: {
                create: mockEmbeddingsCreate
            }
        }));
        // Save the current mockApiKey state before this describe block potentially changes it
        originalApiKeyForFileScope = mockApiKey;
    });

    afterEach(() => {
        // Restore mockApiKey to what it was before this describe block
        mockApiKey = originalApiKeyForFileScope;
        jest.restoreAllMocks(); // Restore spies
    });

    describe('With API Key for Embeddings', () => {
        beforeEach(() => {
            mockApiKey = 'test-api-key-embeddings'; // Set specific API key for these tests
        });

        it('should call OpenAI embeddings API and return embeddings', async () => {
            const texts = ['hello world', 'test text'];
            const mockApiResponse = {
                data: [
                    { index: 0, embedding: Array(1536).fill(0.1) },
                    { index: 1, embedding: Array(1536).fill(0.2) },
                ],
            };
            mockEmbeddingsCreate.mockResolvedValue(mockApiResponse);

            // Re-importing llmService to pick up the change in mockApiKey via the config mock
            jest.resetModules();
            const { generateEmbeddings } = require('../llmService');
            const result = await generateEmbeddings(texts);

            expect(OpenAI).toHaveBeenCalledWith({ apiKey: 'test-api-key-embeddings' });
            expect(mockEmbeddingsCreate).toHaveBeenCalledWith({
                model: 'text-embedding-ada-002',
                input: texts.map(t => t.replace(/\n/g, ' ')),
            });
            expect(result).toEqual([Array(1536).fill(0.1), Array(1536).fill(0.2)]);
        });

        it('should handle empty or malformed response from OpenAI embeddings', async () => {
            mockEmbeddingsCreate.mockResolvedValue({ data: [] }); // Empty data
            jest.resetModules();
            const { generateEmbeddings } = require('../llmService');
            const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
            const result = await generateEmbeddings(['test']);
            expect(result[0]).toEqual(Array(1536).fill(0.0)); // Returns mock
            expect(consoleErrorSpy).toHaveBeenCalledWith('OpenAI embeddings response is empty or malformed.');
            consoleErrorSpy.mockRestore();
        });

        it('should handle OpenAI API errors for embeddings', async () => {
            mockEmbeddingsCreate.mockRejectedValue(new Error('Embedding API Error'));
            jest.resetModules();
            const { generateEmbeddings } = require('../llmService');
            const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
            const result = await generateEmbeddings(['test']);
            expect(result[0]).toEqual(Array(1536).fill(0.0)); // Returns mock
            expect(consoleErrorSpy).toHaveBeenCalledWith('Error calling OpenAI embeddings API:', 'Embedding API Error');
            consoleErrorSpy.mockRestore();
        });

        it('should return empty array for empty input texts for embeddings', async () => {
            jest.resetModules();
            const { generateEmbeddings } = require('../llmService');
            const result = await generateEmbeddings([]);
            expect(result).toEqual([]);
        });
    });

    describe('Without API Key for Embeddings', () => {
        beforeAll(() => { // Use beforeAll for this block to set mockApiKey once
            mockApiKey = '';
        });

        afterAll(() => { // Restore after all tests in this block
            mockApiKey = 'test-api-key-embeddings'; // Or whatever the default should be after this
        });

        it('should return mock embeddings if API key is missing', async () => {
            jest.resetModules();
            const { generateEmbeddings: generateEmbeddingsFresh } = require('../llmService');
            const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});
            const texts = ['test'];
            const result = await generateEmbeddingsFresh(texts);
            expect(result[0]).toEqual(Array(1536).fill(0.0));
            expect(consoleWarnSpy).toHaveBeenCalledWith(expect.stringContaining('OpenAI client not initialized'));
            consoleWarnSpy.mockRestore();
        });
    });
});
