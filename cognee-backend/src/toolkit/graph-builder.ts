import neo4j, { Driver, Session, QueryResult } from 'neo4j-driver';
import { Document } from '@langchain/core/documents';
import { ChatGoogleGenerativeAI } from '@langchain/google-genai';
import {
  NEO4J_URI,
  NEO4J_USERNAME,
  NEO4J_PASSWORD,
  GEMINI_API_KEY,
} from '../config';
import {
  ChatPromptTemplate,
  HumanMessagePromptTemplate,
  SystemMessagePromptTemplate,
} from '@langchain/core/prompts';
import { StringOutputParser } from '@langchain/core/output_parsers';
import { BaseMessage } from '@langchain/core/messages';

let driver: Driver | undefined;
let llm: ChatGoogleGenerativeAI | undefined;

// Initialize Neo4j Driver
try {
  if (!NEO4J_URI || !NEO4J_USERNAME || !NEO4J_PASSWORD) {
    console.warn('Neo4j connection details (URI, USERNAME, PASSWORD) are not fully set in config. Graph operations will be unavailable.');
  } else {
    driver = neo4j.driver(NEO4J_URI, neo4j.auth.basic(NEO4J_USERNAME, NEO4J_PASSWORD));
    // driver.verifyConnectivity() // We can call this in a dedicated init function if needed
    //   .then(() => console.log('Successfully connected to Neo4j for graph-builder.'))
    //   .catch((error: any) => console.error('Neo4j connection verification failed for graph-builder:', error.message));
    console.log('Neo4j driver initialized for graph-builder.');
  }
} catch (error) {
  console.error('Failed to create Neo4j driver in graph-builder:', error);
  driver = undefined; // Ensure driver is undefined if init fails
}

// Initialize LLM
if (GEMINI_API_KEY) {
  llm = new ChatGoogleGenerativeAI({
    apiKey: GEMINI_API_KEY,
    modelName: 'gemini-2.0-flash',
    temperature: 0.2, // Slightly lower temp for more deterministic graph structure generation
  });
  console.log('ChatGoogleGenerativeAI (gemini-2.0-flash) initialized for graph-builder.');
} else {
  console.warn('GEMINI_API_KEY is not set in graph-builder. LLM-dependent graph operations will be unavailable.');
}

function getDriverInstance(): Driver {
  if (!driver) {
    // Attempt to re-initialize if config might have updated or was delayed
    if (NEO4J_URI && NEO4J_USERNAME && NEO4J_PASSWORD) {
        driver = neo4j.driver(NEO4J_URI, neo4j.auth.basic(NEO4J_USERNAME, NEO4J_PASSWORD));
        console.log('Re-initialized Neo4j driver in graph-builder.');
    } else {
        throw new Error('Neo4j driver not initialized. Check connection details in config.');
    }
  }
  return driver;
}

function getLlmInstance(): ChatGoogleGenerativeAI {
  if (!llm) {
     if (GEMINI_API_KEY) {
        llm = new ChatGoogleGenerativeAI({
            apiKey: GEMINI_API_KEY,
            modelName: 'gemini-2.0-flash',
            temperature: 0.2,
        });
        console.log('Re-initialized ChatGoogleGenerativeAI in graph-builder.');
        return llm;
    }
    throw new Error('LLM not initialized in graph-builder. GEMINI_API_KEY is missing.');
  }
  return llm;
}

export async function executeCypherQuery(query: string, params?: Record<string, any>): Promise<QueryResult> {
  const currentDriver = getDriverInstance();
  let session: Session | undefined;
  try {
    session = currentDriver.session();
    console.log(`Executing Cypher: ${query} with params: ${JSON.stringify(params)}`);
    const result = await session.run(query, params);
    return result;
  } catch (error: any) {
    console.error(`Error executing Cypher query in graph-builder: ${query}`, error.message, error.stack);
    throw new Error(`Failed to execute Cypher query: ${error.message}`);
  } finally {
    if (session) {
      await session.close();
    }
  }
}

// Interface for structured graph data from LLM
export interface GraphElements {
  nodes: Array<{ id: string; type: string; properties: Record<string, any> }>; // id should be unique concept identifier from text
  relationships: Array<{ sourceId: string; targetId: string; type: string; properties?: Record<string, any> }>;
}


