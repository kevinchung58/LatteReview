import OpenAI from 'openai';
import { OPENAI_API_KEY } from '../config';

// Define the structure for SPO triples
export interface SPOTriple {
  subject: string;
  relation: string;
  object: string;
}

let openai: OpenAI | undefined;

if (OPENAI_API_KEY) {
  openai = new OpenAI({ apiKey: OPENAI_API_KEY });
} else {
  console.warn(
    'OPENAI_API_KEY is not set. LLM service will use mocked responses or be non-functional for actual API calls.'
  );
}

const DEFAULT_SPO_EXTRACTION_PROMPT_TEMPLATE =
`Extract all entities and their relationships from the following text as Subject-Predicate-Object (SPO) triples.\n` +
`Return the result as a valid JSON array, where each object in the array has the keys "subject", "relation", and "object".\n` +
`If no meaningful SPO triples can be extracted, return an empty array.\n\n` +
`Example:\n` +
`Text: 'Elon Musk founded SpaceX. SpaceX launched Falcon 9.'\n` +
`Output: [\n` +
`  { "subject": "Elon Musk", "relation": "founded", "object": "SpaceX" },\n` +
`  { "subject": "SpaceX", "relation": "launched", "object": "Falcon 9" }\n` +
`]\n\n` +
`Text to process:\n` +
`'{text_chunk}'\n\n` +
`JSON Output:\n`;

export async function extractSPO(textChunk: string, promptTemplate?: string): Promise<SPOTriple[]> {
  if (!openai) {
    console.log('OpenAI client not initialized. Returning mock SPO data for chunk: "' + textChunk.substring(0,30) + '..."');
    if (textChunk.toLowerCase().includes('elon musk')) {
      return [
        { subject: 'Elon Musk', relation: 'founded', object: 'SpaceX (mocked)' },
        { subject: 'SpaceX (mocked)', relation: 'launched', object: 'Falcon 9 (mocked)' },
      ];
    }
    return [];
  }

  const currentPrompt = (promptTemplate || DEFAULT_SPO_EXTRACTION_PROMPT_TEMPLATE).replace('{text_chunk}', textChunk);

  try {
    console.log(`Sending request to LLM for chunk: "${textChunk.substring(0, 50)}..."`);
    const response = await openai.chat.completions.create({
      model: 'gpt-3.5-turbo',
      messages: [
        { role: 'system', content: 'You are an expert in knowledge graph extraction and always return valid JSON.' },
        { role: 'user', content: currentPrompt }
      ],
      temperature: 0.1,
      response_format: { type: "json_object" },
    });

    const content = response.choices[0]?.message?.content;
    if (!content) {
      console.error('LLM response content is empty or undefined.');
      return [];
    }
    console.log('LLM raw response:', content);

    let jsonResponseString = content.trim();
    // Attempt to find JSON array within the string if it's not purely JSON (e.g. wrapped in markdown)
    if (jsonResponseString.startsWith('```json')) {
      jsonResponseString = jsonResponseString.substring(7, jsonResponseString.length - 3).trim();
    } else {
      // Fallback for cases where the response might be just the JSON array, possibly with minor surrounding text
      const startIndex = jsonResponseString.indexOf('[');
      const endIndex = jsonResponseString.lastIndexOf(']');
      if (startIndex !== -1 && endIndex !== -1 && endIndex > startIndex) {
        jsonResponseString = jsonResponseString.substring(startIndex, endIndex + 1);
      }
    }

    const parsedTriples = JSON.parse(jsonResponseString);
    if (Array.isArray(parsedTriples) && (parsedTriples.length === 0 || parsedTriples.every(t => typeof t.subject === 'string' && typeof t.relation === 'string' && typeof t.object === 'string'))) {
      console.log(`Extracted ${parsedTriples.length} SPO triples.`);
      return parsedTriples as SPOTriple[];
    } else {
      console.error('LLM response was not a valid array of SPO triples or had incorrect structure:', parsedTriples);
      return [];
    }

  } catch (error: any) {
    console.error('Error calling OpenAI API or parsing response:', error.message);
    if (error.response && error.response.data) {
      console.error('OpenAI Error Details:', error.response.data);
    }
    return [];
  }
}

