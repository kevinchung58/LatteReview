import React from 'react';
import { NodeObject, LinkObject } from 'react-force-graph-2d';
import styles from './GraphDetailPanel.module.css'; // Import CSS module

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
      className={styles.panelOverlay}
      role="region"
      aria-labelledby="graph-detail-panel-title"
    >
      {/* All positioning and base appearance styles moved to .panelOverlay in CSS module */}
      <div className={styles.panelHeader}>
        <h3 id="graph-detail-panel-title" className={styles.panelTitle}>
            {isNode(element) ? 'Node Details' : isLink(element) ? 'Relationship Details' : 'Details'}
        </h3>
        <button
          onClick={onClose}
          className={styles.closeButton}
          aria-label="Close details panel"
        >
          &times;
        </button>
      </div>

      {isNode(element) && (
        <>
          <p className={styles.detailListItem}><strong>ID:</strong> {element.id}</p>
          {element.name && <p className={styles.detailListItem}><strong>Name:</strong> {element.name}</p>}
          {element.labels && element.labels.length > 0 && (
            <p className={styles.detailListItem}><strong>Labels:</strong> {element.labels.join(', ')}</p>
          )}
          {element.properties && Object.keys(element.properties).length > 0 && (
            <>
              <h4 className={styles.detailSectionTitle}>Properties:</h4>
              <ul className={styles.detailList}>
                {Object.entries(element.properties).map(([key, value]) => (
                  <li key={key} className={styles.detailListItem}>
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
          <p className={styles.detailListItem}><strong>ID:</strong> {element.id || 'N/A'}</p>
          <p className={styles.detailListItem}><strong>Type:</strong> {element.type || 'N/A'}</p>
          <p className={styles.detailListItem}><strong>Source:</strong> {getElementId(element.source)}</p>
          <p className={styles.detailListItem}><strong>Target:</strong> {getElementId(element.target)}</p>
          {element.properties && Object.keys(element.properties).length > 0 && (
            <>
              <h4 className={styles.detailSectionTitle}>Properties:</h4>
              <ul className={styles.detailList}>
                {Object.entries(element.properties).map(([key, value]) => (
                  <li key={key} className={styles.detailListItem}>
                    <strong>{key}:</strong> {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                  </li>
                ))}
              </ul>
            </>
          )}
        </>
      )}

      {!isNode(element) && !isLink(element) && (
         <p className={styles.detailListItem}>Selected element type not recognized.</p>
      )}
    </div>
  );
};

export default GraphDetailPanel;