const EXTRACT_GRAPH_PROMPT_TEMPLATE =
  `From the text below, extract entities and their relationships to form a knowledge graph.
Return the result as a single valid JSON object with two keys: "nodes" and "relationships".
The "nodes" key should have a value of an array of objects, where each object has "id" (a unique identifier derived from the entity name or concept), "type" (a general category for the entity, e.g., "Person", "Organization", "Concept"), and "properties" (an object of key-value pairs, including at least a "name" property).
The "relationships" key should have a value of an array of objects, where each object has "sourceId" (the id of the source node), "targetId" (the id of the target node), "type" (the name of the relationship, e.g., "FOUNDED_BY", "WORKS_AT", "RELATED_TO"), and optionally "properties" (an object for relationship attributes).
Focus on the most important entities and relationships. Ensure IDs are consistent. If no meaningful graph can be extracted, return an object with empty arrays for nodes and relationships.

Example Text: 'Apple Inc. was co-founded by Steve Jobs, Steve Wozniak, and Ronald Wayne. Tim Cook is the current CEO of Apple.'
Example JSON Output:
{
  "nodes": [
    {"id": "apple_inc", "type": "Organization", "properties": {"name": "Apple Inc."}},
    {"id": "steve_jobs", "type": "Person", "properties": {"name": "Steve Jobs"}},
    {"id": "steve_wozniak", "type": "Person", "properties": {"name": "Steve Wozniak"}},
    {"id": "ronald_wayne", "type": "Person", "properties": {"name": "Ronald Wayne"}},
    {"id": "tim_cook", "type": "Person", "properties": {"name": "Tim Cook"}}
  ],
  "relationships": [
    {"sourceId": "apple_inc", "targetId": "steve_jobs", "type": "CO_FOUNDED_BY"},
    {"sourceId": "apple_inc", "targetId": "steve_wozniak", "type": "CO_FOUNDED_BY"},
    {"sourceId": "apple_inc", "targetId": "ronald_wayne", "type": "CO_FOUNDED_BY"},
    {"sourceId": "tim_cook", "targetId": "apple_inc", "type": "CEO_OF"}
  ]
}

Text to process:
'{document_content}'

JSON Output:`;


export async function extractGraphElementsFromDocument(document: Document): Promise<GraphElements> {
  const currentLlm = getLlmInstance();
  const prompt = ChatPromptTemplate.fromMessages([
    new SystemMessage("You are an expert in knowledge graph extraction. Your output must be a single valid JSON object with 'nodes' and 'relationships' keys, as per the user's instructions. Do not include any other text or markdown formatting."),
    new HumanMessage(EXTRACT_GRAPH_PROMPT_TEMPLATE),
  ]);
  const parser = new StringOutputParser(); // Will parse JSON manually after ensuring it's clean
  const chain = prompt.pipe(currentLlm).pipe(parser);

  try {
    console.log(`Extracting graph elements from document (source: ${document.metadata?.source || 'unknown'}). Snippet: ${document.pageContent.substring(0,100)}...`);
    const llmResponse = await chain.invoke({ document_content: document.pageContent });

    let jsonString = llmResponse.trim();
    if (jsonString.startsWith('```json')) {
      jsonString = jsonString.substring(7);
      if (jsonString.endsWith('```')) {
        jsonString = jsonString.substring(0, jsonString.length - 3);
      }
      jsonString = jsonString.trim();
    }
     if (!jsonString.startsWith('{') || !jsonString.endsWith('}')) {
        console.error('LLM response for graph elements was not a JSON object string after trimming potential markdown:', jsonString);
        const startIndex = jsonString.indexOf('{');
        const endIndex = jsonString.lastIndexOf('}');
        if (startIndex !== -1 && endIndex !== -1 && endIndex > startIndex) {
            jsonString = jsonString.substring(startIndex, endIndex + 1);
        } else {
            console.error('Could not reliably extract JSON object from response.');
            return { nodes: [], relationships: [] };
        }
    }


    const graphElements = JSON.parse(jsonString) as GraphElements;

    // Basic validation
    if (!graphElements || !Array.isArray(graphElements.nodes) || !Array.isArray(graphElements.relationships)) {
      console.warn('LLM output for graph extraction was not in the expected format. Returning empty graph.');
      return { nodes: [], relationships: [] };
    }

    console.log(`Extracted ${graphElements.nodes.length} nodes and ${graphElements.relationships.length} relationships.`);
    return graphElements;
  } catch (error: any) {
    console.error(`Error extracting graph elements from document: ${error.message}`, error.stack);
    return { nodes: [], relationships: [] }; // Return empty graph on error
  }
}


