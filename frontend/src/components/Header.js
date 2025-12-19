import React from 'react';
import { motion } from 'framer-motion';
import './Header.css';

function Header({ documentsCount }) {
  return (
    <header className="header">
      <div className="header-content">
        <motion.div 
          className="logo"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="logo-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M7 20V4H17V20H7Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M10 1V4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              <path d="M14 1V4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              <path d="M10 20V23" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              <path d="M14 20V23" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              <path d="M10 9H14" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              <path d="M12 9V15" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </div>
          <span className="logo-text">ElectroLab</span>
        </motion.div>

        <motion.nav 
          className="nav"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <div className="nav-item">
            <span className="nav-label">Agents</span>
            <span className="nav-badge active">5 Active</span>
          </div>
          <div className="nav-divider"></div>
          <div className="nav-item">
            <span className="nav-label">Documents</span>
            <span className="nav-badge">{documentsCount} Indexed</span>
          </div>
        </motion.nav>

        <motion.div 
          className="header-actions"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="status-indicator">
            <span className="status-dot"></span>
            <span>System Online</span>
          </div>
        </motion.div>
      </div>
    </header>
  );
}

export default Header;



