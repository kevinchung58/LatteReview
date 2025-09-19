import React from 'react';
import FileUpload from './components/FileUpload';
import ChatInterface from './components/ChatInterface';
import KnowledgeGraphVisualizer from './components/KnowledgeGraphVisualizer';
// No App.css needed if styles are global or via modules for specific components

function App() {
  return (
    <div className="app-container"> {/* Removed inline styles */}
      <header className="app-header text-center" style={{ marginBottom: '40px' }}> {/* Added text-center utility */}
        <h1>Cognee Application</h1>
      </header>

      <main className="app-main">
        <section id="file-upload-section" className="card">
          <h2>Upload Documents</h2>
          <p>Upload PDF, DOCX, or TXT files to populate the knowledge base.</p>
          <FileUpload />
        </section>

        {/* Removed <hr /> in favor of card margins for separation */}

        <section id="chat-section" className="card">
          <h2>Ask Questions</h2>
          <p>Interact with the AI by asking questions based on the uploaded documents.</p>
          <ChatInterface />
        </section>

        <section id="graph-visualization-section" className="card">
          <h2>Explore Knowledge Graph</h2>
          <p>Visualize and explore the relationships in the knowledge base. Search for terms to focus the graph.</p>
          <KnowledgeGraphVisualizer />
        </section>
      </main>

      <footer className="app-footer text-center text-muted" style={{marginTop: '50px', padding: '20px 0', fontSize: '0.9em'}}> {/* Used text-center and text-muted */}
         <p>Cognee RAG Application Demo</p>
      </footer>
    </div>
  );
}
export default App;
