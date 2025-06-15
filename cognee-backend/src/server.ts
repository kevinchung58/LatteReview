import './config'; // Ensures .env variables are loaded at the very beginning
import express from 'express';
import multer from 'multer';
import path from 'path';
import fs from 'fs'; // fs.promises will be used for async operations like unlink
import { parseFile, ParsedFile } from './services/parser';
import { splitText, TextSplitterOptions, splitBySentences } from './services/textSplitter';
import { extractSPO, SPOTriple, generateEmbeddings, synthesizeAnswerWithContext } from './services/llmService'; // generateEmbeddings added, synthesizeAnswerWithContext added
import { saveTriples as saveSPOsInNeo4j } from './services/neo4jService';
import { addOrUpdateChunks, getOrCreateCollection as getOrCreateVectorCollection } from './services/vectorDbService';
import { executeQueryAgainstGraph, searchVectorStore, fetchGraphData, fetchNodeNeighbors } from './services/queryOrchestrationService'; // fetchNodeNeighbors Added
import { CHROMA_COLLECTION_NAME } from './config';

const app = express();
const port = process.env.PORT || 3001;

// Ensure 'uploads/' directory exists
const uploadsDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

// Configure multer for file storage
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, uploadsDir); // Store files in an 'uploads' directory
  },
  filename: function (req, file, cb) {
    cb(null, Date.now() + '-' + file.originalname);
  }
});
const upload = multer({ storage: storage });

app.use(express.json()); // Middleware to parse JSON bodies
app.use(express.urlencoded({ extended: true })); // Middleware to parse URL-encoded bodies

app.get('/', (req, res) => {
  res.send('Cognee Backend is running!');
});

// POST endpoint for file ingestion
app.post('/ingest', upload.single('file'), async (req, res) => { // Make handler async
  if (!req.file) {
    return res.status(400).send({ message: 'No file uploaded.' });
  }
  console.log('File received:', req.file.originalname, 'Type:', req.file.mimetype);

  let tempFilePath = req.file!.path; // Use non-null assertion if file check is robust

  try {
    const parsedResult = await parseFile(tempFilePath, req.file.mimetype); // parsedResult needs to be in scope for success response
    const chunks = splitBySentences(parsedResult.textContent, 1500);
    console.log(`Parsed into ${chunks.length} chunks.`);

    const allSpos: SPOTriple[] = [];
    if (chunks.length > 0) {
      console.log('Starting SPO extraction from chunks...');
      for (let i = 0; i < chunks.length; i++) {
        console.log(`Processing chunk ${i + 1} of ${chunks.length} for SPOs...`);
        const sposFromChunk = await extractSPO(chunks[i]);
        if (sposFromChunk.length > 0) {
          allSpos.push(...sposFromChunk);
          console.log(`Extracted ${sposFromChunk.length} SPOs from chunk ${i + 1}.`);
        }
      }
      console.log(`Total SPOs extracted from all chunks: ${allSpos.length}`);

      if (allSpos.length > 0) {
        console.log('Saving extracted SPOs to Neo4j...');
        await saveSPOsInNeo4j(allSpos);
        console.log('SPOs successfully saved to Neo4j.');
      }
    }

    // Vector Embedding and Storage
    let chunkEmbeddings: number[][] = []; // Define chunkEmbeddings in a scope accessible by the response
    if (chunks.length > 0) {
      console.log('Starting vector embedding for chunks...');
      chunkEmbeddings = await generateEmbeddings(chunks); // Assign to the outer scope variable
      console.log(`Generated ${chunkEmbeddings.length} embeddings.`);

      if (chunkEmbeddings.length === chunks.length) {
        const chunkIds = chunks.map((_, idx) => `${req.file!.filename}-chunk-${idx}`);
        const chunkMetadatas = chunks.map((chunkText, idx) => ({ // chunkText is not defined here, should be chunks[idx]
          source: req.file!.originalname,
          chunkId: chunkIds[idx],
          // Storing the chunk text itself in metadata can be useful for direct access after search
          // Or, if documents in Chroma are the chunks themselves, this might be redundant here
          // Let's assume documents ARE the chunks for now.
        }));

        console.log(`Using Chroma collection: ${CHROMA_COLLECTION_NAME}`);
        await getOrCreateVectorCollection(CHROMA_COLLECTION_NAME); // Ensure collection exists
        await addOrUpdateChunks(
          CHROMA_COLLECTION_NAME,
          chunkIds,
          chunkEmbeddings,
          chunks, // Storing chunks as documents in Chroma
          chunkMetadatas
        );
        console.log('Chunks and embeddings successfully saved to ChromaDB.');
      } else {
        console.warn('Mismatch between number of chunks and generated embeddings. Skipping ChromaDB storage.');
      }
    }
    // Update success message
    // const currentMessage = res.locals.message || 'File processed successfully.'; // res.locals.message is not standard, let's build a full message
    let successMessage = 'File processed successfully.';
    if (allSpos.length > 0) successMessage += ' SPOs extracted and saved.';
    if (chunks.length > 0 && chunkEmbeddings.length === chunks.length) successMessage += ' Vector embeddings generated and stored.';


    res.status(200).send({
      message: successMessage,
      filename: req.file!.filename,
      originalName: req.file!.originalname,
      full_text_content_snippet: parsedResult.textContent.substring(0, 200) + '...', // parsedResult needs to be available
      totalChunks: chunks.length,
      totalSPOsExtracted: allSpos.length, // Assuming allSpos is still in scope
      totalEmbeddingsStored: chunks.length > 0 && chunkEmbeddings.length === chunks.length ? chunkEmbeddings.length : 0,
    });

    // Clean up the uploaded file after successful processing
    await fs.promises.unlink(tempFilePath);
    console.log('Temporary file deleted:', tempFilePath);
    tempFilePath = ''; // Clear path to prevent double deletion in catch

  } catch (error: any) {
    console.error('Error processing file in /ingest:', error.message, error.stack);
    if (tempFilePath) { // Ensure file is cleaned up on error too
      try {
        await fs.promises.unlink(tempFilePath);
        console.log('Temporary file deleted due to error:', tempFilePath);
      } catch (unlinkErr: any) {
        console.error('Error deleting temporary file during error handling:', unlinkErr.message);
      }
    }
    res.status(500).send({ message: 'Error processing file for vectorization.', error: error.message });
  }
});

