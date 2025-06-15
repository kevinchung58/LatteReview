export interface TextSplitterOptions {
  chunkSize: number; // Target size of each chunk
  chunkOverlap?: number; // Optional overlap between chunks
}

// Basic splitter by character count with overlap
export function splitText(text: string, options: TextSplitterOptions): string[] {
  const { chunkSize, chunkOverlap = 0 } = options;
  if (chunkOverlap >= chunkSize) {
    throw new Error('Chunk overlap cannot be greater than or equal to chunk size.');
  }

  const chunks: string[] = [];
  let i = 0;
  while (i < text.length) {
    const end = Math.min(i + chunkSize, text.length);
    chunks.push(text.substring(i, end));
    i += (chunkSize - chunkOverlap);
    if (i >= text.length && end < text.length) { // Ensure last part is captured if loop condition makes i jump over
         // This condition might need refinement depending on desired behavior for the very last chunk with overlap
    }
  }
  // A simple way to ensure the last chunk is always included up to text.length
  // This might result in a final chunk smaller than chunkSize if there's no overlap or specific handling
  // For a more robust solution, RecursiveCharacterTextSplitter logic from langchain is a good reference.
  return chunks.filter(chunk => chunk.trim() !== ''); // Remove empty chunks
}

// Example of a sentence splitter (very basic)
export function splitBySentences(text: string, maxCharsPerChunk: number = 1000): string[] {
    const sentences = text.match(/[^.!?]+[.!?]+(\s|$)/g) || [];
    if (sentences.length === 0 && text.trim().length > 0) { // Handle case with no sentence terminators
        return [text];
    }

    const chunks: string[] = [];
    let currentChunk = "";
    for (const sentence of sentences) {
        if ((currentChunk + sentence).length > maxCharsPerChunk && currentChunk.length > 0) {
            chunks.push(currentChunk.trim());
            currentChunk = "";
        }
        currentChunk += sentence;
    }
    if (currentChunk.trim().length > 0) {
        chunks.push(currentChunk.trim());
    }
    return chunks;
}