export async function addGraphElementsToNeo4j(graphElements: GraphElements): Promise<void> {
  if (graphElements.nodes.length === 0 && graphElements.relationships.length === 0) {
    console.log("No graph elements to add to Neo4j.");
    return;
  }

  const currentDriver = getDriverInstance();
  const session = currentDriver.session();

  try {
    console.log(`Adding ${graphElements.nodes.length} nodes and ${graphElements.relationships.length} relationships to Neo4j.`);
    // Using a transaction for atomicity
    await session.writeTransaction(async tx => {
      for (const node of graphElements.nodes) {
        // Ensure properties is not undefined
        const properties = node.properties || {};
        // MERGE based on a unique ID if available, otherwise by name within a type.
        // For this example, we assume 'id' is a conceptual unique key derived from text, and 'name' is a primary display property.
        // A more robust solution might involve generating deterministic UUIDs based on content or a combination of properties.
        await tx.run(
          // Using a generic 'Resource' label if node.type is too variable or for simplicity.
          // Or, use dynamic labels: `MERGE (n:\`${node.type}\` {id: $id}) SET n += $properties`, but sanitize node.type.
          `MERGE (n:Resource {id: $id}) SET n += $properties, n.nodeType = $nodeType`,
          { id: node.id, properties: properties, nodeType: node.type }
        );
      }

      for (const rel of graphElements.relationships) {
        // Ensure properties is not undefined
        const properties = rel.properties || {};
        // Use dynamic relationship type, ensuring 'rel.type' is sanitized or from a controlled vocabulary.
        // For safety, sanitize rel.type (e.g., ensure it's alphanumeric). A simple placeholder for now.
        const sanitizedRelType = rel.type.replace(/[^a-zA-Z0-9_]/g, '_').toUpperCase();
        if (!sanitizedRelType) {
            console.warn(\`Skipping relationship due to empty sanitized type from original: \${rel.type}\`);
            continue;
        }
        await tx.run(
          \`MATCH (source:Resource {id: \$sourceId})
            MATCH (target:Resource {id: \$targetId})
            MERGE (source)-[r:\`${sanitizedRelType}\`]->(target)
            SET r += \$properties\`,
          { sourceId: rel.sourceId, targetId: rel.targetId, properties: properties }
        );
      }
    });
    console.log("Successfully added graph elements to Neo4j.");
  } catch (error: any) {
    console.error('Error adding graph elements to Neo4j:', error.message, error.stack);
    // Consider if partial additions should be rolled back or handled; transaction helps.
    throw new Error(`Failed to add graph elements to Neo4j: ${error.message}`);
  } finally {
    await session.close();
  }
}

/**
 * Processes documents, extracts graph elements, and adds them to Neo4j.
 */
export async function documentsToGraph(documents: Document[]): Promise<void> {
    console.log(\`Starting graph extraction from ${documents.length} documents.\`);
    for (const doc of documents) {
        try {
            console.log(`Processing document with source: ${doc.metadata?.source}`);
            const graphElements = await extractGraphElementsFromDocument(doc);
            if (graphElements.nodes.length > 0 || graphElements.relationships.length > 0) {
                await addGraphElementsToNeo4j(graphElements);
            } else {
                console.log(\`No graph elements extracted from document: ${doc.metadata?.source}\`);
            }
        } catch (error) {
            console.error(\`Failed to process document to graph (source: ${doc.metadata?.source || 'unknown'}): \`, error);
            // Continue with next document
        }
    }
    console.log("Finished processing all documents for graph extraction.");
}


// Placeholder for queryGraph function (natural language to Cypher via LLM)
// This will be similar to generateCypherQuery in llmService but might use specific prompts
// for graph context and then execute the query.
const GENERATE_CYPHER_FOR_QA_PROMPT =
  \`Given the graph schema (node labels, relationship types, properties) and a question,
generate a Cypher query to answer the question.
Only return the Cypher query, with no explanations, comments, or markdown.
Schema:
{schema}

Question: {question}
Cypher Query:\`;

export async function queryGraph(naturalLanguageQuestion: string, graphSchemaSummary?: string): Promise<any[]> {
  const currentLlm = getLlmInstance();
  let schemaForPrompt = graphSchemaSummary;

  if (!schemaForPrompt) {
    try {
        const { nodeLabels, relationshipTypes } = await fetchGraphSchemaSummary(); // Assuming this function is also part of this module or imported
        schemaForPrompt = \`Node Labels: \${nodeLabels.join(', ')}. Relationship Types: \${relationshipTypes.join(', ')}.\`; // Basic schema
    } catch (error) {
        console.warn("Could not fetch graph schema for queryGraph, using default.", error);
        schemaForPrompt = "Nodes have 'name' and 'id' properties. Relationships have 'type'.";
    }
  }

  const prompt = ChatPromptTemplate.fromMessages([
    new SystemMessage("You are an expert Cypher query generator for question answering. Only return the Cypher query. No explanations, comments, or markdown."),
    new HumanMessage(GENERATE_CYPHER_FOR_QA_PROMPT),
  ]);
  const chain = prompt.pipe(currentLlm).pipe(new StringOutputParser());

  try {
    const cypherQuery = await chain.invoke({
      schema: schemaForPrompt,
      question: naturalLanguageQuestion,
    });
    console.log(\`Generated Cypher for graph query: \${cypherQuery}\`);

    if (!cypherQuery || cypherQuery.toLowerCase().includes("i cannot answer")) {
        console.warn("LLM could not generate a valid Cypher query for the question.");
        return [{ warning: "Could not translate question to a graph query.", query: cypherQuery }];
    }

    const result = await executeCypherQuery(cypherQuery.trim());
    return result.records.map(record => record.toObject());
  } catch (error: any) {
    console.error(\`Error in queryGraph for question "\${naturalLanguageQuestion}":\`, error.message, error.stack);
    throw error; // Re-throw to be handled by caller
  }
}

export async function fetchGraphSchemaSummary(): Promise<{ nodeLabels: string[], relationshipTypes: string[], propertyKeys: string[] }> {
  console.log('Fetching graph schema summary (labels, rel types, properties)...');
  const currentDriver = getDriverInstance();
  const session = currentDriver.session();
  try {
    const labelsResult = await session.run('CALL db.labels() YIELD label RETURN collect(label) AS nodeLabels');
    const nodeLabels: string[] = (labelsResult.records.length > 0 && labelsResult.records[0].get('nodeLabels')) ? labelsResult.records[0].get('nodeLabels') : [];

    const typesResult = await session.run('CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) AS relationshipTypes');
    const relationshipTypes: string[] = (typesResult.records.length > 0 && typesResult.records[0].get('relationshipTypes')) ? typesResult.records[0].get('relationshipTypes') : [];

    const propertiesResult = await session.run('CALL db.propertyKeys() YIELD propertyKey RETURN collect(propertyKey) AS propertyKeys');
    const propertyKeys: string[] = (propertiesResult.records.length > 0 && propertiesResult.records[0].get('propertyKeys')) ? propertiesResult.records[0].get('propertyKeys') : [];

    console.log(\`Found labels: \${nodeLabels.join(', ')}, types: \${relationshipTypes.join(', ')}, properties: \${propertyKeys.join(', ')}\`);
    return { nodeLabels, relationshipTypes, propertyKeys };
  } catch (error: any) {
    console.error('Error fetching graph schema summary:', error.message, error.stack);
    throw new Error(\`Failed to fetch graph schema summary: \${error.message}\`);
  } finally {
    await session.close();
  }
}


console.log('graph-builder.ts loaded');
