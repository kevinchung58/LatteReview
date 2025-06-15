# Cognee Backend

## Development Setup

### Neo4j Database Setup

To run the backend services locally with graph database capabilities, you will need to set up a Neo4j AuraDB instance (cloud-hosted) or a local Neo4j Desktop installation.

**1. Using Neo4j AuraDB (Recommended for ease of use):**

*   Go to [Neo4j AuraDB](https://neo4j.com/cloud/aura-db/) and sign up for a free instance.
*   Once your instance is created, you will receive a connection URI (e.g., `neo4j+s://xxxxxx.databases.neo4j.io`) and credentials (username and password).
*   Create a `.env` file in the `cognee-backend` root directory by copying the `.env_sample` file.
*   Update the `.env` file with your AuraDB credentials:
    ```env
    NEO4J_URI="neo4j+s://xxxxxx.databases.neo4j.io"
    NEO4J_USERNAME="your_username"
    NEO4J_PASSWORD="your_password"
    ```

**2. Using Neo4j Desktop (Local Installation):**

*   Download and install [Neo4j Desktop](https://neo4j.com/download/).
*   Create a new project and add a local database instance.
*   Start the database. The default connection URI is usually `bolt://localhost:7687` (or `neo4j://localhost:7687`). The default username is typically `neo4j`. Set a password for this database.
*   Create a `.env` file in the `cognee-backend` root directory (if not already present).
*   Update the `.env` file with your local Neo4j credentials:
    ```env
    NEO4J_URI="bolt://localhost:7687" # Or neo4j://localhost:7687
    NEO4J_USERNAME="neo4j"
    NEO4J_PASSWORD="your_local_password"
    ```

**Important:**
*   Ensure that the Neo4j driver is correctly installed in the project (this should be part of `npm install` if `neo4j-driver` is listed in `package.json`). If not, you might need to install it: `npm install neo4j-driver`.
*   The application will use these environment variables to connect to the Neo4j database.

### Vector Database Setup (ChromaDB)

For vector embeddings and similarity search, this project uses ChromaDB.

**1. Running ChromaDB with Docker (Recommended):**

*   Ensure you have Docker installed and running on your system.
*   Pull the ChromaDB image and run the container:
    ```bash
    docker pull chromadb/chroma
    docker run -d -p 8000:8000 --name chromadb_server chromadb/chroma
    ```
*   This will start a ChromaDB server accessible at `http://localhost:8000`.
*   Update your `.env` file in the `cognee-backend` root directory with the ChromaDB server URL:
    ```env
    CHROMA_DB_URL="http://localhost:8000"
    ```

**2. Running ChromaDB as a Persistent Local Service (Alternative):**

*   You can also run ChromaDB as a persistent local service using `pip`:
    ```bash
    pip install chromadb
    chroma run --path /path/to/your/chroma_data --port 8000
    ```
    Replace `/path/to/your/chroma_data` with the actual directory where you want ChromaDB to store its data.
*   Update your `.env` file as shown above with `CHROMA_DB_URL="http://localhost:8000"`.

**Important:**
*   Ensure the `chromadb` client library is installed in the project (e.g., `npm install @langchain/community @langchain/openai chromadb`). The specific client might vary based on how it's integrated (e.g., directly or via Langchain).
*   The application will use the `CHROMA_DB_URL` environment variable to connect to the ChromaDB instance.
