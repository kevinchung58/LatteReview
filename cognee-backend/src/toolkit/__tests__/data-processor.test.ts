import { processFileToDocuments, SupportedFileMimeTypes } from '../data-processor';
import { Document } from '@langchain/core/documents';
import { PDFLoader } from '@langchain/community/document_loaders/fs/pdf';
import { TextLoader } from '@langchain/community/document_loaders/fs/text';
import { DocxLoader } from '@langchain/community/document_loaders/fs/docx';
import { RecursiveCharacterTextSplitter } from 'langchain/text_splitter';

// Mock the loaders and splitter
jest.mock('@langchain/community/document_loaders/fs/pdf');
jest.mock('@langchain/community/document_loaders/fs/text');
jest.mock('@langchain/community/document_loaders/fs/docx');
jest.mock('langchain/text_splitter');

describe('Data Processor Toolkit', () => {
  const mockFilePath = 'test_file.pdf';
  const mockDocuments: Document[] = [new Document({ pageContent: 'This is a test document.', metadata: { source: 'test.pdf'} })];
  const mockSplitDocuments: Document[] = [
    new Document({ pageContent: 'This is a test document.', metadata: { source: 'test_file.pdf', filePath: mockFilePath } })
  ];

  beforeEach(() => {
    // Reset mocks before each test
    (PDFLoader as jest.Mock).mockClear();
    (TextLoader as jest.Mock).mockClear();
    (DocxLoader as jest.Mock).mockClear();
    (RecursiveCharacterTextSplitter as jest.Mock).mockClear();

    // Mock implementations
    (PDFLoader.prototype.load as jest.Mock) = jest.fn().mockResolvedValue(mockDocuments);
    (TextLoader.prototype.load as jest.Mock) = jest.fn().mockResolvedValue(mockDocuments);
    (DocxLoader.prototype.load as jest.Mock) = jest.fn().mockResolvedValue(mockDocuments);
    (RecursiveCharacterTextSplitter.prototype.splitDocuments as jest.Mock) = jest.fn().mockResolvedValue(mockSplitDocuments);
  });

  test('processFileToDocuments should use PDFLoader for PDF files', async () => {
    await processFileToDocuments(mockFilePath, 'application/pdf');
    expect(PDFLoader).toHaveBeenCalledWith(mockFilePath);
    expect(PDFLoader.prototype.load).toHaveBeenCalled();
    expect(RecursiveCharacterTextSplitter).toHaveBeenCalledWith({ chunkSize: 1000, chunkOverlap: 200 });
    expect(RecursiveCharacterTextSplitter.prototype.splitDocuments).toHaveBeenCalledWith(mockDocuments);
  });

  test('processFileToDocuments should use TextLoader for TXT files', async () => {
    await processFileToDocuments('test_file.txt', 'text/plain');
    expect(TextLoader).toHaveBeenCalledWith('test_file.txt');
    expect(TextLoader.prototype.load).toHaveBeenCalled();
  });

  test('processFileToDocuments should use DocxLoader for DOCX files', async () => {
    await processFileToDocuments('test_file.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document');
    expect(DocxLoader).toHaveBeenCalledWith('test_file.docx');
    expect(DocxLoader.prototype.load).toHaveBeenCalled();
  });

  test('processFileToDocuments should add source and filePath to metadata', async () => {
    const result = await processFileToDocuments(mockFilePath, 'application/pdf');
    expect(result[0].metadata.source).toBe('test_file.pdf');
    expect(result[0].metadata.filePath).toBe(mockFilePath);
  });

  test('processFileToDocuments should throw error for unsupported file types', async () => {
    await expect(processFileToDocuments('test_file.unsupported', 'application/unsupported'))
      .rejects.toThrow('Unsupported file type: application/unsupported or extension: .unsupported');
  });
});
