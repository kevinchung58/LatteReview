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
