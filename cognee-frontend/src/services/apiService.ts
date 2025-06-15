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

export interface GraphNode {
  id: string;
  name: string;
  labels?: string[];
  properties?: Record<string, any>;
  // Add other properties if needed based on what react-force-graph-2d uses, e.g., val, color
}

export interface GraphLink {
  source: string; // ID of source node
  target: string; // ID of target node
  type?: string;
  // Add other properties if needed, e.g., value, color
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

export const getGraphData = async (searchTerm?: string): Promise<GraphData> => {
  try {
    const params = searchTerm ? { searchTerm } : {};
    const response = await apiClient.get<GraphData>('/graph-data', { params });
    return response.data;
  } catch (error: any) {
    console.error('Error fetching graph data:', error);
    throw error.response?.data || error.message || new Error('Failed to fetch graph data');
  }
};

export const getNodeNeighbors = async (nodeId: string): Promise<GraphData> => {
  try {
    // Ensure nodeId is properly encoded if it can contain special characters, though elementIds usually don't.
    const response = await apiClient.get<GraphData>(`/node-neighbors/${nodeId}`);
    return response.data;
  } catch (error: any) {
    console.error(`Error fetching neighbors for node ${nodeId}:`, error);
    throw error.response?.data || error.message || new Error(`Failed to fetch neighbors for node ${nodeId}`);
  }
};
