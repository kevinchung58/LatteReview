import express from 'express';
import multer from 'multer';
import path from 'path';
import fs from 'fs'; // fs.promises will be used for async operations like unlink
import { parseFile, ParsedFile } from './services/parser';
import { splitText, TextSplitterOptions, splitBySentences } from './services/textSplitter'; // Import the new service

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

  try {
    const parsedResult: ParsedFile = await parseFile(req.file.path, req.file.mimetype);

    // Define options for the text splitter
    // const simpleSplitOptions: TextSplitterOptions = { chunkSize: 1000, chunkOverlap: 100 };
    // const chunks = splitText(parsedResult.textContent, simpleSplitOptions);

    // Or using sentence splitter
    const chunks = splitBySentences(parsedResult.textContent, 1500); // Target 1500 chars per chunk

    console.log(`Original text length: ${parsedResult.textContent.length}, Number of chunks: ${chunks.length}`);

    res.status(200).send({
      message: 'File parsed and chunked successfully.',
      original_filename: req.file.filename, // filename on server (multer generated)
      originalName: req.file.originalname, // original filename from user
      full_text_content: parsedResult.textContent, // Full parsed text
      totalChunks: chunks.length,
      chunks: chunks // All chunks
    });

    // Clean up the uploaded file after processing
    try {
      await fs.promises.unlink(req.file.path);
      console.log('Temporary file deleted:', req.file.path);
    } catch (unlinkError) {
      console.error('Error deleting temporary file:', unlinkError);
    }

  } catch (error: any) {
    console.error('Error processing file in /ingest:', error);
    // parseFile should handle deleting the file on its own error, but if error happens after parseFile, ensure cleanup
    if (req.file && req.file.path) {
        try { await fs.promises.unlink(req.file.path); } catch (e) { /* ignore */ }
    }
    res.status(500).send({ message: 'Error processing file.', error: error.message });
  }
});

app.listen(port, () => {
  console.log(`Backend server listening on port ${port}`);
});
