# Cognee Backend (LangChain Integrated)

This backend service provides the core functionalities for the Cognee application, focusing on data ingestion, processing, querying, and knowledge graph construction using Large Language Models (LLMs) via the LangChain.js library. The primary LLM used is Google's Gemini (gemini-2.0-flash for chat, text-embedding-004 for embeddings).

## Features

-   **File Ingestion**: Upload PDF, DOCX, and TXT files via the `/ingest` endpoint.
-   **Data Processing**: Files are processed into text, split into manageable chunks.
-   **Vector Storage**: Processed documents are embedded using Gemini and stored in ChromaDB for semantic search.
-   **Knowledge Graph Construction**: Optionally, entities and relationships can be extracted from documents using Gemini and stored in Neo4j to build a knowledge graph.
-   **Querying**:
    -   Perform Retrieval Augmented Generation (RAG) against the vector store via the `/query` endpoint.
    -   Supports conversational context (chat history).
    -   Optionally augment RAG with context retrieved from the knowledge graph.
    -   Stream responses using Server-Sent Events (SSE).
    -   Query the knowledge graph directly using natural language via the `/query-graph` endpoint.
-   **Graph Schema**: Retrieve the Neo4j graph schema via the `/graph-schema` endpoint.

## Architecture

The backend is built with Node.js, Express, and TypeScript. It leverages a modular **Cognitive Toolkit** built with LangChain.js for core LLM-related operations.

### Cognitive Toolkit (`./src/toolkit/`)

-   **`data-processor.ts`**: Handles loading documents from various file types (PDF, DOCX, TXT) and splitting them into processable chunks using LangChain document loaders and text splitters.
-   **`vector-store.ts`**: Manages interactions with the ChromaDB vector store. It uses Gemini embeddings to store and retrieve documents. Provides functions to add documents and create retrievers.
-   **`query-engine.ts`**: Contains the logic for creating RAG (Retrieval Augmented Generation) chains using LangChain. It sets up `RetrievalQAChain` and `ConversationalRetrievalQAChain` with the Gemini chat model and a vector store retriever.
-   **`graph-builder.ts`**: Manages interactions with the Neo4j graph database. It includes functionalities to:
    -   Extract graph elements (nodes, relationships) from documents using the Gemini LLM.
    -   Add these elements to Neo4j.
    -   Convert natural language questions into Cypher queries using the Gemini LLM for graph Q&A.
    -   Fetch the graph schema.

## Setup

1.  **Prerequisites**:
    *   Node.js (e.g., v18+ or v20+)
    *   NPM
    *   Docker (for running ChromaDB and Neo4j, or use cloud/managed instances)

2.  **Clone the repository** (if applicable)

3.  **Navigate to `cognee-backend`**:
    \`\`\`bash
    cd cognee-backend
    \`\`\`

4.  **Install dependencies**:
    \`\`\`bash
    npm install
    \`\`\`

5.  **Set up Environment Variables**:
    Create a `.env` file in the `cognee-backend` directory by copying `.env.example` (if it exists) or creating a new one.
    Populate it with the following:
    \`\`\`dotenv
    # LLM Configuration
    GEMINI_API_KEY="your-google-gemini-api-key" # Primary LLM and Embeddings
    # OPENAI_API_KEY="sk-..." # Optional, if OpenAI models were to be used as fallback

    # Neo4j Configuration
    NEO4J_URI="bolt://localhost:7687" # Or your Neo4j AuraDB URI (e.g., neo4j+s://xxxx.databases.neo4j.io)
    NEO4J_USERNAME="neo4j"
    NEO4J_PASSWORD="your-neo4j-password"

    # ChromaDB Configuration
    CHROMA_URL="http://localhost:8000" # URL of your ChromaDB instance
    CHROMA_COLLECTION_NAME="cognee_main_collection" # Default collection name

    # Server Configuration
    PORT=3001
    \`\`\`
    Replace placeholders with your actual credentials and URLs.

6.  **Run ChromaDB and Neo4j**:
    Ensure instances of ChromaDB and Neo4j are running and accessible based on your `.env` configuration. You can use Docker for local setup:
    *   **ChromaDB**: `docker pull chromadb/chroma && docker run -p 8000:8000 chromadb/chroma`
    *   **Neo4j**: Refer to Neo4j Docker documentation for setup (e.g., `docker run --rm -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/your-password neo4j:latest`)

## Running the Application

-   **Development mode (with auto-reloading)**:
    \`\`\`bash
    npm run dev
    \`\`\`
-   **Production mode (build first)**:
    \`\`\`bash
    npm run build
    node dist/server.js # Or your specific build output path
    \`\`\`

The server will typically start on `http://localhost:3001`.

## API Endpoints

-   **`POST /ingest`**: Upload a file for processing.
    -   Form Data: `file` (the file to upload)
    -   Query Parameters:
        -   `collectionName` (string, optional): ChromaDB collection name. Defaults to `cognee_main_collection`.
        -   `buildGraph` (string, optional, 'true' or 'false'): Whether to extract and store graph data in Neo4j. Defaults to `true`.
-   **`POST /query`**: Ask a question.
    -   JSON Body:
        \`\`\`json
        {
          "question": "Your question here",
          "collectionName": "optional_chroma_collection_name",
          "chat_history": [
            { "type": "human", "content": "Previous human message" },
            { "type": "ai", "content": "Previous AI message" }
          ],
          "use_knowledge_graph": false // boolean, true to augment with graph context
        }
        \`\`\`
    -   Response: Server-Sent Events (SSE) stream with tokens, source documents, etc.
-   **`GET /graph-schema`**: Get the summary of the Neo4j graph schema.
-   **`POST /query-graph`**: Query the knowledge graph directly with a natural language question.
    -   JSON Body:
        \`\`\`json
        {
          "question": "Your natural language question for the graph"
        }
        \`\`\`

## Testing

Unit tests for the toolkit modules are located in `src/toolkit/__tests__`. Run tests using:
\`\`\`bash
npm test
\`\`\`
(Requires Jest and `ts-jest` setup, which should be in `package.json`)
