import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react'; // useMemo imported
import ForceGraph2D, { NodeObject, LinkObject } from 'react-force-graph-2d';
import { getGraphData, GraphData, GraphNode, GraphLink, getNodeNeighbors, getGraphSchemaSummary, GraphSchemaSummary } from '../services/apiService';
import GraphDetailPanel from './GraphDetailPanel';
import styles from './KnowledgeGraphVisualizer.module.css'; // Import CSS module
// Note: GraphDetailPanel expects CustomNodeObject/CustomLinkObject.
// GraphNode/GraphLink from apiService should be compatible if they include all necessary fields.

const KnowledgeGraphVisualizer: React.FC = () => {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [containerWidth, setContainerWidth] = useState<number>(600); // Default width
  const graphContainerRef = useRef<HTMLDivElement>(null);
  const [selectedElement, setSelectedElement] = useState<GraphNode | GraphLink | null>(null);
  const [isExpandingNode, setIsExpandingNode] = useState<string | false>(false); // Store ID of node being expanded or false
  const [isMobile, setIsMobile] = useState<boolean>(window.innerWidth < 768);

  const [availableSchema, setAvailableSchema] = useState<GraphSchemaSummary>({ nodeLabels: [], relationshipTypes: [] });
  const [activeNodeLabelFilters, setActiveNodeLabelFilters] = useState<Set<string>>(new Set());
  const [activeRelationshipTypeFilters, setActiveRelationshipTypeFilters] = useState<Set<string>>(new Set());
  const [schemaError, setSchemaError] = useState<string>('');


  const fetchData = useCallback(async (term?: string) => {
    setIsLoading(true);
    setError('');
    try {
      const data = await getGraphData(term);
      setGraphData(data);
    } catch (err: any) {
      console.error('Failed to fetch graph data:', err);
      setError(err.message || 'Could not load graph data.');
      setGraphData({ nodes: [], links: [] }); // Clear graph on error
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Fetch initial overview graph data on component mount
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Fetch schema on component mount
  useEffect(() => {
    const fetchSchema = async () => {
      try {
        setSchemaError('');
        const schema = await getGraphSchemaSummary();
        setAvailableSchema(schema);
        // Initialize filters to all selected by default
        setActiveNodeLabelFilters(new Set(schema.nodeLabels));
        setActiveRelationshipTypeFilters(new Set(schema.relationshipTypes));
      } catch (err: any) {
        console.error('Failed to fetch graph schema:', err);
        setSchemaError(err.message || 'Could not load graph schema.');
      }
    };
    fetchSchema();
  }, []);

  // Update graph width on resize
  useEffect(() => {
     const updateWidth = () => {
         if (graphContainerRef.current) {
             setContainerWidth(graphContainerRef.current.offsetWidth);
         }
     };
     window.addEventListener('resize', updateWidth);
     updateWidth(); // Initial width
     return () => window.removeEventListener('resize', updateWidth);
  }, []);

  // Effect to update isMobile state on window resize
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    window.addEventListener('resize', checkMobile);
    checkMobile(); // Initial check
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const handleSearchSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    fetchData(searchTerm);
  };

  const handleNodeLabelFilterChange = (label: string) => {
    setActiveNodeLabelFilters(prevFilters => {
      const newFilters = new Set(prevFilters);
      if (newFilters.has(label)) {
        newFilters.delete(label);
      } else {
        newFilters.add(label);
      }
      return newFilters;
    });
  };

  const handleRelationshipTypeFilterChange = (type: string) => {
    setActiveRelationshipTypeFilters(prevFilters => {
      const newFilters = new Set(prevFilters);
      if (newFilters.has(type)) {
        newFilters.delete(type);
      } else {
        newFilters.add(type);
      }
      return newFilters;
    });
  };

  const handleNodeDoubleClick = async (node: NodeObject) => {
    if (!node.id) return;
    console.log('Double-clicked node:', node);
    setIsExpandingNode(node.id as string);
    setError(''); // Clear previous errors

    try {
      const newGraphData = await getNodeNeighbors(node.id as string);

      setGraphData(prevData => {
        const existingNodeIds = new Set(prevData.nodes.map(n => n.id));
        const newNodes = newGraphData.nodes.filter(n => !existingNodeIds.has(n.id));

        const existingLinkIds = new Set(prevData.links.map(l => (l as any).id)); // Assuming links have unique 'id'
        const newLinks = newGraphData.links.filter(l => !(existingLinkIds.has((l as any).id)));

        if (newNodes.length === 0 && newLinks.length === 0) {
          console.log('No new nodes or links to add from expansion.');
          // Optionally set a message to user if desired
          return prevData; // No change
        }

        return {
          nodes: [...prevData.nodes, ...newNodes],
          links: [...prevData.links, ...newLinks],
        };
      });

    } catch (err: any) {
      console.error(`Failed to fetch neighbors for node ${node.id}:`, err);
      setError(err.message || `Could not expand node ${node.id}.`);
    } finally {
      setIsExpandingNode(false);
    }
  };

  // Custom node rendering
  const renderNode = (node: NodeObject, ctx: CanvasRenderingContext2D, globalScale: number) => {
     const label = (node as any).name || node.id || '';
     const fontSize = 12 / globalScale;
     ctx.font = `${fontSize}px Sans-Serif`;
     // const textWidth = ctx.measureText(label).width; // Not used in this simplified version
     // const rectPadding = 2 / globalScale; // Not used
     // const rectWidth = textWidth + 2 * rectPadding; // Not used
     // const rectHeight = fontSize + 2 * rectPadding; // Not used

     // Simple colored circle as node representation
     ctx.beginPath();
     // @ts-ignore: Property 'x' does not exist on type 'NodeObject<NodeObject>'.
     ctx.arc(node.x, node.y, 5 / globalScale, 0, 2 * Math.PI, false);
     // Highlight selected node
     const typedNode = node as GraphNode; // Cast to access custom properties like __selected
     ctx.fillStyle = typedNode.__selected ? 'orange' : (typedNode.color || (typedNode.labels?.includes('Entity') ? 'blue' : 'red'));
     ctx.fill();

     // Node label
     ctx.textAlign = 'center';
     ctx.textBaseline = 'middle';
     ctx.fillStyle = 'black';
     // @ts-ignore: Property 'y' does not exist on type 'NodeObject<NodeObject>'.
     ctx.fillText(label, node.x, node.y + 10 / globalScale);
  };

  const displayedGraphData = useMemo(() => {
    // If schema isn't fully loaded yet, or if there are no active filters, return original data.
    // This also handles the initial state where all filters are active by default.
    const allNodeLabelsSelected = activeNodeLabelFilters.size === availableSchema.nodeLabels.length;
    const allRelationshipTypesSelected = activeRelationshipTypeFilters.size === availableSchema.relationshipTypes.length;

    // If all filters are active (initial state or user re-selects all), no filtering needed, unless schema is empty
    if ( (availableSchema.nodeLabels.length > 0 && allNodeLabelsSelected) &&
         (availableSchema.relationshipTypes.length > 0 && allRelationshipTypesSelected) ) {
        // This condition might be too simple if we want "show all if no filters touched" vs "show all if ALL filters explicitly checked"
        // The current setup initializes filters to all checked, so this path is taken initially.
        // If user deselects any, then filtering logic below applies.
        // return graphData; // This was the original thought, but this doesn't apply filtering if only one category is fully selected
    }


    const filteredNodes = graphData.nodes.filter(node => {
      const graphNode = node as GraphNode; // Ensure we're working with our extended GraphNode type
      const nodeActualLabels = graphNode.labels || [];

      // If no label filters are defined in the schema yet, or if all available labels are selected, show the node (subject to relationship checks later)
      if (availableSchema.nodeLabels.length === 0 || activeNodeLabelFilters.size === availableSchema.nodeLabels.length) return true;
      // If there are label filters defined and the set of active filters is empty, show no nodes.
      if (activeNodeLabelFilters.size === 0) return false;
      // If the node has no labels, it cannot satisfy any specific active filter unless all filters are active (covered above)
      if (nodeActualLabels.length === 0) return false;

      return nodeActualLabels.some(label => activeNodeLabelFilters.has(label));
    });

    const filteredNodeIds = new Set(filteredNodes.map(node => node.id));

    const filteredLinks = graphData.links.filter(link => {
      const graphLink = link as GraphLink; // Ensure we're working with our extended GraphLink type
      const linkType = graphLink.type || '';

      let typeMatch = false;
      // If no relationship type filters are defined in schema, or all available types are selected, consider it a match for type
      if (availableSchema.relationshipTypes.length === 0 || activeRelationshipTypeFilters.size === availableSchema.relationshipTypes.length) {
        typeMatch = true;
      } else if (activeRelationshipTypeFilters.size === 0) { // All type filters exist but are deselected
        typeMatch = false;
      } else {
        typeMatch = activeRelationshipTypeFilters.has(linkType);
      }

      if (!typeMatch) return false;

      const sourceId = typeof graphLink.source === 'object' && graphLink.source !== null ? (graphLink.source as any).id : graphLink.source;
      const targetId = typeof graphLink.target === 'object' && graphLink.target !== null ? (graphLink.target as any).id : graphLink.target;
      return filteredNodeIds.has(sourceId as string | number) && filteredNodeIds.has(targetId as string | number);
    });
    return { nodes: filteredNodes, links: filteredLinks };
  }, [graphData, activeNodeLabelFilters, activeRelationshipTypeFilters, availableSchema]);

  return (
    <div ref={graphContainerRef} className={styles.visualizerContainer} style={{ position: 'relative' }}> {/* Inline position:relative kept as it's crucial for panel */}
      <form onSubmit={handleSearchSubmit} className={styles.searchForm}>
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search graph by term..."
          aria-label="Search graph by term" // Added aria-label
          className={styles.searchInput}
        />
        <button type="submit" disabled={isLoading || isExpandingNode}> {/* Also disable on expand */}
          {isLoading ? 'Searching...' : (isExpandingNode ? 'Expanding...' : 'Search Graph')}
        </button>
      </form>

      {schemaError && <p className={styles.errorMessage} aria-live="assertive">Error loading schema: {schemaError}</p>}

      <div className={styles.filtersContainer}>
        {availableSchema.nodeLabels.length > 0 && (
          <div className={styles.filterSection}>
              <h4>Filter Node Labels:</h4> {/* Will pick up styles.filterSection h4 */}
              {availableSchema.nodeLabels.map(label => (
                  <label key={`label-${label}`} className={styles.filterCheckboxLabel}>
                      <input
                          type="checkbox"
                          checked={activeNodeLabelFilters.has(label)}
                          onChange={() => handleNodeLabelFilterChange(label)}
                          // input specific style is in the CSS module
                      /> {label}
                  </label>
              ))}
          </div>
        )}
        {availableSchema.relationshipTypes.length > 0 && (
          <div className={styles.filterSection}>
              <h4>Filter Relationship Types:</h4> {/* Will pick up styles.filterSection h4 */}
              {availableSchema.relationshipTypes.map(type => (
                  <label key={`type-${type}`} className={styles.filterCheckboxLabel}>
                      <input
                          type="checkbox"
                          checked={activeRelationshipTypeFilters.has(type)}
                          onChange={() => handleRelationshipTypeFilterChange(type)}
                          // input specific style is in the CSS module
                      /> {type}
                  </label>
              ))}
          </div>
        )}
      </div>

      {isLoading && <p className={styles.loadingMessage} aria-live="polite">Loading graph data...</p>}
      {isExpandingNode &&
        <p className={styles.loadingMessage} aria-live="polite">
          Expanding node (ID: {typeof isExpandingNode === 'string' ? isExpandingNode : ''})...
        </p>}
      {error && <p className={styles.errorMessage} aria-live="assertive">Error: {error}</p>}

      {!isLoading && !isExpandingNode && !error && displayedGraphData.nodes.length === 0 && (
        <p className={styles.noDataMessage} aria-live="polite">No graph data to display with current filters. Try adjusting filters or searching.</p>
      )}

      {/* Use displayedGraphData here */}
      {!isLoading && !isExpandingNode && !error && displayedGraphData.nodes.length > 0 && (
         <ForceGraph2D
             graphData={displayedGraphData}
             nodeLabel="name" // Property to display on node hover
             nodeCanvasObject={renderNode} // Custom node rendering
             linkLabel="type"   // Property to display on link hover
             linkDirectionalArrowLength={3.5}
             linkDirectionalArrowRelPos={1}
             linkCurvature={0.1}
             width={containerWidth > 0 ? containerWidth - 20 : 300 } // Subtract padding, ensure positive
             height={isMobile ? 300 : 400} // Conditional height
             backgroundColor="#f9f9f9"
             // @ts-ignore: Type problem with linkSource/linkTarget from react-force-graph, common issue.
             linkSource="source"
             // @ts-ignore:
             linkTarget="target"
             onNodeDoubleClick={handleNodeDoubleClick} // Added
             onNodeClick={(node, event) => {
               console.log('Clicked node:', node);
               const clickedNode = node as GraphNode;
               // Update graphData to mark the node as selected
               setGraphData(prevGraphData => ({
                 ...prevGraphData,
                 nodes: prevGraphData.nodes.map(n => ({
                   ...n,
                   __selected: n.id === clickedNode.id
                 }))
               }));
               setSelectedElement(clickedNode);
             }}
             onLinkClick={(link, event) => {
               console.log('Clicked link:', link);
                // Clear node selection when a link is clicked, or handle link selection differently
                setGraphData(prevGraphData => ({
                    ...prevGraphData,
                    nodes: prevGraphData.nodes.map(n => ({ ...n, __selected: false }))
                }));
               setSelectedElement(link as GraphLink);
             }}
             onBackgroundClick={() => {
               setGraphData(prevGraphData => ({
                 ...prevGraphData,
                 nodes: prevGraphData.nodes.map(n => ({ ...n, __selected: false }))
               }));
               setSelectedElement(null);
             }}
         />
      )}
      {selectedElement && (
        <GraphDetailPanel
          element={selectedElement}
          onClose={() => {
            setGraphData(prevGraphData => ({
              ...prevGraphData,
              nodes: prevGraphData.nodes.map(n => ({ ...n, __selected: false }))
            }));
            setSelectedElement(null);
          }}
        />
      )}
    </div>
  );
};

export default KnowledgeGraphVisualizer;
