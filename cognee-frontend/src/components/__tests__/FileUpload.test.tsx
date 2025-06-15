// src/components/__tests__/FileUpload.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import FileUpload from '../FileUpload'; // Adjust path as needed
import * as apiService from '../../services/apiService'; // To mock ingestFile

// Mock the apiService.ingestFile function
vi.mock('../../services/apiService', () => ({
  ingestFile: vi.fn(),
}));

describe('FileUpload Component', () => {
  beforeEach(() => {
    // Reset mocks before each test
    vi.resetAllMocks();
  });

  it('renders the file input and upload button', () => {
    render(<FileUpload />);
    expect(screen.getByLabelText(/choose file/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /upload file/i })).toBeInTheDocument();
  });

  it('enables upload button when a file is selected', async () => {
    render(<FileUpload />);
    const fileInput = screen.getByLabelText(/choose file/i); // Actually targets the hidden input via label
    const uploadButton = screen.getByRole('button', { name: /upload file/i });

    expect(uploadButton).toBeDisabled(); // Initially disabled

    const file = new File(['hello'], 'hello.txt', { type: 'text/plain' });
    // userEvent.upload is for interacting with the visible input, but ours is hidden.
    // We need to fire a change event on the hidden input directly.
    // The label click is implicitly handled by testing-library when getting by label text and clicking label.
    // However, for userEvent.upload, it's more direct to target the input.
    // Since our input is hidden, we get it by its ID (which label is connected to)
    const hiddenInput = screen.getByTestId('file-input') || document.getElementById('file-input'); // Assuming you add data-testid or use ID
    if (!hiddenInput) throw new Error("File input not found");


    await userEvent.upload(hiddenInput, file);

    expect(uploadButton).toBeEnabled();
    expect(screen.getByText('hello.txt')).toBeInTheDocument(); // Check if file name is displayed
  });

  it('calls ingestFile and displays success message on successful upload', async () => {
    const mockSuccessResponse = {
      originalName: 'hello.txt',
      filename: 'server-filename.txt',
      totalChunks: 1,
      totalSPOsExtracted: 0,
      totalEmbeddingsStored: 1,
      message: 'File ingested successfully (mocked)' // This field is not directly used by component, but good to have
    };
    (apiService.ingestFile as vi.Mock).mockResolvedValue(mockSuccessResponse);

    render(<FileUpload />);
    const hiddenInput = screen.getByTestId('file-input') || document.getElementById('file-input');
    if (!hiddenInput) throw new Error("File input not found");
    const uploadButton = screen.getByRole('button', { name: /upload file/i });
    const file = new File(['hello'], 'hello.txt', { type: 'text/plain' });

    await userEvent.upload(hiddenInput, file); // Select file
    await userEvent.click(uploadButton); // Click upload

    expect(apiService.ingestFile).toHaveBeenCalledTimes(1);
    // The button text changes to 'Uploading...' when isLoading is true
    expect(screen.getByRole('button', { name: /uploading.../i})).toBeInTheDocument();

    await waitFor(() => {
      // The success message is more detailed
      expect(screen.getByText(/file ingested successfully: hello.txt/i)).toBeInTheDocument();
      expect(screen.getByText(/server filename: server-filename.txt/i)).toBeInTheDocument();
    });
    expect(screen.queryByRole('button', { name: /uploading.../i})).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /upload file/i})).toBeInTheDocument(); // Back to original text
  });

  it('displays error message on failed upload', async () => {
    (apiService.ingestFile as vi.Mock).mockRejectedValue(new Error('Mocked upload failed'));

    render(<FileUpload />);
    const hiddenInput = screen.getByTestId('file-input') || document.getElementById('file-input');
    if (!hiddenInput) throw new Error("File input not found");
    const uploadButton = screen.getByRole('button', { name: /upload file/i });
    const file = new File(['hello'], 'hello.txt', { type: 'text/plain' });

    await userEvent.upload(hiddenInput, file);
    await userEvent.click(uploadButton);

    expect(apiService.ingestFile).toHaveBeenCalledTimes(1);
    await waitFor(() => {
      expect(screen.getByText(/mocked upload failed/i)).toBeInTheDocument();
    });
  });

  it('shows an error if trying to submit without a file', async () => {
     render(<FileUpload />);
     const uploadButton = screen.getByRole('button', { name: /upload file/i });
     await userEvent.click(uploadButton); // userEvent for more realistic click
     expect(apiService.ingestFile).not.toHaveBeenCalled();
     expect(screen.getByText(/please select a file first/i)).toBeInTheDocument();
  });
});
