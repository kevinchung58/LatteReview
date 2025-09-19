import neo4j, { Driver, Session, QueryResult, Neo4jError } from 'neo4j-driver';
import { NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD } from '../config';

let driver: Driver | undefined;

function getDriver(): Driver {
  if (!driver) {
    try {
      driver = neo4j.driver(NEO4J_URI, neo4j.auth.basic(NEO4J_USER, NEO4J_PASSWORD));
      // Verify connectivity during initialization (optional but good practice)
      driver.verifyConnectivity()
        .then(() => console.log('Successfully connected to Neo4j.'))
        .catch((error: Neo4jError) => {
          console.error('Neo4j connection verification failed:', error.message);
          // Depending on policy, you might want to throw here or let operations fail later
        });
    } catch (error) {
      console.error('Failed to create Neo4j driver:', error);
      throw new Error('Could not create Neo4j driver. Check connection details.');
    }
  }
  return driver;
}

export async function executeQuery(query: string, params?: Record<string, any>): Promise<QueryResult> {
  const currentDriver = getDriver();
  let session: Session | undefined;
  try {
    session = currentDriver.session();
    const result = await session.run(query, params);
    return result;
  } catch (error: any) {
    console.error(`Error executing Cypher query: ${query}`, error.message);
    throw new Neo4jError(`Failed to execute query. ${error.message}`, error.code);
  } finally {
    if (session) {
      await session.close();
    }
  }
}

// Optional: Function to save SPO triples (will be refined in a later step)
export async function saveTriples(triples: Array<{ subject: string; relation: string; object: string }>): Promise<void> {
  for (const triple of triples) {
    const query = `
      MERGE (s:Entity {name: $subject})
      MERGE (o:Entity {name: $object})
      MERGE (s)-[r:RELATIONSHIP {type: $relation}]->(o)
    `;
    // Note: For relationship type, it's common to use dynamic relationship types like MERGE (s)-[r:\`${relation}\`]->(o)
    // However, this requires sanitization of the relation string to prevent injection if it's user-generated.
    // For now, using a generic :RELATIONSHIP with a 'type' property is safer.
    await executeQuery(query, triple);
    console.log(`Saved triple: ${triple.subject} -[${triple.relation}]-> ${triple.object}`);
  }
}

export async function closeDriver(): Promise<void> {
  if (driver) {
    await driver.close();
    driver = undefined;
    console.log('Neo4j driver closed.');
  }
}

// Graceful shutdown (optional, useful for standalone scripts or specific server setups)
process.on('exit', async () => {
  await closeDriver();
});

// Exported for testing purposes only
export function _resetDriverForTesting() {
  if (driver) {
    // It's good practice to ensure the driver is closed before undefining it,
    // though in a mock environment 'close' might be a jest.fn()
    // For real driver instances, this would be important.
    const promise = driver.close();
    if (promise && typeof promise.then === 'function') {
      promise.catch(e => console.error("Error closing driver during test reset:", e));
    }
  }
  driver = undefined;
}
