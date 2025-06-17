import { GEMINI_API_KEY, OPENAI_API_KEY } from '../config'; // Added GEMINI_API_KEY
import {
  ChatGoogleGenerativeAI,
  GoogleGenerativeAIEmbeddings,
} from '@langchain/google-genai';
import {
  HumanMessage,
  SystemMessage,
  BaseMessage,
} from '@langchain/core/messages';
import { StringOutputParser } from '@langchain/core/output_parsers';
import { ChatPromptTemplate } from '@langchain/core/prompts';

// Define the structure for SPO triples - remains the same
export interface SPOTriple {
  subject: string;
  relation: string;
  object: string;
}

let langchainGeminiChatModel: ChatGoogleGenerativeAI | undefined;
let langchainGeminiEmbeddings: GoogleGenerativeAIEmbeddings | undefined;

if (GEMINI_API_KEY) {
  langchainGeminiChatModel = new ChatGoogleGenerativeAI({
    apiKey: GEMINI_API_KEY,
    modelName: 'gemini-2.0-flash', // Corrected model name as per user request
    temperature: 0.3, // Default temperature, can be overridden
  });
  langchainGeminiEmbeddings = new GoogleGenerativeAIEmbeddings({
    apiKey: GEMINI_API_KEY,
    modelName: 'text-embedding-004', // Or other appropriate Gemini embedding model
  });
  console.log('LangChain Gemini models initialized using GEMINI_API_KEY.');
} else if (OPENAI_API_KEY) {
  // Fallback or secondary LLM - for now, we focus on Gemini as primary
  // This section could initialize OpenAI models if needed as a fallback
  // For this refactor, we assume Gemini is the primary and will warn if not available.
  console.warn(
    'GEMINI_API_KEY is not set. OPENAI_API_KEY is available but this service is being refactored for Gemini first.'
  );
  // To maintain some functionality if only OpenAI is available, you could init OpenAI Langchain wrappers here.
  // For now, the functions below will primarily check for langchainGeminiChatModel.
} else {
  console.warn(
    'Neither GEMINI_API_KEY nor OPENAI_API_KEY is set. LLM service will use mocked responses or be non-functional.'
  );
}

const DEFAULT_SPO_EXTRACTION_PROMPT_TEMPLATE =
  `Extract all entities and their relationships from the following text as Subject-Predicate-Object (SPO) triples. ` +
  `Return the result as a valid JSON array of objects, where each object has the keys "subject", "relation", and "object". ` +
  `The JSON array should be the only content in your response. Do not include any other text or explanations. ` +
  `If no meaningful SPO triples can be extracted, return an empty array: [].

` +
  `Example:
` +
  `Text: 'Elon Musk founded SpaceX. SpaceX launched Falcon 9.'
` +
  `Output: [
` +
  `  { "subject": "Elon Musk", "relation": "founded", "object": "SpaceX" },
` +
  `  { "subject": "SpaceX", "relation": "launched", "object": "Falcon 9" }
` +
  `]

` +
  `Text to process:
` +
  `'{text_chunk}'

` +
  `JSON Output:
`;

