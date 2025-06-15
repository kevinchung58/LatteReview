import './config'; // Ensures .env variables are loaded at the very beginning
import express from 'express';
import multer from 'multer';
import path from 'path';
import fs from 'fs'; // fs.promises will be used for async operations like unlink
import { parseFile, ParsedFile } from './services/parser';
import { splitText, TextSplitterOptions, splitBySentences } from './services/textSplitter';
import { extractSPO, SPOTriple } from './services/llmService';
import { saveTriples as saveSPOsInNeo4j } from './services/neo4jService';

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

  let tempFilePath = req.file.path;

  try {
    const parsedResult = await parseFile(tempFilePath, req.file.mimetype);
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

    res.status(200).send({
      message: 'File processed, SPOs extracted and saved successfully.',
      filename: req.file.filename, // filename on server (multer generated) - user wants this as 'filename' not 'original_filename' per snippet
      originalName: req.file.originalname, // original filename from user
      full_text_content_snippet: parsedResult.textContent.substring(0, 200) + '...',
      totalChunks: chunks.length,
      totalSPOsExtracted: allSpos.length,
      // chunks: chunks, // Optionally return all chunks
      // spos: allSpos    // Optionally return all SPOs
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
    res.status(500).send({ message: 'Error processing file.', error: error.message });
  }
});

app.listen(port, () => {
  console.log(`Backend server listening on port ${port}`);
});
