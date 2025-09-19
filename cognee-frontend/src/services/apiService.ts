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

export interface GraphSchemaSummary {
  nodeLabels: string[];
  relationshipTypes: string[];
}

export const getGraphSchemaSummary = async (): Promise<GraphSchemaSummary> => {
  try {
    const response = await apiClient.get<GraphSchemaSummary>('/graph-schema-summary');
    return response.data;
  } catch (error: any) {
    console.error('Error fetching graph schema summary:', error);
    throw error.response?.data || error.message || new Error('Failed to fetch graph schema summary');
  }
};

// QueryResponse might not be needed here if we only get tokens, or it could represent the final assembled object if desired.
// For now, the function calls onToken, onComplete, onError, and doesn't return a Promise<QueryResponse>.
// The component will be responsible for assembling the final answer.

export const askQuery = async (
  question: string,
  onToken: (token: string) => void,
  onComplete: () => void,
  onError: (error: Error) => void
): Promise<void> => {
  try {
    const response = await fetch(VITE_API_BASE_URL + '/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream' // Important to tell the server we expect an SSE stream
      },
      body: JSON.stringify({ question }),
    });

    if (!response.ok) {
      // Handle HTTP errors before trying to read stream
      const errorBody = await response.text();
      onError(new Error(`Failed to fetch stream: ${response.status} ${response.statusText} - ${errorBody}`));
      return;
    }

    if (!response.body) {
      onError(new Error('Response body is null.'));
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        // Process any remaining buffer content if needed
        if (buffer.trim().startsWith('data:')) { // Check if buffer has a final complete message
            const jsonString = buffer.substring(buffer.indexOf('data:') + 5).trim();
            try {
                const parsed = JSON.parse(jsonString);
                if (parsed.token) {
                    onToken(parsed.token);
                }
            } catch (e) {
                console.error('Failed to parse final SSE JSON from buffer:', jsonString, e);
            }
        }
        break; // Stream finished
      }

      buffer += decoder.decode(value, { stream: true });

      let eolIndex;
      // SSE messages are separated by double newlines (\n\n)
      // A single message can also span multiple lines, each starting with 'data: '
      // Robust parsing should handle multi-line data fields and other event types (event:, id:, retry:)
      // This simplified parser looks for "data: {...}\n\n"
      while ((eolIndex = buffer.indexOf('\n\n')) >= 0) {
        const messageLine = buffer.substring(0, eolIndex).trim();
        buffer = buffer.substring(eolIndex + 2); // Consume the message including \n\n

        if (messageLine.startsWith('data:')) {
          const jsonString = messageLine.substring(5).trim();
          try {
            const parsed = JSON.parse(jsonString);
            if (parsed.token) {
              onToken(parsed.token);
            }
            // Potentially handle other event types here if backend sends them
            // e.g., if(parsed.type === 'context') { onContext(parsed.data); }
          } catch (e) {
            console.error('Failed to parse SSE JSON:', jsonString, e);
            // Potentially call onError or ignore malformed message
          }
        }
      }
    }
    onComplete();
  } catch (error: any) {
    console.error('Error in askQuery stream processing:', error);
    onError(error);
  }
  // No finally block for reader.releaseLock() as it's handled by stream consumption ending
  // or if an error during reader.read() or processing occurs, it's caught.
  // If specific cancellation logic were added, releaseLock would be important there.
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