export async function extractSPO(textChunk: string, promptTemplate?: string): Promise<SPOTriple[]> {
  if (!langchainGeminiChatModel) {
    console.log('Langchain Gemini Chat client not initialized. Returning mock SPO data for chunk: "' + textChunk.substring(0,30) + '..."');
    // Mock data logic (can be expanded or made more sophisticated)
    if (textChunk.toLowerCase().includes('elon musk')) {
      return [
        { subject: 'Elon Musk', relation: 'founded', object: 'SpaceX (mocked)' },
        { subject: 'SpaceX (mocked)', relation: 'launched', object: 'Falcon 9 (mocked)' },
      ];
    }
    return [];
  }

  const currentPromptContent = (promptTemplate || DEFAULT_SPO_EXTRACTION_PROMPT_TEMPLATE).replace('{text_chunk}', textChunk);

  const messages: BaseMessage[] = [
    new SystemMessage('You are an expert in knowledge graph extraction. Your response must be only a valid JSON array of SPO triples. If no triples are found, return an empty array []. Do not include markdown code blocks or any other explanatory text.'),
    new HumanMessage(currentPromptContent),
  ];

  try {
    console.log(`Sending request to Gemini for SPO extraction from chunk: "${textChunk.substring(0, 50)}..."`);
    // Using .invoke() for a single response
    const response = await langchainGeminiChatModel.invoke(messages);
    const content = response.content;

    if (typeof content !== 'string' || !content.trim()) {
      console.error('Gemini response content is empty or not a string.');
      return [];
    }
    console.log('Gemini raw response for SPO:', content);

    let jsonResponseString = content.trim();
    // Gemini might sometimes wrap in ```json ... ```, attempt to strip it.
    if (jsonResponseString.startsWith('```json')) {
      jsonResponseString = jsonResponseString.substring(7);
      if (jsonResponseString.endsWith('```')) {
        jsonResponseString = jsonResponseString.substring(0, jsonResponseString.length - 3);
      }
      jsonResponseString = jsonResponseString.trim();
    }

    // Ensure it's actually an array string before parsing
    if (!jsonResponseString.startsWith('[') || !jsonResponseString.endsWith(']')) {
        console.error('Gemini response for SPO was not a JSON array string after trimming potential markdown:', jsonResponseString);
        // Attempt to find array within potentially extraneous text (last resort)
        const startIndex = jsonResponseString.indexOf('[');
        const endIndex = jsonResponseString.lastIndexOf(']');
        if (startIndex !== -1 && endIndex !== -1 && endIndex > startIndex) {
            jsonResponseString = jsonResponseString.substring(startIndex, endIndex + 1);
        } else {
            console.error('Could not reliably extract JSON array from response.');
            return [];
        }
    }


    const parsedTriples = JSON.parse(jsonResponseString);
    if (Array.isArray(parsedTriples) && (parsedTriples.length === 0 || parsedTriples.every(t => typeof t === 'object' && t !== null && 'subject' in t && 'relation' in t && 'object' in t))) {
      console.log(`Extracted ${parsedTriples.length} SPO triples.`);
      return parsedTriples as SPOTriple[];
    } else {
      console.error('Gemini response was not a valid array of SPO triples or had incorrect structure:', parsedTriples);
      return [];
    }

  } catch (error: any) {
    console.error('Error calling Gemini API or parsing response for SPO extraction:', error.message, error.stack);
    return [];
  }
}

export async function generateEmbeddings(texts: string[]): Promise<number[][]> {
  if (!langchainGeminiEmbeddings) {
    console.warn('Langchain Gemini Embeddings client not initialized. GEMINI_API_KEY might be missing. Returning mock embeddings.');
    return texts.map(() => Array(768).fill(0.0)); // Gemini embedding dimensions might differ, e.g., 768 for text-embedding-004
  }

  if (!texts || texts.length === 0) {
    return [];
  }

  try {
    console.log(`Requesting Gemini embeddings for ${texts.length} text snippet(s)...`);
    // embedDocuments is for multiple texts
    const embeddings = await langchainGeminiEmbeddings.embedDocuments(texts.map(text => text.replace(/
/g, ' ')));

    if (embeddings && embeddings.length === texts.length) {
      console.log(`Successfully generated ${embeddings.length} Gemini embeddings.`);
      return embeddings;
    } else {
      console.error('Gemini embeddings response is empty, malformed, or length mismatch.');
      return texts.map(() => Array(768).fill(0.0)); // Fallback
    }
  } catch (error: any) {
    console.error('Error calling Gemini embeddings API via Langchain:', error.message, error.stack);
    return texts.map(() => Array(768).fill(0.0)); // Fallback
  }
}

const CYPHER_GENERATION_PROMPT_TEMPLATE_STRING = // Renamed to avoid conflict
  'Given the following graph schema and a natural language question, generate a Cypher query to answer the question.
' +
  'Graph Schema:
{graphSchema}

' +
  'Natural Language Question:
{naturalLanguageQuestion}

' +
  'Return ONLY the Cypher query. Do not include any explanations, comments, or markdown formatting like ```cypher ... ``` or ``` ... ```.
' +
  'The query should be directly executable. Do not include a semicolon at the end of the query.

' +
  'Cypher Query:';

