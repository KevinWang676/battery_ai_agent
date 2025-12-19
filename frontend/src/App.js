import React, { useState, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Header from './components/Header';
import DemoBanner from './components/DemoBanner';
import QueryInput from './components/QueryInput';
import FileUpload from './components/FileUpload';
import AgentStatus from './components/AgentStatus';
import ExperimentPlans from './components/ExperimentPlans';
import Summary from './components/Summary';
import References from './components/References';
import './styles/App.css';

const API_URL = process.env.REACT_APP_API_URL || 'https://battery0676.ngrok.app';

function App() {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [documentsCount, setDocumentsCount] = useState(0);

  // Fetch document count on page load
  useEffect(() => {
    const fetchDocumentCount = async () => {
      try {
        const response = await fetch(`${API_URL}/api/documents`);
        if (response.ok) {
          const data = await response.json();
          setDocumentsCount(data.total_indexed || 0);
        }
      } catch (err) {
        console.error('Failed to fetch document count:', err);
      }
    };
    
    fetchDocumentCount();
  }, []);

  const handleQuerySubmit = useCallback(async (queryText, userMaterials = '') => {
    if (!queryText.trim()) return;
    
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/api/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          query: queryText,
          user_materials: userMaterials || null
        }),
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message || 'Failed to process query');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Handle file upload (FileUpload component manages the actual upload)
  const handleFileUpload = useCallback((files) => {
    // Files are uploaded by the FileUpload component directly
    // This callback is just for notification
    console.log('Files uploaded:', files.length);
  }, []);

  // Handle index completion - refetch actual count from backend
  const handleIndexComplete = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/documents`);
      if (response.ok) {
        const data = await response.json();
        setDocumentsCount(data.total_indexed || 0);
      }
    } catch (err) {
      console.error('Failed to fetch document count after indexing:', err);
    }
  }, []);

  return (
    <div className="app">
      <DemoBanner />
      <Header documentsCount={documentsCount} />
      
      <main className="main-content">
        <motion.div 
          className="hero-section"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <h1 className="hero-title">
            <span className="text-gradient">Electrolyte Design</span>
            <br />
            Multi-Agent System
          </h1>
          <p className="hero-subtitle">
            AI-powered electrolyte formulation design with intelligent experiment planning
          </p>
        </motion.div>

        <div className="content-grid">
          <motion.div 
            className="input-section"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <QueryInput 
              query={query}
              setQuery={setQuery}
              onSubmit={handleQuerySubmit}
              isLoading={isLoading}
            />
            
            <FileUpload 
              onUpload={handleFileUpload}
              uploadedFiles={uploadedFiles}
              onIndexComplete={handleIndexComplete}
            />

            <AgentStatus isProcessing={isLoading} />
          </motion.div>

          <motion.div 
            className="results-section"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <AnimatePresence mode="wait">
              {error && (
                <motion.div 
                  className="error-message"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                >
                  <span className="error-icon">⚠️</span>
                  {error}
                </motion.div>
              )}

              {isLoading && (
                <motion.div 
                  className="loading-state"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <div className="loading-spinner"></div>
                  <p>Analyzing with multi-agent system...</p>
                  <div className="loading-agents">
                    <span>Literature Search</span>
                    <span>Property Analysis</span>
                    <span>Experiment Planning</span>
                    <span>Performance Prediction</span>
                  </div>
                </motion.div>
              )}

              {result && !isLoading && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5 }}
                >
                  <Summary 
                    summary={result.summary}
                    processingTime={result.processing_time}
                  />
                  
                  <References agentResponses={result.agent_responses} />
                  
                  <ExperimentPlans plans={result.experiment_plans} />
                </motion.div>
              )}

              {!result && !isLoading && !error && (
                <motion.div 
                  className="empty-state"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                >
                  <div className="empty-icon">🔬</div>
                  <h3>Ready to Design</h3>
                  <p>Enter your electrolyte design requirements above to get started</p>
                  <div className="example-queries">
                    <p className="examples-label">Try these examples:</p>
                    <button onClick={() => setQuery("Design a high-voltage electrolyte for NMC cathode with silicon anode")}>
                      High-voltage electrolyte for NMC/Si
                    </button>
                    <button onClick={() => setQuery("Fast-charging electrolyte with good low-temperature performance")}>
                      Fast-charging electrolyte
                    </button>
                    <button onClick={() => setQuery("Long cycle life electrolyte for EV application with LiPF6 salt")}>
                      Long cycle life for EV
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>
      </main>

      <footer className="footer">
        <p>Powered by Multi-Agent AI System</p>
      </footer>
    </div>
  );
}

export default App;

