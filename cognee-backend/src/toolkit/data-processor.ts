import { Document } from '@langchain/core/documents';
import { RecursiveCharacterTextSplitter } from 'langchain/text_splitter'; // Or from '@langchain/textsplitters' if this path is wrong
import { PDFLoader } from '@langchain/community/document_loaders/fs/pdf';
import { TextLoader } from '@langchain/community/document_loaders/fs/text';
import { DocxLoader } from '@langchain/community/document_loaders/fs/docx';
import * as fs from 'fs/promises'; // For checking file existence, etc.
import *
as path from 'path';

export type SupportedFileMimeTypes =
  | 'application/pdf'
  | 'text/plain'
  | 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'; // for .docx

export type SupportedFileExtensions = '.pdf' | '.txt' | '.docx';


export async function processFileToDocuments(
  filePath: string,
  mimeType: SupportedFileMimeTypes | string // Allow string for broader compatibility initially
): Promise<Document[]> {
  console.log(`Processing file: ${filePath} with mimeType: ${mimeType}`);

  let loader: PDFLoader | TextLoader | DocxLoader;

  // Determine loader based on mimeType or fall back to extension
  const fileExtension = path.extname(filePath).toLowerCase() as SupportedFileExtensions;

  if (mimeType === 'application/pdf' || (!mimeType && fileExtension === '.pdf')) {
    console.log('Using PDFLoader');
    loader = new PDFLoader(filePath);
  } else if (mimeType === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' || (!mimeType && fileExtension === '.docx')) {
    console.log('Using DocxLoader');
    loader = new DocxLoader(filePath);
  } else if (mimeType === 'text/plain' || (!mimeType && fileExtension === '.txt')) {
    console.log('Using TextLoader');
    loader = new TextLoader(filePath);
  } else {
    console.error(`Unsupported mimeType or file extension: ${mimeType} / ${fileExtension} for file ${filePath}`);
    // Optionally, could try a generic loader or throw a more specific error
    // For now, try TextLoader as a last resort if extension is unknown but seems text-based
    if (fileExtension === '.txt' || !fileExtension) { // if extension is unknown but it's a text based mime
        console.warn(`Attempting TextLoader as a fallback for ${filePath}`);
        loader = new TextLoader(filePath);
    } else {
        throw new Error(`Unsupported file type: ${mimeType} or extension: ${fileExtension}`);
    }
  }

  try {
    const rawDocs = await loader.load();
    console.log(`Loaded ${rawDocs.length} raw documents from file.`);

    if (rawDocs.length === 0) {
      console.warn('No documents were loaded from the file.');
      return [];
    }

    const splitter = new RecursiveCharacterTextSplitter({
      chunkSize: 1000, // As per user's example
      chunkOverlap: 200, // As per user's example
      // addStartIndex: true, // Optional: adds chunk's start index in original doc to metadata
    });

    const splittedDocs = await splitter.splitDocuments(rawDocs);
    console.log(`Split into ${splittedDocs.length} documents/chunks.`);

    // Add source metadata to each document
    return splittedDocs.map(doc => ({
      ...doc,
      metadata: {
        ...doc.metadata,
        source: path.basename(filePath), // Add filename as source
        filePath: filePath, // Add full path as well
      }
    }));

  } catch (error: any) {
    console.error(`Error processing file ${filePath}:`, error.message, error.stack);
    throw new Error(`Failed to process file ${filePath}: ${error.message}`);
  }
}

// Example of a more generic function if input type is not strictly file path (e.g. raw text, URL)
// This matches the user's original idea of `processRawData` more closely, but the primary
// request was for `processFileToDocuments`. This can be added later if needed.
/*
export async function processGenericInputToDocuments(
  input: string,
  inputType: 'filePath' | 'url' | 'rawText',
  mimeType?: SupportedFileMimeTypes | string // MimeType relevant for filePath or URL content type
): Promise<Document[]> {
  if (inputType === 'rawText') {
    const splitter = new RecursiveCharacterTextSplitter({ chunkSize: 1000, chunkOverlap: 200 });
    const docs = await splitter.createDocuments([input]);
    return docs.map(doc => ({ ...doc, metadata: { ...doc.metadata, source: 'rawText' }}));
  } else if (inputType === 'filePath') {
    if (!mimeType) throw new Error('mimeType is required for filePath processing in processGenericInputToDocuments');
    return processFileToDocuments(input, mimeType);
  } else if (inputType === 'url') {
    // Here you would use a URL loader, e.g., CheerioWebBaseLoader or PuppeteerWebBaseLoader
    // from '@langchain/community/document_loaders/web/cheerio' or similar
    // For now, this is a placeholder
    console.warn('URL processing is not fully implemented yet in processGenericInputToDocuments.');
    // Example:
    // const loader = new CheerioWebBaseLoader(input);
    // const rawDocs = await loader.load();
    // const splitter = new RecursiveCharacterTextSplitter({ chunkSize: 1000, chunkOverlap: 200 });
    // const splittedDocs = await splitter.splitDocuments(rawDocs);
    // return splittedDocs.map(doc => ({ ...doc, metadata: { ...doc.metadata, source: input }}));
    return [];
  }
  throw new Error('Unsupported inputType for processGenericInputToDocuments');
}
*/

console.log('data-processor.ts loaded');
