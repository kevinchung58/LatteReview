import OpenAI from 'openai';
import { extractSPO, SPOTriple } from '../llmService';
// import { OPENAI_API_KEY } from '../../config'; // Not used directly, but llmService uses it

// Mock the OpenAI SDK
jest.mock('openai');

// Mock config to control OPENAI_API_KEY for tests
// This will be the default mock for most tests in this suite
let mockApiKey = 'test-api-key';
jest.mock('../../config', () => ({
  __esModule: true,
  get OPENAI_API_KEY() { return mockApiKey; } // Use a getter to allow dynamic changes
}));

const mockCreate = jest.fn();

describe('LLM Service - extractSPO', () => {

  beforeEach(() => {
    jest.clearAllMocks();
    (OpenAI as jest.Mock).mockImplementation(() => ({
      chat: {
        completions: {
          create: mockCreate,
        },
      },
    }));
    // Set a default mock API key before each test, can be overridden in specific describe blocks
    mockApiKey = 'test-api-key';
  });

  describe('With API Key', () => {
    // mockApiKey is 'test-api-key' here due to beforeEach

    it('should call OpenAI API and return parsed SPO triples', async () => {
      const mockLLMResponse: SPOTriple[] = [{ subject: 'S', relation: 'R', object: 'O' }];
      mockCreate.mockResolvedValue({
        choices: [{ message: { content: JSON.stringify(mockLLMResponse) } }],
      });

      const textChunk = 'Some text';
      const result = await extractSPO(textChunk);

      expect(OpenAI).toHaveBeenCalledWith({ apiKey: 'test-api-key' });
      expect(mockCreate).toHaveBeenCalledWith(expect.objectContaining({
        model: 'gpt-3.5-turbo',
        messages: expect.arrayContaining([
          expect.objectContaining({ role: 'user', content: expect.stringContaining(textChunk) })
        ]),
      }));
      expect(result).toEqual(mockLLMResponse);
    });

    it('should handle empty or malformed JSON response from LLM', async () => {
      mockCreate.mockResolvedValue({ choices: [{ message: { content: 'Not a JSON' } }] });
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {}); // Suppress console.error for this test
      const result = await extractSPO('Some text');
      expect(result).toEqual([]);
      expect(consoleErrorSpy).toHaveBeenCalledWith(expect.stringContaining('LLM response was not a valid array of SPO triples or had incorrect structure:'), 'Not a JSON');
      consoleErrorSpy.mockRestore();
    });

    it('should handle LLM API errors', async () => {
      mockCreate.mockRejectedValue(new Error('API Error'));
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {}); // Suppress console.error
      const result = await extractSPO('Some text');
      expect(result).toEqual([]);
      expect(consoleErrorSpy).toHaveBeenCalledWith('Error calling OpenAI API or parsing response:', 'API Error');
      consoleErrorSpy.mockRestore();
    });

    it('should correctly parse JSON wrapped in markdown', async () => {
        const mockLLMResponse: SPOTriple[] = [{ subject: 'S', relation: 'R', object: 'O' }];
        mockCreate.mockResolvedValue({
          choices: [{ message: { content: '```json\n' + JSON.stringify(mockLLMResponse) + '\n```' } }],
        });
        const result = await extractSPO('Some text');
        expect(result).toEqual(mockLLMResponse);
    });
  });

  describe('Without API Key', () => {
    beforeAll(() => {
      // Set API key to empty for this block of tests
      mockApiKey = '';
    });

    afterAll(() => {
        // Restore API key if other describe blocks need it (though usually tests are isolated)
        mockApiKey = 'test-api-key';
    });

    it('should return mock data if API key is missing and text matches mock condition', async () => {
      // Reset modules to ensure llmService re-evaluates its openai client based on the new mockApiKey value
      jest.resetModules();
      const { extractSPO: extractSPOFresh } = require('../llmService'); // Re-require llmService

      const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});
      const consoleLogSpy = jest.spyOn(console, 'log').mockImplementation(() => {});

      const result = await extractSPOFresh('Elon Musk test'); // Use the freshly imported function

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
