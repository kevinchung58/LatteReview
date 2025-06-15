# Cognee - Full Stack RAG Application

This project is a full-stack Retrieval Augmented Generation (RAG) application. It consists of a React frontend, a Node.js (TypeScript/Express) backend, and utilizes Neo4j and ChromaDB for data storage and retrieval.

## Project Structure

-   `/cognee-frontend`: Contains the React frontend application built with Vite.
-   `/cognee-backend`: Contains the Node.js backend API built with Express and TypeScript.

## Running the Application with Docker Compose

This is the recommended way to run the entire application stack locally for development or testing.

### Prerequisites

-   Docker: [Install Docker](https://docs.docker.com/get-docker/)
-   Docker Compose: Usually included with Docker Desktop. If not, [install Docker Compose](https://docs.docker.com/compose/install/).

### Environment Setup

1.  **Backend Configuration (`.env` for `cognee-backend`):**
    *   Navigate to the `cognee-backend` directory.
    *   Copy the example environment file: `cp .env.example .env`
    *   Open the newly created `.env` file and **update the following variables**:
        *   `OPENAI_API_KEY`: **Crucial for LLM functionalities.** Set this to your actual OpenAI API key.
        *   `NEO4J_PASSWORD`: The password for the Neo4j database. The default is `yourStrongPassword`.
            *   **IMPORTANT:** If you change `yourStrongPassword` here, you **must** also change it in the `NEO4J_AUTH` environment variable for the `neo4j` service in the main `docker-compose.yml` file (e.g., `NEO4J_AUTH=neo4j/yourNewPassword`).
    *   Other variables like `NEO4J_URI`, `CHROMA_URL`, `CHROMA_COLLECTION_NAME`, and `PORT` are pre-configured in `.env.example` to work with the Docker Compose service names.

2.  **Frontend Configuration (`.env` for `cognee-frontend` - Optional for Docker):**
    *   The `VITE_API_BASE_URL` for the frontend is set at build time by Docker Compose to `http://backend:3001`.
    *   If you were running the frontend locally *outside* of Docker (e.g., with `npm run dev` directly from `cognee-frontend`), you would create a `.env` file in `cognee-frontend` (by copying `cognee-frontend/.env.example` if it existed, or just creating it) and ensure `VITE_API_BASE_URL=http://localhost:3001` is set. For Docker Compose, this is handled by the build arguments.

### Build and Run

1.  From the project root directory (where `docker-compose.yml` is located), run:
    ```bash
    docker-compose up --build -d
    ```
    *   `--build`: This flag tells Docker Compose to build the images for the `backend` and `frontend` services if they don't exist locally or if their respective `Dockerfile` or build context has changed.
    *   `-d`: This flag runs the containers in detached mode, meaning they run in the background.

### Accessing Services

Once the containers are up and running:

-   **Frontend Application:** Open your browser and go to `http://localhost:8080`
-   **Backend API:** Accessible at `http://localhost:3001` (This is what the frontend will connect to. You can also use tools like Postman or curl to test API endpoints directly.)
-   **Neo4j Browser:** Open your browser and go to `http://localhost:7474`
    -   Connect using the URI `bolt://localhost:7687` (or the one specified in `cognee-backend/.env` if you changed it for local non-Docker Neo4j).
    -   Login with username `neo4j` and the password you set (default `yourStrongPassword` as per `NEO4J_AUTH` in `docker-compose.yml` and `NEO4J_PASSWORD` in `cognee-backend/.env`).
-   **ChromaDB API:** Accessible at `http://localhost:8000` (Primarily for backend use or direct inspection if needed).

### Stopping the Application

1.  To stop all running services defined in the `docker-compose.yml`, navigate to the project root directory and run:
    ```bash
    docker-compose down
    ```
    This will stop and remove the containers.

### Data Persistence

-   Neo4j data is persisted in a Docker volume named `neo4j_data`.
-   ChromaDB data is persisted in a Docker volume named `chroma_data`.
-   This means your graph data and vector embeddings will survive if you stop and restart the application using `docker-compose down` and `docker-compose up`.
-   To remove the data completely, you would need to explicitly remove the Docker volumes (e.g., `docker volume rm neo4j_data chroma_data`).

---
*(Other sections of a typical README like "Project Setup for Local Development (without Docker)", "Features", "API Documentation", "Contributing", etc., can be added here later.)*
