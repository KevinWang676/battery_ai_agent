import React, { useState } from 'react';
import { motion } from 'framer-motion';
import './QueryInput.css';

function QueryInput({ query, setQuery, onSubmit, isLoading }) {
  const [userMaterials, setUserMaterials] = useState('');
  const [showMaterialsInput, setShowMaterialsInput] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(query, userMaterials);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSubmit(query, userMaterials);
    }
  };

  return (
    <motion.div 
      className="query-input-card"
      whileHover={{ boxShadow: '0 0 30px rgba(0, 212, 255, 0.1)' }}
    >
      <div className="card-header">
        <div className="card-icon">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 21L15 15M17 10C17 13.866 13.866 17 10 17C6.13401 17 3 13.866 3 10C3 6.13401 6.13401 3 10 3C13.866 3 17 6.13401 17 10Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        <h3>Design Query</h3>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="textarea-wrapper">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe your electrolyte design requirements...

Example: Design a high-voltage electrolyte for NMC811 cathode with silicon-graphite anode, targeting fast charging applications."
            rows={5}
            disabled={isLoading}
          />
        </div>

        {/* Toggle for Materials Input */}
        <div className="materials-toggle">
          <button 
            type="button" 
            className={`toggle-button ${showMaterialsInput ? 'active' : ''}`}
            onClick={() => setShowMaterialsInput(!showMaterialsInput)}
          >
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="toggle-icon">
              <path d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            {showMaterialsInput ? 'Hide Materials Input' : 'Specify Materials (Optional)'}
            <span className="toggle-arrow">{showMaterialsInput ? '▲' : '▼'}</span>
          </button>
        </div>

        {/* Materials Input Section */}
        {showMaterialsInput && (
          <motion.div 
            className="materials-input-section"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="materials-header">
              <span className="materials-icon">🧪</span>
              <span>User-Specified Materials</span>
            </div>
            <textarea
              value={userMaterials}
              onChange={(e) => setUserMaterials(e.target.value)}
              placeholder="Enter specific materials or formulation you want to use...

Examples:
• ZnSO4 2M, Zn(CF3SO3)2, water
• 1M LiPF6 in EC:DMC (1:1), 2% VC
• NaTFSI 1M in diglyme
• Acetonitrile, DMSO, ZnCl2 0.5M"
              rows={3}
              disabled={isLoading}
              className="materials-textarea"
            />
            <div className="materials-hint">
              💡 The system will prioritize these materials in the experiment plans
            </div>
          </motion.div>
        )}

        <button 
          type="submit" 
          className="submit-button"
          disabled={isLoading || !query.trim()}
        >
          {isLoading ? (
            <>
              <span className="button-spinner"></span>
              Analyzing...
            </>
          ) : (
            <>
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M22 2L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              Analyze & Generate Plans
            </>
          )}
        </button>
      </form>

      <div className="input-hints">
        <span className="hint">💡 Mention specific components, voltage ranges, or applications</span>
        {userMaterials && (
          <span className="hint materials-active">
            🧪 Custom materials: {userMaterials.substring(0, 50)}{userMaterials.length > 50 ? '...' : ''}
          </span>
        )}
      </div>
    </motion.div>
  );
}

export default QueryInput;
