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