export async function generateEmbeddings(texts: string[]): Promise<number[][]> {
  if (!openai) {
    console.warn('OpenAI client not initialized. OPENAI_API_KEY might be missing. Returning mock embeddings.');
    // Return mock embeddings (e.g., arrays of zeros with ADA-002 dimension: 1536)
    return texts.map(() => Array(1536).fill(0.0));
  }

  if (!texts || texts.length === 0) {
    return [];
  }

  // OpenAI's node library handles batching for the embeddings endpoint internally to some extent.
  // However, be mindful of overall request size limits if sending extremely large numbers of texts or very long texts.
  // For this implementation, we'll send them in one batch, assuming typical usage.
  try {
    console.log(`Requesting embeddings for ${texts.length} text snippet(s)...`);
    const response = await openai.embeddings.create({
      model: 'text-embedding-ada-002',
      input: texts.map(text => text.replace(/\n/g, ' ')), // ADA model works best with no newlines
    });

    if (response.data && response.data.length > 0) {
      // Sort embeddings by original index to ensure order is preserved
      const sortedEmbeddings = response.data.sort((a, b) => a.index - b.index);
      console.log(`Successfully generated ${sortedEmbeddings.length} embeddings.`);
      return sortedEmbeddings.map(embeddingData => embeddingData.embedding);
    } else {
      console.error('OpenAI embeddings response is empty or malformed.');
      return texts.map(() => Array(1536).fill(0.0)); // Fallback to mock on malformed response
    }
  } catch (error: any) {
    console.error('Error calling OpenAI embeddings API:', error.message);
    if (error.response && error.response.data) {
      console.error('OpenAI Error Details:', error.response.data);
    }
    // Fallback to mock embeddings on error
    return texts.map(() => Array(1536).fill(0.0));
  }
}

const CYPHER_GENERATION_PROMPT_TEMPLATE =
  'Given the following graph schema and a natural language question, generate a Cypher query to answer the question.\n' +
  'Graph Schema:\n{graphSchema}\n\n' +
  'Natural Language Question:\n{naturalLanguageQuestion}\n\n' +
  'Return ONLY the Cypher query. Do not include any explanations, comments, or markdown formatting like ```cypher ... ```.\n' +
  'The query should be directly executable.\n\n' +
  'Cypher Query:\n';

