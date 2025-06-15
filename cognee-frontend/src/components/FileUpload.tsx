import React, { useState, ChangeEvent, FormEvent } from 'react';
import { ingestFile } from '../services/apiService';
import styles from './FileUpload.module.css'; // Import CSS module

const FileUpload: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [message, setMessage] = useState<string>('');
  const [error, setError] = useState<string>('');
  const fileInputRef = React.useRef<HTMLInputElement>(null); // Ref to reset file input

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
      setMessage(
        `File ingested successfully: ${response.originalName || selectedFile.name}. ` +
        `Server Filename: ${response.filename}. ` +
        `Chunks: ${response.totalChunks}. ` +
        `SPOs: ${response.totalSPOsExtracted}. ` +
        `Embeddings: ${response.totalEmbeddingsStored}.`
      );
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = ""; // Reset file input
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
    <div className={styles.formContainer}>
      <form onSubmit={handleSubmit}>
        <div className={styles.fileInputWrapper}>
          <label htmlFor="file-input" className={styles.fileInputLabel}>
            Choose File
          </label>
          <input
             id="file-input"
             type="file"
             ref={fileInputRef} // Added ref
             onChange={handleFileChange}
             accept=".pdf,.txt,.docx"
             style={{ display: 'none' }} // Hide the default input
            //  Using ref to reset is more reliable than key change for hidden inputs
          />
          {selectedFile && <span className={styles.fileName}>{selectedFile.name}</span>}
        </div>
        <button type="submit" disabled={isLoading || !selectedFile}>
          {isLoading ? 'Uploading...' : 'Upload File'}
        </button>
      </form>
      <div className={styles.messageArea}>
        {isLoading && <p>Processing file, please wait...</p>}
        {message && <p className={styles.successMessage}>{message}</p>}
        {error && <p className={styles.errorMessage}>{error}</p>}
      </div>
    </div>
  );
};

export default FileUpload;
