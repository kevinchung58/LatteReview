import dotenv from 'dotenv';
import path from 'path';

// Load .env file from the root of cognee-backend
dotenv.config({ path: path.resolve(__dirname, '../../.env') });

export const NEO4J_URI = process.env.NEO4J_URI || 'neo4j://localhost:7687';
export const NEO4J_USER = process.env.NEO4J_USER || 'neo4j';
export const NEO4J_PASSWORD = process.env.NEO4J_PASSWORD || 'password';
export const OPENAI_API_KEY = process.env.OPENAI_API_KEY || '';

if (!OPENAI_API_KEY && process.env.NODE_ENV !== 'test') {
  // In test environment, we might mock the OpenAI API, so key might not be needed
  // console.warn('Warning: OPENAI_API_KEY is not set. LLM functionalities will be disabled or mocked.');
}