export async function generateCypherQuery(naturalLanguageQuestion: string, graphSchema: string = "Nodes are :Entity(name). Relationships are :RELATIONSHIP(type) where 'type' stores the relation name like 'founded'. Example: (:Entity {name: 'SpaceX'})-[:RELATIONSHIP {type: 'launched'}]->(:Entity {name: 'Falcon 9'})."): Promise<string> {
  if (!openai) {
    console.warn('OpenAI client not initialized for Cypher generation. OPENAI_API_KEY might be missing.');
    return 'MATCH (n:Entity) RETURN n.name AS name, labels(n) AS labels, properties(n) AS properties LIMIT 1; // Placeholder: LLM unavailable';
  }

  const prompt = CYPHER_GENERATION_PROMPT_TEMPLATE
    .replace('{graphSchema}', graphSchema)
    .replace('{naturalLanguageQuestion}', naturalLanguageQuestion);

  try {
    console.log(`Generating Cypher query for question: "${naturalLanguageQuestion}" with schema: "${graphSchema.substring(0,50)}..."`);
    const response = await openai.chat.completions.create({
      model: 'gpt-3.5-turbo',
      messages: [
        { role: 'system', content: 'You are an expert Cypher query generator. You only return Cypher queries without any additional text or formatting.' },
        { role: 'user', content: prompt },
      ],
      temperature: 0.0,
      max_tokens: 250,
      stop: ['\n\n', ';'],
    });

    let cypherQuery = response.choices[0]?.message?.content?.trim() || '';
    console.log('LLM raw response for Cypher generation:', cypherQuery);

    if (cypherQuery.toLowerCase().startsWith('```cypher')) {
      cypherQuery = cypherQuery.substring(9);
      if (cypherQuery.endsWith('```')) {
         cypherQuery = cypherQuery.substring(0, cypherQuery.length - 3);
      }
      cypherQuery = cypherQuery.trim();
    } else if (cypherQuery.toLowerCase().startsWith('cypher')) {
      cypherQuery = cypherQuery.substring(6).trim();
    }

    if (cypherQuery.endsWith(';')) {
      cypherQuery = cypherQuery.substring(0, cypherQuery.length - 1).trim();
    }

    if (!cypherQuery) {
      console.error('LLM did not return a Cypher query.');
      return 'MATCH (n) RETURN n LIMIT 0; // Error: LLM returned empty query';
    }

    console.log('Generated Cypher query (cleaned):', cypherQuery);
    return cypherQuery;

  } catch (error: any) {
    console.error('Error calling OpenAI API for Cypher generation:', error.message);
    if (error.response && error.response.data) {
      console.error('OpenAI Error Details:', error.response.data);
    }
    return 'MATCH (n) RETURN n LIMIT 0; // Error: LLM API call failed for Cypher generation';
  }
}

const ANSWER_SYNTHESIS_PROMPT_TEMPLATE =
    'You are a helpful AI assistant. Answer the following question based *only* on the provided context.\n' +
    'If the context does not contain enough information to answer the question, state that you cannot answer based on the provided context.\n' +
    'Do not use any external knowledge or make assumptions beyond what is given in the context.\n\n' +
    'Context Items:\n---\n{context}\n---\n\n' +
    'Question: {question}\n\n' +
    'Answer:\n';

export async function* synthesizeAnswerWithContext(question: string, contextItems: string[]): AsyncIterable<string> {
  if (!openai) {
    console.warn('OpenAI client not initialized for answer synthesis. OPENAI_API_KEY might be missing.');
    yield 'I am currently unable to synthesize an answer as my language processing capabilities are offline. Please ensure the API key is configured.';
    return;
  }

  let contextString = "No specific context provided.";
  if (contextItems && contextItems.length > 0) {
     contextString = contextItems.map((item, index) => `Context Item ${index + 1}: ${item}`).join('\n\n');
  } else {
     console.log('No context items provided for answer synthesis for question: "' + question + '"');
  }

  const finalPrompt = ANSWER_SYNTHESIS_PROMPT_TEMPLATE
     .replace('{context}', contextString)
     .replace('{question}', question);

  try {
    console.log(`Requesting stream for answer synthesis for question: "${question}" with ${contextItems ? contextItems.length : 0} context items.`);
    const stream = await openai.chat.completions.create({
      model: 'gpt-3.5-turbo',
      messages: [
        { role: 'user', content: finalPrompt }
      ],
      temperature: 0.3,
      max_tokens: 350,
      stream: true, // Enable streaming
    });

    for await (const chunk of stream) {
      const contentDelta = chunk.choices[0]?.delta?.content;
      if (contentDelta) {
        yield contentDelta;
      }
      if (chunk.choices[0]?.finish_reason === 'stop') {
         // Optionally yield a special end-of-stream marker if needed by client, or just complete.
         break;
      }
    }
    console.log('Answer synthesis stream completed.');

  } catch (error: any) {
    console.error('Error calling OpenAI API for streaming answer synthesis:', error.message);
    if (error.response && error.response.data) {
      console.error('OpenAI Error Details:', error.response.data);
    }
    yield 'An error occurred while trying to synthesize an answer with the language model.';
  }
}