export async function generateCypherQuery(naturalLanguageQuestion: string, graphSchema: string = "Nodes are :Entity(name). Relationships are :RELATIONSHIP(type) where 'type' stores the relation name like 'founded'. Example: (:Entity {name: 'SpaceX'})-[:RELATIONSHIP {type: 'launched'}]->(:Entity {name: 'Falcon 9'})."): Promise<string> {
  if (!langchainGeminiChatModel) {
    console.warn('Langchain Gemini Chat client not initialized for Cypher generation. GEMINI_API_KEY might be missing.');
    return 'MATCH (n:Entity) RETURN n.name AS name, labels(n) AS labels, properties(n) AS properties LIMIT 1; // Placeholder: LLM unavailable';
  }

  const prompt = ChatPromptTemplate.fromMessages([
    new SystemMessage('You are an expert Cypher query generator. You only return Cypher queries without any additional text, formatting, or semicolons.'),
    new HumanMessage(CYPHER_GENERATION_PROMPT_TEMPLATE_STRING),
  ]);

  const chain = prompt.pipe(langchainGeminiChatModel).pipe(new StringOutputParser());

  try {
    console.log(`Generating Cypher query with Gemini for question: "${naturalLanguageQuestion}" with schema: "${graphSchema.substring(0,50)}..."`);
    const response = await chain.invoke({
      graphSchema: graphSchema,
      naturalLanguageQuestion: naturalLanguageQuestion,
    });

    let cypherQuery = response.trim();
    console.log('Gemini raw response for Cypher generation:', cypherQuery);

    // Clean common markdown/formatting issues
    if (cypherQuery.toLowerCase().startsWith('```cypher')) {
      cypherQuery = cypherQuery.substring(9);
      if (cypherQuery.endsWith('```')) {
         cypherQuery = cypherQuery.substring(0, cypherQuery.length - 3);
      }
      cypherQuery = cypherQuery.trim();
    } else if (cypherQuery.toLowerCase().startsWith('cypher')) {
      cypherQuery = cypherQuery.substring(6).trim();
    } else if (cypherQuery.startsWith('```')) {
      cypherQuery = cypherQuery.substring(3);
      if (cypherQuery.endsWith('```')) {
         cypherQuery = cypherQuery.substring(0, cypherQuery.length - 3);
      }
      cypherQuery = cypherQuery.trim();
    }


    if (cypherQuery.endsWith(';')) {
      cypherQuery = cypherQuery.substring(0, cypherQuery.length - 1).trim();
    }

    if (!cypherQuery) {
      console.error('Gemini did not return a Cypher query.');
      return 'MATCH (n) RETURN n LIMIT 0; // Error: LLM returned empty query';
    }

    console.log('Generated Cypher query (cleaned):', cypherQuery);
    return cypherQuery;

  } catch (error: any) {
    console.error('Error calling Gemini API for Cypher generation via Langchain:', error.message, error.stack);
    return 'MATCH (n) RETURN n LIMIT 0; // Error: LLM API call failed for Cypher generation';
  }
}

const ANSWER_SYNTHESIS_PROMPT_TEMPLATE_STRING = // Renamed
    'You are a helpful AI assistant. Answer the following question based *only* on the provided context.
' +
    'If the context does not contain enough information to answer the question, state that you cannot answer based on the provided context.
' +
    'Do not use any external knowledge or make assumptions beyond what is given in the context.

' +
    'Context Items:
---
{context}
---

' +
    'Question: {question}

' +
    'Answer:
';

export async function* synthesizeAnswerWithContext(question: string, contextItems: string[]): AsyncIterable<string> {
  if (!langchainGeminiChatModel) {
    console.warn('Langchain Gemini Chat client not initialized for answer synthesis. GEMINI_API_KEY might be missing.');
    yield 'I am currently unable to synthesize an answer as my language processing capabilities are offline. Please ensure the API key is configured.';
    return;
  }

  let contextString = "No specific context provided.";
  if (contextItems && contextItems.length > 0) {
     contextString = contextItems.map((item, index) => `Context Item ${index + 1}: ${item}`).join('

');
  } else {
     console.log('No context items provided for answer synthesis for question: "' + question + '"');
  }

  const prompt = ChatPromptTemplate.fromMessages([
      new HumanMessage(ANSWER_SYNTHESIS_PROMPT_TEMPLATE_STRING)
  ]);
  const chain = prompt.pipe(langchainGeminiChatModel).pipe(new StringOutputParser());

  try {
    console.log(`Requesting stream from Gemini for answer synthesis for question: "${question}" with ${contextItems ? contextItems.length : 0} context items.`);
    const stream = await chain.stream({
        context: contextString,
        question: question,
    });

    for await (const token of stream) {
      if (typeof token === 'string') {
        yield token;
      }
    }
    console.log('Gemini answer synthesis stream completed.');

  } catch (error: any) {
    console.error('Error calling Gemini API for streaming answer synthesis via Langchain:', error.message, error.stack);
    yield 'An error occurred while trying to synthesize an answer with the language model.';
  }
}
