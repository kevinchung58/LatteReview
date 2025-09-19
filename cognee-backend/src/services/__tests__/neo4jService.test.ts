import neo4j, { Driver, Session, QueryResult, Neo4jError } from 'neo4j-driver';
import { getDriver, executeQuery, saveTriples, closeDriver, _resetDriverForTesting } from '../neo4jService'; // Assuming an exported reset for testing
import { NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD } from '../../config';

// Mock the neo4j-driver module
jest.mock('neo4j-driver');

describe('Neo4j Service', () => {
  const mockSessionRun = jest.fn();
  const mockSessionClose = jest.fn();
  const mockDriverVerifyConnectivity = jest.fn();
  const mockDriverClose = jest.fn();

  const mockSession = {
    run: mockSessionRun,
    close: mockSessionClose,
  } as unknown as Session;

  const mockDriver = {
    session: jest.fn(() => mockSession),
    verifyConnectivity: mockDriverVerifyConnectivity,
    close: mockDriverClose,
  } as unknown as Driver;

  beforeEach(() => {
    jest.clearAllMocks();
    _resetDriverForTesting(); // Ensure driver is reset before each test
    (neo4j.driver as jest.Mock).mockReturnValue(mockDriver);
    mockDriverVerifyConnectivity.mockResolvedValue(undefined); // Default success for verifyConnectivity
  });

  describe('getDriver', () => {
    it('should create and return a driver on first call', async () => {
      getDriver(); // Call to initialize
      expect(neo4j.driver).toHaveBeenCalledWith(NEO4J_URI, neo4j.auth.basic(NEO4J_USER, NEO4J_PASSWORD));
      expect(mockDriverVerifyConnectivity).toHaveBeenCalled();
    });

    it('should return the same driver instance on subsequent calls', () => {
      const d1 = getDriver();
      const d2 = getDriver();
      expect(d1).toBe(d2);
      expect(neo4j.driver).toHaveBeenCalledTimes(1);
    });

    it('should handle error if neo4j.driver throws', () => {
      (neo4j.driver as jest.Mock).mockImplementationOnce(() => { throw new Error('Driver creation failed'); });
      expect(() => getDriver()).toThrow('Could not create Neo4j driver. Check connection details.');
    });
  });

  describe('executeQuery', () => {
    it('should execute a query successfully', async () => {
      const query = 'RETURN 1';
      const params = { p: 1 };
      const mockResult = { records: [] } as QueryResult;
      mockSessionRun.mockResolvedValue(mockResult);

      const result = await executeQuery(query, params);

      expect(mockDriver.session).toHaveBeenCalled();
      expect(mockSessionRun).toHaveBeenCalledWith(query, params);
      expect(result).toBe(mockResult);
      expect(mockSessionClose).toHaveBeenCalled();
    });

    it('should handle errors during query execution', async () => {
      const query = 'RETURN 1';
      mockSessionRun.mockRejectedValue(new Neo4jError('Query failed', 'ERR_CODE'));

      await expect(executeQuery(query)).rejects.toThrow('Failed to execute query. Query failed');
      expect(mockSessionClose).toHaveBeenCalled();
    });
  });

  describe('saveTriples', () => {
    it('should call executeQuery for each triple', async () => {
      const triples = [
        { subject: 's1', relation: 'r1', object: 'o1' },
        { subject: 's2', relation: 'r2', object: 'o2' },
      ];
      mockSessionRun.mockResolvedValue({ records: [] } as QueryResult); // Mock executeQuery's underlying run

      await saveTriples(triples);

      expect(mockSessionRun).toHaveBeenCalledTimes(triples.length);
      triples.forEach(triple => {
        expect(mockSessionRun).toHaveBeenCalledWith(expect.stringContaining('MERGE (s:Entity {name: $subject})'), triple);
      });
    });

    it('should not call executeQuery for empty triples array', async () => {
      await saveTriples([]);
      expect(mockSessionRun).not.toHaveBeenCalled();
    });
  });

  describe('closeDriver', () => {
    it('should close the driver if it exists', async () => {
      getDriver(); // Initialize driver
      await closeDriver();
      expect(mockDriverClose).toHaveBeenCalled();
    });

    it('should not throw if driver does not exist', async () => {
      await expect(closeDriver()).resolves.toBeUndefined();
      expect(mockDriverClose).not.toHaveBeenCalled();
    });
  });
});
