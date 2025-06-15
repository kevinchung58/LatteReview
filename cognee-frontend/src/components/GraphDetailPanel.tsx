import React from 'react';
import { NodeObject, LinkObject } from 'react-force-graph-2d'; // Assuming LinkObject might need properties too

// Extend LinkObject to include properties if your data structure has them
interface CustomLinkObject extends LinkObject {
  id?: string | number;
  type?: string;
  properties?: Record<string, any>;
  // react-force-graph-2d LinkObject has source and target which can be string | number | NodeObject
  // Ensure they are resolved to string or number for display if they are objects here
  source?: string | number | { id?: string | number };
  target?: string | number | { id?: string | number };
}

interface CustomNodeObject extends NodeObject {
  id?: string | number;
  name?: string;
  labels?: string[];
  properties?: Record<string, any>;
}

interface GraphDetailPanelProps {
  element: CustomNodeObject | CustomLinkObject | null;
  onClose: () => void;
}

const GraphDetailPanel: React.FC<GraphDetailPanelProps> = ({ element, onClose }) => {
  if (!element) {
    return null; // Don't render anything if no element is selected
  }

  // Helper to get ID from node/link source/target which might be object or primitive
  const getElementId = (val: any): string => {
     if (typeof val === 'object' && val !== null && val.id !== undefined) return String(val.id);
     return String(val);
  }

  // Type guard to check if the element is a node or a link
  // Nodes usually have 'name' or 'labels', links have 'source' and 'target'.
  // A more robust way might be to add a 'type' field ('node'/'link') to the element itself when setting it.
  const isNode = (el: any): el is CustomNodeObject => el && (el.name !== undefined || el.labels !== undefined) && el.source === undefined && el.target === undefined;
  const isLink = (el: any): el is CustomLinkObject => el && el.source !== undefined && el.target !== undefined;

  return (
    <div
      style={{
        position: 'absolute',
        top: '10px',
        right: '10px',
        width: '300px',
        maxHeight: 'calc(100% - 20px)',
        overflowY: 'auto',
        backgroundColor: 'white',
        border: '1px solid #ccc',
        borderRadius: '8px',
        padding: '15px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
        zIndex: 1000, // Ensure it's above the graph canvas
      }}
    >
      <button
        onClick={onClose}
        style={{ float: 'right', background: 'none', border: 'none', fontSize: '1.2em', cursor: 'pointer' }}
      >
        &times;
      </button>

      {isNode(element) && (
        <>
          <h3 style={{ marginTop: '0' }}>Node Details</h3>
          <p><strong>ID:</strong> {element.id}</p>
          {element.name && <p><strong>Name:</strong> {element.name}</p>}
          {element.labels && element.labels.length > 0 && (
            <p><strong>Labels:</strong> {element.labels.join(', ')}</p>
          )}
          {element.properties && Object.keys(element.properties).length > 0 && (
            <>
              <h4>Properties:</h4>
              <ul style={{ listStyleType: 'none', paddingLeft: '0' }}>
                {Object.entries(element.properties).map(([key, value]) => (
                  <li key={key} style={{ marginBottom: '5px' }}>
                    <strong>{key}:</strong> {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                  </li>
                ))}
              </ul>
            </>
          )}
        </>
      )}

      {isLink(element) && (
        <>
          <h3 style={{ marginTop: '0' }}>Relationship Details</h3>
          <p><strong>ID:</strong> {element.id || 'N/A'}</p>
          <p><strong>Type:</strong> {element.type || 'N/A'}</p>
          <p><strong>Source:</strong> {getElementId(element.source)}</p>
          <p><strong>Target:</strong> {getElementId(element.target)}</p>
          {element.properties && Object.keys(element.properties).length > 0 && (
            <>
              <h4>Properties:</h4>
              <ul style={{ listStyleType: 'none', paddingLeft: '0' }}>
                {Object.entries(element.properties).map(([key, value]) => (
                  <li key={key} style={{ marginBottom: '5px' }}>
                    <strong>{key}:</strong> {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                  </li>
                ))}
              </ul>
            </>
          )}
        </>
      )}

      {!isNode(element) && !isLink(element) && (
         <p>Selected element type not recognized.</p>
      )}
    </div>
  );
};

export default GraphDetailPanel;
