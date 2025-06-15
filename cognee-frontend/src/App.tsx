import React from 'react';
// import './App.css'; // If App.css is removed/empty
import FileUpload from './components/FileUpload';
import ChatInterface from './components/ChatInterface';
import KnowledgeGraphVisualizer from './components/KnowledgeGraphVisualizer'; // Import new component

function App() {
  return (
    <div className="App" style={{ fontFamily: 'Arial, sans-serif', maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <header className="App-header" style={{ textAlign: 'center', marginBottom: '30px' }}>
        <h1>Cognee Application</h1>
      </header>
      <main>
        <section id="file-upload-section" style={{ marginBottom: '30px', padding: '20px', border: '1px solid #eee', borderRadius: '8px' }}>
          <h2 style={{ marginTop: '0' }}>Upload Documents</h2>
          <p>Upload PDF, DOCX, or TXT files to populate the knowledge base.</p>
          <FileUpload />
        </section>

        <hr style={{ margin: '30px 0', border: '0', borderTop: '1px solid #ccc' }} />

        <section id="chat-section" style={{ marginBottom: '30px', padding: '20px', border: '1px solid #eee', borderRadius: '8px' }}>
          <h2 style={{ marginTop: '0' }}>Ask Questions</h2>
          <p>Interact with the AI by asking questions based on the uploaded documents.</p>
          <ChatInterface />
        </section>

        <hr style={{ margin: '30px 0', border: '0', borderTop: '1px solid #ccc' }} />

        <section id="graph-visualization-section" style={{ padding: '20px', border: '1px solid #eee', borderRadius: '8px' }}>
          <h2 style={{ marginTop: '0' }}>Explore Knowledge Graph</h2>
          <p>Visualize and explore the relationships in the knowledge base. Search for terms to focus the graph.</p>
          <KnowledgeGraphVisualizer />
        </section>
      </main>
      <footer style={{textAlign: 'center', marginTop: '40px', fontSize: '0.9em', color: '#777'}}>
         <p>Cognee RAG Application Demo</p>
      </footer>
    </div>
  );
}

export default App;
