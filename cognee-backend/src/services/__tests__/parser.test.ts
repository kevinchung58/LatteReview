import path from 'path';
import fs from 'fs/promises';
import { parseFile, ParsedFile } from '../parser';

const samplesDir = path.join(__dirname, 'sample_files');
const tempTestDir = path.join(__dirname, 'temp_test_files');

beforeAll(async () => {
  await fs.mkdir(tempTestDir, { recursive: true });
});

afterAll(async () => {
  await fs.rm(tempTestDir, { recursive: true, force: true });
});

describe('File Parser Service', () => {
  it('should parse a .txt file', async () => {
    const testFilePath = path.join(tempTestDir, 'test.txt');
    const sampleText = 'Hello text world. This is a test.';
    await fs.writeFile(testFilePath, sampleText);
    const result = await parseFile(testFilePath, 'text/plain');
    expect(result.textContent).toBe(sampleText);
  });

  it('should attempt to parse a .pdf file and likely fail for a text placeholder', async () => {
    const pdfOriginalPath = path.join(samplesDir, 'sample.pdf');
    try {
      await fs.access(pdfOriginalPath);
    } catch (e) {
      console.warn('Sample PDF (placeholder) not found, skipping PDF parsing test.');
      return;
    }
    const testFilePath = path.join(tempTestDir, 'test_placeholder.pdf');
    await fs.copyFile(pdfOriginalPath, testFilePath);

    // Expect an error because the placeholder is not a valid PDF structure
    await expect(parseFile(testFilePath, 'application/pdf')).rejects.toThrow();
    // Check if file was deleted due to parsing error
    await expect(fs.access(testFilePath)).rejects.toThrow();
  });

  it('should attempt to parse a .docx file and likely fail for a text placeholder', async () => {
    const docxOriginalPath = path.join(samplesDir, 'sample.docx');
    try {
      await fs.access(docxOriginalPath);
    } catch (e) {
      console.warn('Sample DOCX (placeholder) not found, skipping DOCX parsing test.');
      return;
    }
    const testFilePath = path.join(tempTestDir, 'test_placeholder.docx');
    await fs.copyFile(docxOriginalPath, testFilePath);

    // Expect an error because the placeholder is not a valid DOCX structure
    await expect(parseFile(testFilePath, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')).rejects.toThrow();
    // Check if file was deleted
    await expect(fs.access(testFilePath)).rejects.toThrow();
  });

  it('should throw error for unsupported file type and delete the file', async () => {
    const testFilePath = path.join(tempTestDir, 'test.unsupported');
    await fs.writeFile(testFilePath, 'some data');
    await expect(parseFile(testFilePath, 'application/octet-stream')).rejects.toThrow('Unsupported file type: application/octet-stream');
    // Check if file was deleted
    await expect(fs.access(testFilePath)).rejects.toThrow();
  });
});
