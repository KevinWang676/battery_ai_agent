import React, { useState } from 'react';
import './DemoBanner.css';

function DemoBanner() {
  const [isVisible, setIsVisible] = useState(true);

  if (!isVisible) return null;

  return (
    <div className="demo-banner">
      <div className="demo-content">
        <span className="demo-icon">🧪</span>
        <div className="demo-text">
          <strong>Demo Version</strong> — This is a demonstration deployment. 
          The backend API is not connected in this hosted version.
          <a 
            href="https://github.com/KevinWang676/battery_ai_agent" 
            target="_blank" 
            rel="noopener noreferrer"
            className="demo-link"
          >
            Deploy locally via GitHub →
          </a>
        </div>
        <button 
          className="demo-close" 
          onClick={() => setIsVisible(false)}
          aria-label="Close banner"
        >
          ×
        </button>
      </div>
    </div>
  );
}

export default DemoBanner;

