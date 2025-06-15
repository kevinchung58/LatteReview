import React, { useState, ChangeEvent, FormEvent } from 'react';
import { ingestFile } from '../services/apiService';

const FileUpload: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [message, setMessage] = useState<string>('');
  const [error, setError] = useState<string>('');

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0]);
      setMessage(''); // Clear previous messages
      setError('');
    } else {
      setSelectedFile(null);
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedFile) {
      setError('Please select a file first.');
      return;
    }

    setIsLoading(true);
    setMessage('');
    setError('');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await ingestFile(formData);
      // Assuming backend returns a message like:
      // { message: '...', filename: '...', totalChunks: ..., totalSPOsExtracted: ..., totalEmbeddingsStored: ... }
      setMessage(
        `File ingested successfully: ${response.originalName || selectedFile.name}. ` +
        `Server Filename: ${response.filename}. ` +
        `Chunks: ${response.totalChunks}. ` +
        `SPOs: ${response.totalSPOsExtracted}. ` +
        `Embeddings: ${response.totalEmbeddingsStored}.`
      );
      setSelectedFile(null); // Clear selection after successful upload
      // Clear the file input visually (this is a bit tricky, often requires resetting the form or input value)
      if (event.target instanceof HTMLFormElement) {
         event.target.reset();
      }
    } catch (err: any) {
      console.error('Upload error:', err);
      setError(err.message || 'File upload failed. Check console for details.');
      setMessage('');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="file-input">Choose file to upload:</label>
          <input
             id="file-input"
             type="file"
             onChange={handleFileChange}
             accept=".pdf,.txt,.docx"
             key={selectedFile ? 'file-selected' : 'no-file'} // Helps reset input if needed
          />
        </div>
        <button type="submit" disabled={isLoading || !selectedFile}>
          {isLoading ? 'Uploading...' : 'Upload File'}
        </button>
      </form>
      {isLoading && <p>Processing file, please wait...</p>}
      {message && <p style={{ color: 'green' }}>{message}</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </div>
  );
};

export default FileUpload;
