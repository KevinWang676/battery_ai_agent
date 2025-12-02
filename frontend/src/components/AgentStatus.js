import React from 'react';
import { motion } from 'framer-motion';
import './AgentStatus.css';

const agents = [
  { 
    id: 'orchestrator', 
    name: 'Orchestrator', 
    description: 'Coordinates all agents',
    icon: '🎯',
    color: '#00d4ff'
  },
  { 
    id: 'literature', 
    name: 'Literature & RAG', 
    description: 'Searches papers',
    icon: '📚',
    color: '#7c3aed'
  },
  { 
    id: 'property', 
    name: 'Property & Compat', 
    description: 'Checks constraints',
    icon: '⚗️',
    color: '#22d3ee'
  },
  { 
    id: 'prediction', 
    name: 'Performance', 
    description: 'Predicts metrics',
    icon: '📊',
    color: '#10b981'
  },
  { 
    id: 'planning', 
    name: 'Experiment', 
    description: 'Plans experiments',
    icon: '🧪',
    color: '#f59e0b'
  },
];

function AgentStatus({ isProcessing }) {
  return (
    <div className="agent-status-card">
      <div className="card-header">
        <div className="card-icon agent-icon">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="2"/>
            <path d="M12 1V3" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            <path d="M12 21V23" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            <path d="M4.22 4.22L5.64 5.64" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            <path d="M18.36 18.36L19.78 19.78" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            <path d="M1 12H3" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            <path d="M21 12H23" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            <path d="M4.22 19.78L5.64 18.36" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            <path d="M18.36 5.64L19.78 4.22" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </div>
        <div>
          <h3>Agent Network</h3>
          <span className="agent-model">Powered by GPT-4.1</span>
        </div>
      </div>

      <div className="agents-list">
        {agents.map((agent, index) => (
          <motion.div 
            key={agent.id}
            className={`agent-item ${isProcessing ? 'processing' : ''}`}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <div 
              className="agent-indicator" 
              style={{ 
                '--agent-color': agent.color,
                animationDelay: `${index * 0.2}s`
              }}
            >
              <span className="agent-emoji">{agent.icon}</span>
            </div>
            <div className="agent-info">
              <span className="agent-name">{agent.name}</span>
              <span className="agent-desc">{agent.description}</span>
            </div>
            <div className={`agent-status-dot ${isProcessing ? 'active' : 'idle'}`}></div>
          </motion.div>
        ))}
      </div>

      <div className="status-footer">
        <div className="status-row">
          <span className="status-label">Status</span>
          <span className={`status-value ${isProcessing ? 'processing' : 'ready'}`}>
            {isProcessing ? 'Processing' : 'Ready'}
          </span>
        </div>
        <div className="status-row">
          <span className="status-label">Model</span>
          <span className="status-value model">GPT-4.1</span>
        </div>
        <div className="status-row">
          <span className="status-label">Embeddings</span>
          <span className="status-value embeddings">text-embedding-3-large</span>
        </div>
      </div>
    </div>
  );
}

export default AgentStatus;

