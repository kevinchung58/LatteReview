import React, { useState, useEffect, useCallback, useRef } from 'react';
import ForceGraph2D, { NodeObject, LinkObject } from 'react-force-graph-2d';
import { getGraphData, GraphData, GraphNode, GraphLink } from '../services/apiService'; // Assuming GraphNode and GraphLink are exported from apiService
import GraphDetailPanel from './GraphDetailPanel';
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

  const handleSearchSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    fetchData(searchTerm);
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

  return (
    <div ref={graphContainerRef} style={{ border: '1px solid #eee', borderRadius: '8px', padding: '20px', position: 'relative' }}>
      <form onSubmit={handleSearchSubmit} style={{ marginBottom: '10px' }}>
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search graph by term..."
          // style={{ marginRight: '5px' }} // Removed to use global style from index.css
        />
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Searching...' : 'Search Graph'}
        </button>
      </form>

      {isLoading && <p>Loading graph data...</p>}
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}

      {!isLoading && !error && graphData.nodes.length === 0 && (
        <p>No graph data to display. Try a different search or ensure data is ingested.</p>
      )}

      {!isLoading && !error && graphData.nodes.length > 0 && (
         <ForceGraph2D
             graphData={graphData}
             nodeLabel="name" // Property to display on node hover
             nodeCanvasObject={renderNode} // Custom node rendering
             linkLabel="type"   // Property to display on link hover
             linkDirectionalArrowLength={3.5}
             linkDirectionalArrowRelPos={1}
             linkCurvature={0.1}
             width={containerWidth > 0 ? containerWidth - 20 : 300 } // Subtract padding, ensure positive
             height={400} // Fixed height, or make it responsive
             backgroundColor="#f9f9f9"
             // @ts-ignore: Type problem with linkSource/linkTarget from react-force-graph, common issue.
             linkSource="source"
             // @ts-ignore:
             linkTarget="target"
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
