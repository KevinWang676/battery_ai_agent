import React from 'react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import './Summary.css';

function Summary({ summary, processingTime }) {
  return (
    <motion.div 
      className="summary-card"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="summary-header">
        <div className="summary-icon">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M9 5H7C5.89543 5 5 5.89543 5 7V19C5 20.1046 5.89543 21 7 21H17C18.1046 21 19 20.1046 19 19V7C19 5.89543 18.1046 5 17 5H15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M9 5C9 3.89543 9.89543 3 11 3H13C14.1046 3 15 3.89543 15 5C15 6.10457 14.1046 7 13 7H11C9.89543 7 9 6.10457 9 5Z" stroke="currentColor" strokeWidth="2"/>
            <path d="M9 12H15" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            <path d="M9 16H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </div>
        <div>
          <h2>Analysis Summary</h2>
          <span className="processing-time">Completed in {processingTime}s</span>
        </div>
      </div>

      <div className="summary-content">
        <ReactMarkdown>{summary}</ReactMarkdown>
      </div>

      <div className="summary-footer">
        <div className="powered-by">
          <span>🤖</span>
          <span>Multi-Agent Analysis powered by GPT-4.1</span>
        </div>
      </div>
    </motion.div>
  );
}

export default Summary;



