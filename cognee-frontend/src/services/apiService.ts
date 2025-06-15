import axios from 'axios';

const VITE_API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3001';

const apiClient = axios.create({
  baseURL: VITE_API_BASE_URL,
});

export const ingestFile = async (formData: FormData): Promise<any> => {
  try {
    const response = await apiClient.post('/ingest', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error: any) {
    console.error('Error ingesting file:', error);
    throw error.response?.data || error.message || new Error('File ingestion failed');
  }
};

export interface QueryResponse {
  question: string;
  answer: string;
  graphContextItems?: string[];
  vectorContextItems?: string[];
}

export const askQuery = async (question: string): Promise<QueryResponse> => {
  try {
    const response = await apiClient.post<QueryResponse>('/query', { question });
    return response.data;
  } catch (error: any) {
    console.error('Error asking query:', error);
    throw error.response?.data || error.message || new Error('Query failed');
  }
};
