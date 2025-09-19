import fs from 'fs/promises'; // Using promises version of fs
import path from 'path';
import mammoth from 'mammoth';
import pdf from 'pdf-parse'; // pdf-parse uses 'pdf.js-dist'

// Define a type for the parsed result for consistency
export interface ParsedFile {
  textContent: string;
  metadata?: Record<string, any>; // For potential future use (e.g., PDF metadata)
}

export async function parseFile(filePath: string, mimeType: string): Promise<ParsedFile> {
  try {
    const buffer = await fs.readFile(filePath);

    if (mimeType === 'application/pdf') {
      const data = await pdf(buffer);
      return {
        textContent: data.text,
        metadata: { ...data.metadata, numPages: data.numpages, info: data.info }
      };
    } else if (mimeType === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' || mimeType === 'application/msword') {
      // Handle DOCX (mammoth) and potentially older DOC if mammoth supports it or a different lib is needed
      const result = await mammoth.extractRawText({ buffer });
      return { textContent: result.value };
    } else if (mimeType === 'text/plain') {
      return { textContent: buffer.toString('utf-8') };
    } else {
      // Clean up the uploaded file if it's an unsupported type
      await fs.unlink(filePath);
      throw new Error(`Unsupported file type: ${mimeType}`);
    }
  } catch (error) {
    // Clean up the uploaded file in case of any parsing error
    try {
      await fs.unlink(filePath);
    } catch (unlinkError) {
      console.error('Error unlinking file after parsing error:', unlinkError);
    }
    console.error('Error parsing file:', error);
    throw error; // Re-throw the error to be handled by the route
  }
}
