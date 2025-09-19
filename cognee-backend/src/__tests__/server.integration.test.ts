import request from 'supertest';
import express from 'express'; // Import express to type 'app' if not already available globally
import { মোকাবিQueryAgainstGraph, মোকাবিSearchVectorStore } from '../services/queryOrchestrationService';
import { মোকাবিSynthesizeAnswerWithContext } from '../services/llmService';

// Mock the services that the /query endpoint uses
jest.mock('../services/queryOrchestrationService', () => ({
  executeQueryAgainstGraph: jest.fn(),
  searchVectorStore: jest.fn(),
}));
jest.mock('../services/llmService', () => ({
  // Keep existing mocks if any, or add new ones
  // Need to ensure all functions used by the module being tested (server.ts -> query route) are mocked
  // or provided. For /query, synthesizeAnswerWithContext is key.
  // Assuming other functions like generateEmbeddings, extractSPO are not directly called by /query route,
  // but by services that are themselves mocked (like queryOrchestrationService).
  synthesizeAnswerWithContext: jest.fn(),
  // Mock other llmService functions if server.ts directly calls them and they are not part of deeper mocks
}));


// We need to import the app from server.ts.
// However, server.ts starts the server by calling app.listen().
// For integration tests with supertest, we need the 'app' instance without it already listening.
// This typically requires refactoring server.ts to export 'app' before calling 'listen',
// or having a separate app.ts and server.ts (where server.ts imports app from app.ts and calls listen).

// Assuming a refactor where 'app' can be imported (e.g., app.ts exports app, server.ts imports and listens):
// For now, let's proceed as if 'app' can be imported. If server.ts execution causes issues,
// this part of the test will highlight it.
// Due to the current structure of server.ts (app.listen is top-level),
// importing it directly will try to start the server, which can lead to EADDRINUSE errors in tests.
// This is a common challenge. The "solution" for this test would be to conditionally export app
// or restructure. For this subtask, I will write the test as if app is exportable.

// Placeholder: server.ts would need to be refactored to export app, e.g.
// let server; const app = express(); ... export { app, server };
// if (require.main === module) { server = app.listen(...); }
// For now, we'll mock the app listener for tests.

let app: express.Application;

beforeAll(async () => {
    // Dynamically import app AFTER mocks are set up
    // And potentially prevent app.listen from being called in test environment
    process.env.NODE_ENV = 'test'; // Common practice
    const serverModule = require('../server'); // Path to your server.ts
    app = serverModule.app; // Assuming server.ts exports 'app'
});


describe('POST /query Integration Test', () => {
  beforeEach(() => {
    // Reset mocks before each test
    (executeQueryAgainstGraph as jest.Mock).mockReset();
    (searchVectorStore as jest.Mock).mockReset();
    (synthesizeAnswerWithContext as jest.Mock).mockReset();
  });

  it('should return a 200 OK with an answer for a valid question', async () => {
    const mockQuestion = 'What is the meaning of life?';
    const mockGraphContext = ['Graph context item'];
    const mockVectorContext = ['Vector context item'];
    const mockAnswer = '42, based on context.';

    (executeQueryAgainstGraph as jest.Mock).mockResolvedValue(mockGraphContext);
    (searchVectorStore as jest.Mock).mockResolvedValue(mockVectorContext);
    (synthesizeAnswerWithContext as jest.Mock).mockResolvedValue(mockAnswer);

    const response = await request(app)
      .post('/query')
      .send({ question: mockQuestion })
      .expect('Content-Type', /json/)
      .expect(200);

    expect(response.body).toEqual({
      question: mockQuestion,
      answer: mockAnswer,
      graphContextItems: mockGraphContext,
      vectorContextItems: mockVectorContext,
    });
    expect(executeQueryAgainstGraph).toHaveBeenCalledWith(mockQuestion);
    expect(searchVectorStore).toHaveBeenCalledWith(mockQuestion, expect.any(String)); // CHROMA_COLLECTION_NAME
    expect(synthesizeAnswerWithContext).toHaveBeenCalledWith(mockQuestion, [...mockGraphContext, ...mockVectorContext]);
  });

  it('should return a 400 error if question is missing', async () => {
    const response = await request(app)
      .post('/query')
      .send({})
      .expect('Content-Type', /json/)
      .expect(400);

    expect(response.body.message).toContain('question is required');
  });

  it('should return a 400 error if question is not a string', async () => {
    const response = await request(app)
      .post('/query')
      .send({ question: 123 })
      .expect('Content-Type', /json/)
      .expect(400);

    expect(response.body.message).toContain('question is required and must be a string');
  });

  it('should return a 500 error if query orchestration fails', async () => {
    const mockQuestion = 'A failing question';
    (executeQueryAgainstGraph as jest.Mock).mockRejectedValue(new Error('Internal service failure'));

    const response = await request(app)
      .post('/query')
      .send({ question: mockQuestion })
      .expect('Content-Type', /json/)
      .expect(500);

    expect(response.body.message).toContain('Error processing your query');
    expect(response.body.error).toContain('Internal service failure');
  });
});