app.get('/node-neighbors/:nodeId', async (req, res) => {
  const { nodeId } = req.params;
  if (!nodeId) {
    return res.status(400).json({ message: 'Node ID is required.' });
  }
  console.log(`Fetching neighbors for nodeId: ${nodeId}`);
  try {
    const graphData = await fetchNodeNeighbors(nodeId);
    res.json(graphData);
  } catch (error: any) {
    console.error(`Error fetching neighbors for nodeId ${nodeId}:`, error.message, error.stack);
    res.status(500).json({ message: 'Failed to fetch node neighbors', error: error.message });
  }
});

app.get('/graph-data', async (req, res) => {
  const searchTerm = req.query.searchTerm as string | undefined;
  console.log(`Fetching graph data with searchTerm: "${searchTerm || 'None'}"`);
  try {
    const graphData = await fetchGraphData(searchTerm);
    res.json(graphData);
  } catch (error: any) {
    console.error('Error fetching graph data:', error.message, error.stack);
    res.status(500).json({ message: 'Failed to fetch graph data', error: error.message });
  }
});

app.post('/query', async (req, res) => { // Made async
  const { question } = req.body;

  if (!question || typeof question !== 'string') {
    return res.status(400).json({ message: 'Validation error: question is required and must be a string.' });
  }

  console.log(`Received query for SSE: ${question}`);

  // Flag to track if headers have been sent
  let headersSent = false;

  try {
    console.log(`Processing query: "${question}"`);

    // Step 1 & 2: Fetch context from Knowledge Graph and Vector Store concurrently
    console.log('Fetching context from knowledge graph...');
    const graphContextPromise = executeQueryAgainstGraph(question);

    console.log('Fetching context from vector store...');
    const vectorContextPromise = searchVectorStore(question, CHROMA_COLLECTION_NAME);

    const [graphContextItems, vectorContextItems] = await Promise.all([graphContextPromise, vectorContextPromise]);

    console.log('Graph context items (first few):', graphContextItems.slice(0,2));
    console.log('Vector context items (first few):', vectorContextItems.slice(0,2));

    // Step 3: Combine contexts
    const combinedContext = [...graphContextItems, ...vectorContextItems].filter(item => item && !item.toLowerCase().includes('no results found'));
    console.log('Combined context for synthesis (item count):', combinedContext.length);

    // Step 4: Set SSE headers and start streaming the answer
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.flushHeaders();
    headersSent = true;

    // Send context items first (optional, for debugging on client)
    // res.write(`data: ${JSON.stringify({ type: 'context', graphContext: graphContextItems, vectorContext: vectorContextItems })}\n\n`);

    console.log('Synthesizing and streaming answer with LLM...');
    const answerStream = synthesizeAnswerWithContext(question, combinedContext);

    for await (const token of answerStream) {
      res.write(`data: ${JSON.stringify({ token })}\n\n`);
    }
    console.log('Answer stream finished.');
    res.end();

  } catch (error: any) {
    console.error(`Error processing query "${question}":`, error.message, error.stack);
    if (!headersSent) {
      // If headers haven't been sent, we can send a normal error response
      res.status(500).json({
        message: 'Error processing your query before streaming.',
        error: error.message,
      });
    } else {
      // If headers were already sent, we can only end the stream, possibly after writing an error event if desired
      // Example: res.write(`data: ${JSON.stringify({ error: "Streaming error: " + error.message })}\n\n`);
      console.error('Error occurred after SSE headers were sent. Stream will be closed.');
      res.end(); // Ensure the stream is closed
    }
  }
});

app.listen(port, () => {
  console.log(`Backend server listening on port ${port}`);
});
