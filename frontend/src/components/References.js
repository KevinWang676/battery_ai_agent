import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './References.css';

function References({ agentResponses }) {
  const [expandedRef, setExpandedRef] = useState(null);
  const [showAll, setShowAll] = useState(false);

  // Extract literature results from agent responses
  const literatureResponse = agentResponses?.find(
    (r) => r.agent_type === 'literature_rag'
  );
  
  const results = literatureResponse?.data?.results || [];
  const sourcesCount = literatureResponse?.data?.sources_count || 0;
  
  // Separate uploaded documents from knowledge base
  const uploadedDocs = results.filter(r => r.source === 'uploaded_document');
  const knowledgeBase = results.filter(r => r.source === 'knowledge_base');
  
  const displayedResults = showAll ? results : results.slice(0, 5);

  if (!results.length) {
    return null;
  }

  const toggleExpand = (index) => {
    setExpandedRef(expandedRef === index ? null : index);
  };

  const truncateContent = (content, maxLength = 200) => {
    if (!content) return '';
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + '...';
  };

  return (
    <motion.div 
      className="references-card"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.1 }}
    >
      <div className="references-header">
        <div className="references-icon">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M4 19.5C4 18.837 4.26339 18.2011 4.73223 17.7322C5.20107 17.2634 5.83696 17 6.5 17H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M6.5 2H20V22H6.5C5.83696 22 5.20107 21.7366 4.73223 21.2678C4.26339 20.7989 4 20.163 4 19.5V4.5C4 3.83696 4.26339 3.20107 4.73223 2.73223C5.20107 2.26339 5.83696 2 6.5 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M8 6H16" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            <path d="M8 10H14" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </div>
        <div>
          <h2>Literature & RAG References</h2>
          <span className="sources-count">
            {sourcesCount} source{sourcesCount !== 1 ? 's' : ''} found
            {uploadedDocs.length > 0 && (
              <span className="uploaded-badge">
                {uploadedDocs.length} from uploaded documents
              </span>
            )}
          </span>
        </div>
      </div>

      <div className="references-content">
        {/* Uploaded Documents Section */}
        {uploadedDocs.length > 0 && (
          <div className="reference-section">
            <h3 className="section-title">
              <span className="section-icon">📄</span>
              From Your Uploaded Documents
            </h3>
            <div className="references-list">
              {uploadedDocs.map((ref, index) => (
                <motion.div
                  key={`uploaded-${index}`}
                  className={`reference-item uploaded ${expandedRef === `u-${index}` ? 'expanded' : ''}`}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <div 
                    className="reference-header"
                    onClick={() => toggleExpand(`u-${index}`)}
                  >
                    <div className="reference-title-row">
                      <span className="reference-number">{index + 1}</span>
                      <span className="reference-title">{ref.title}</span>
                      <span className="relevance-badge">
                        {Math.round((ref.relevance_score || 0.85) * 100)}% match
                      </span>
                    </div>
                    <button className="expand-btn">
                      {expandedRef === `u-${index}` ? '▲' : '▼'}
                    </button>
                  </div>
                  
                  <AnimatePresence>
                    {expandedRef === `u-${index}` ? (
                      <motion.div 
                        className="reference-content-full"
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3 }}
                      >
                        <div className="content-text">{ref.content}</div>
                        <div className="reference-meta">
                          <span className="meta-item">
                            <span className="meta-icon">📁</span>
                            Source: {ref.title}
                          </span>
                        </div>
                      </motion.div>
                    ) : (
                      <div className="reference-content-preview">
                        {truncateContent(ref.content)}
                      </div>
                    )}
                  </AnimatePresence>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* Knowledge Base Section */}
        {knowledgeBase.length > 0 && (
          <div className="reference-section">
            <h3 className="section-title">
              <span className="section-icon">📚</span>
              From Knowledge Base
            </h3>
            <div className="references-list">
              {knowledgeBase.slice(0, showAll ? knowledgeBase.length : 3).map((ref, index) => (
                <motion.div
                  key={`kb-${index}`}
                  className={`reference-item knowledge-base ${expandedRef === `k-${index}` ? 'expanded' : ''}`}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <div 
                    className="reference-header"
                    onClick={() => toggleExpand(`k-${index}`)}
                  >
                    <div className="reference-title-row">
                      <span className="reference-number">{index + 1}</span>
                      <span className="reference-title">{ref.title}</span>
                      {ref.year && (
                        <span className="year-badge">{ref.year}</span>
                      )}
                    </div>
                    <button className="expand-btn">
                      {expandedRef === `k-${index}` ? '▲' : '▼'}
                    </button>
                  </div>
                  
                  <AnimatePresence>
                    {expandedRef === `k-${index}` ? (
                      <motion.div 
                        className="reference-content-full"
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3 }}
                      >
                        <div className="content-text">{ref.content}</div>
                        {ref.key_findings && (
                          <div className="key-findings">
                            <strong>Key Findings:</strong>
                            <ul>
                              {ref.key_findings.map((finding, i) => (
                                <li key={i}>{finding}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        <div className="reference-meta">
                          {ref.authors && (
                            <span className="meta-item">
                              <span className="meta-icon">👤</span>
                              {ref.authors}
                            </span>
                          )}
                          {ref.journal && (
                            <span className="meta-item">
                              <span className="meta-icon">📖</span>
                              {ref.journal}
                            </span>
                          )}
                        </div>
                      </motion.div>
                    ) : (
                      <div className="reference-content-preview">
                        {truncateContent(ref.content)}
                      </div>
                    )}
                  </AnimatePresence>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {results.length > 5 && (
          <button 
            className="show-more-btn"
            onClick={() => setShowAll(!showAll)}
          >
            {showAll ? 'Show Less' : `Show All ${results.length} References`}
          </button>
        )}
      </div>

      <div className="references-footer">
        <div className="rag-info">
          <span className="info-icon">ℹ️</span>
          <span>
            References retrieved using RAG (Retrieval-Augmented Generation) 
            with text-embedding-3-large
          </span>
        </div>
      </div>
    </motion.div>
  );
}

export default References;

