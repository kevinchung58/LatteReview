import {
  extractGraphElementsFromDocument,
  addGraphElementsToNeo4j,
  queryGraph,
  documentsToGraph,
  fetchGraphSchemaSummary,
  GraphElements
} from '../graph-builder';
import { Document } from '@langchain/core/documents';
import { ChatGoogleGenerativeAI } from '@langchain/google-genai';
import neo4j, { QueryResult } from 'neo4j-driver';

jest.mock('@langchain/google-genai');
jest.mock('neo4j-driver');

describe('Graph Builder Toolkit', () => {
  let mockLlm: Partial<ChatGoogleGenerativeAI>;
  let mockDriver: any;
  let mockSession: any;
  let mockTransaction: any;

  const mockDocument = new Document({ pageContent: 'Steve Jobs co-founded Apple.' });
  const mockGraphElements: GraphElements = {
    nodes: [{ id: 'steve_jobs', type: 'Person', properties: { name: 'Steve Jobs' } }],
    relationships: [],
  };

  beforeEach(() => {
    (ChatGoogleGenerativeAI as jest.Mock).mockClear();
    (neo4j.driver as jest.Mock).mockClear();

    mockLlm = {
      // .pipe().invoke() structure for chain simulation
      pipe: jest.fn().mockReturnThis(),
      invoke: jest.fn().mockResolvedValue(JSON.stringify(mockGraphElements)),
    };
    (ChatGoogleGenerativeAI as jest.Mock).mockImplementation(() => mockLlm);

    mockTransaction = {
      run: jest.fn().mockResolvedValue({ records: [], summary: {} } as QueryResult),
      commit: jest.fn().mockResolvedValue(undefined),
      rollback: jest.fn().mockResolvedValue(undefined),
    };
    mockSession = {
      run: jest.fn().mockResolvedValue({ records: [], summary: {} } as QueryResult),
      writeTransaction: jest.fn(callback => callback(mockTransaction)),
      close: jest.fn().mockResolvedValue(undefined),
    };
    mockDriver = {
      session: jest.fn().mockReturnValue(mockSession),
      verifyConnectivity: jest.fn().mockResolvedValue(undefined),
      close: jest.fn().mockResolvedValue(undefined),
    };
    (neo4j.driver as jest.Mock).mockReturnValue(mockDriver);
  });

  describe('extractGraphElementsFromDocument', () => {
    test('should call LLM and parse its JSON response', async () => {
      const result = await extractGraphElementsFromDocument(mockDocument);
      expect(mockLlm.invoke).toHaveBeenCalled();
      expect(result).toEqual(mockGraphElements);
    });
  });

  describe('addGraphElementsToNeo4j', () => {
    test('should run MERGE queries for nodes and relationships', async () => {
      await addGraphElementsToNeo4j(mockGraphElements);
      expect(mockDriver.session).toHaveBeenCalled();
      expect(mockSession.writeTransaction).toHaveBeenCalled();
      expect(mockTransaction.run).toHaveBeenCalledWith(
        expect.stringContaining('MERGE (n:Resource {id: $id})'),
        expect.any(Object)
      );
    });
  });

  describe('documentsToGraph', () => {
    test('should process each document and add elements', async () => {
       // Spy on the functions to ensure they are called
      const extractSpy = jest.spyOn(globalThis, 'extractGraphElementsFromDocument' as any).mockResolvedValue(mockGraphElements);
      const addSpy = jest.spyOn(globalThis, 'addGraphElementsToNeo4j' as any).mockResolvedValue(undefined);

      await documentsToGraph([mockDocument, mockDocument]);

      expect(extractSpy).toHaveBeenCalledTimes(2);
      expect(addSpy).toHaveBeenCalledTimes(2);

      extractSpy.mockRestore();
      addSpy.mockRestore();
    });
  });

  describe('queryGraph', () => {
    test('should generate Cypher with LLM and execute it', async () => {
      (mockLlm.invoke as jest.Mock).mockResolvedValue('MATCH (n) RETURN n.name AS name'); // LLM returns Cypher
      (mockSession.run as jest.Mock).mockResolvedValue({ records: [{ get: (key: string) => 'Test Node', toObject: () => ({name: 'Test Node'}) }], summary: {} } as unknown as QueryResult);

      // Mock fetchGraphSchemaSummary for this test, assuming it's also part of the module or imported correctly
      jest.spyOn(globalThis, 'fetchGraphSchemaSummary' as any).mockResolvedValue({ nodeLabels: ['TestLabel'], relationshipTypes: ['TEST_REL'], propertyKeys: ['name'] });


      const results = await queryGraph('What is the test node?');
      expect(mockLlm.invoke).toHaveBeenCalledWith(expect.objectContaining({ question: 'What is the test node?' }));
      expect(mockSession.run).toHaveBeenCalledWith('MATCH (n) RETURN n.name AS name', undefined);
      expect(results).toEqual([{name: 'Test Node'}]);
    });
  });

  describe('fetchGraphSchemaSummary', () => {
    test('should call db.labels(), db.relationshipTypes(), and db.propertyKeys()', async () => {
      // Setup mock responses for each call
      (mockSession.run as jest.Mock)
        .mockResolvedValueOnce({ records: [{ get: () => ['Label1'] }], summary: {} } as unknown as QueryResult) // db.labels()
        .mockResolvedValueOnce({ records: [{ get: () => ['REL1'] }], summary: {} } as unknown as QueryResult)   // db.relationshipTypes()
        .mockResolvedValueOnce({ records: [{ get: () => ['prop1'] }], summary: {} } as unknown as QueryResult); // db.propertyKeys()

      const schema = await fetchGraphSchemaSummary();
      expect(mockSession.run).toHaveBeenCalledWith('CALL db.labels() YIELD label RETURN collect(label) AS nodeLabels');
      expect(mockSession.run).toHaveBeenCalledWith('CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) AS relationshipTypes');
      expect(mockSession.run).toHaveBeenCalledWith('CALL db.propertyKeys() YIELD propertyKey RETURN collect(propertyKey) AS propertyKeys');
      expect(schema.nodeLabels).toEqual(['Label1']);
      expect(schema.relationshipTypes).toEqual(['REL1']);
      expect(schema.propertyKeys).toEqual(['prop1']);
    });
  });
});
