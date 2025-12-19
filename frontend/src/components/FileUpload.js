import React, { useCallback, useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import './FileUpload.css';

const API_URL = process.env.REACT_APP_API_URL || 'https://battery0676.ngrok.app';

function FileUpload({ onUpload, uploadedFiles, onIndexComplete }) {
  const [isUploading, setIsUploading] = useState(false);
  const [isIndexing, setIsIndexing] = useState(false);
  const [pendingDocs, setPendingDocs] = useState([]);
  const [indexedDocs, setIndexedDocs] = useState([]);
  const [indexProgress, setIndexProgress] = useState(null);

  // Fetch document status on mount
  useEffect(() => {
    fetchDocumentStatus();
  }, []);

  const fetchDocumentStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/api/documents/pending`);
      if (response.ok) {
        const data = await response.json();
        setPendingDocs(data.pending || []);
        setIndexedDocs(data.indexed || []);
      }
    } catch (err) {
      console.error('Failed to fetch document status:', err);
    }
  };

  const onDrop = useCallback(async (acceptedFiles) => {
    setIsUploading(true);
    
    for (const file of acceptedFiles) {
      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await fetch(`${API_URL}/api/upload`, {
          method: 'POST',
          body: formData,
        });

        if (response.ok) {
          const data = await response.json();
          if (data.status === 'uploaded') {
            setPendingDocs(prev => [...prev, {
              filename: data.filename,
              file_type: data.file_type,
              file_size: data.file_size,
              status: 'pending'
            }]);
          }
        }
      } catch (err) {
        console.error(`Failed to upload ${file.name}:`, err);
      }
    }
    
    setIsUploading(false);
    // Notify parent if needed
    if (onUpload) {
      onUpload(acceptedFiles);
    }
  }, [onUpload]);

  const handleIndexDocuments = async () => {
    if (pendingDocs.length === 0) return;
    
    setIsIndexing(true);
    setIndexProgress({ current: 0, total: pendingDocs.length });

    try {
      const response = await fetch(`${API_URL}/api/index`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({}), // Index all pending documents
      });

      if (response.ok) {
        const data = await response.json();
        
        // Update lists
        setIndexedDocs(prev => [...prev, ...data.indexed_files]);
        setPendingDocs([]);
        
        setIndexProgress({
          current: data.indexed_count,
          total: data.indexed_count,
          chunks: data.total_chunks,
          message: data.message
        });

        // Notify parent
        if (onIndexComplete) {
          onIndexComplete(data.total_chunks);
        }

        // Clear progress after delay
        setTimeout(() => {
          setIndexProgress(null);
        }, 3000);
      }
    } catch (err) {
      console.error('Failed to index documents:', err);
      setIndexProgress({ error: 'Failed to index documents' });
    } finally {
      setIsIndexing(false);
    }
  };

  const handleRemovePending = async (filename) => {
    try {
      const response = await fetch(`${API_URL}/api/documents/pending/${encodeURIComponent(filename)}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        setPendingDocs(prev => prev.filter(d => d.filename !== filename));
      }
    } catch (err) {
      console.error('Failed to remove document:', err);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      // PDF files - include multiple possible MIME types
      'application/pdf': ['.pdf'],
      'application/x-pdf': ['.pdf'],
      // Text files
      'text/plain': ['.txt'],
      // Word documents
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxSize: 10485760, // 10MB
    // Allow files even if MIME type doesn't match exactly
    validator: (file) => {
      const allowedExtensions = ['.pdf', '.txt', '.doc', '.docx'];
      const ext = '.' + file.name.split('.').pop().toLowerCase();
      if (allowedExtensions.includes(ext)) {
        return null; // Valid
      }
      return {
        code: 'file-invalid-type',
        message: `File type ${ext} not supported`
      };
    }
  });

  return (
    <div className="file-upload-card">
      <div className="card-header">
        <div className="card-icon upload-icon">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 15V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M17 8L12 3L7 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M12 3V15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        <h3>Document Upload & Indexing</h3>
      </div>

      <div 
        {...getRootProps()} 
        className={`dropzone ${isDragActive ? 'active' : ''} ${isUploading ? 'uploading' : ''}`}
      >
        <input {...getInputProps()} />
        {isUploading ? (
          <div className="upload-progress">
            <div className="upload-spinner"></div>
            <p>Uploading documents...</p>
          </div>
        ) : isDragActive ? (
          <p>Drop files here...</p>
        ) : (
          <>
            <div className="dropzone-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M14 2V8H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <p>Drag & drop PDF, DOCX, or TXT files</p>
            <span className="dropzone-hint">or click to browse</span>
          </>
        )}
      </div>

      {/* Pending Documents Section */}
      <AnimatePresence>
        {pendingDocs.length > 0 && (
          <motion.div 
            className="pending-docs-section"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <div className="section-header pending">
              <span className="section-icon">⏳</span>
              <span>Pending Documents ({pendingDocs.length})</span>
            </div>
            <ul className="files-list">
              {pendingDocs.map((doc, index) => (
                <motion.li 
                  key={doc.filename}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="file-item pending"
                >
                  <svg className="file-icon" viewBox="0 0 24 24" fill="none">
                    <path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                  <div className="file-info">
                    <span className="file-name">{doc.filename}</span>
                    <span className="file-meta">
                      {doc.file_type?.toUpperCase().replace('.', '')} • {formatFileSize(doc.file_size)}
                    </span>
                  </div>
                  <button 
                    className="remove-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRemovePending(doc.filename);
                    }}
                    title="Remove from queue"
                  >
                    ✕
                  </button>
                </motion.li>
              ))}
            </ul>
            
            {/* Index Button */}
            <motion.button
              className={`index-button ${isIndexing ? 'indexing' : ''}`}
              onClick={handleIndexDocuments}
              disabled={isIndexing || pendingDocs.length === 0}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              {isIndexing ? (
                <>
                  <div className="button-spinner"></div>
                  <span>Indexing...</span>
                </>
              ) : (
                <>
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                  <span>Index {pendingDocs.length} Document{pendingDocs.length > 1 ? 's' : ''}</span>
                </>
              )}
            </motion.button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Index Progress/Success Message */}
      <AnimatePresence>
        {indexProgress && (
          <motion.div 
            className={`index-progress ${indexProgress.error ? 'error' : 'success'}`}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            {indexProgress.error ? (
              <span>❌ {indexProgress.error}</span>
            ) : (
              <span>✅ {indexProgress.message || `Indexed ${indexProgress.current} documents`}</span>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Indexed Documents Section */}
      <AnimatePresence>
        {indexedDocs.length > 0 && (
          <motion.div 
            className="indexed-docs-section"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <div className="section-header indexed">
              <span className="section-icon">✓</span>
              <span>Indexed Documents ({indexedDocs.length})</span>
            </div>
            <ul className="files-list indexed-list">
              {indexedDocs.slice(-5).reverse().map((doc, index) => (
                <motion.li 
                  key={doc.filename}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="file-item indexed"
                >
                  <svg className="file-icon" viewBox="0 0 24 24" fill="none">
                    <path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                  <div className="file-info">
                    <span className="file-name">{doc.filename}</span>
                    <span className="file-meta">
                      {doc.chunks_created} chunks indexed
                    </span>
                  </div>
                  <span className="file-status-icon success">✓</span>
                </motion.li>
              ))}
              {indexedDocs.length > 5 && (
                <li className="more-files">
                  +{indexedDocs.length - 5} more documents indexed
                </li>
              )}
            </ul>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="upload-info">
        <span>📄 PDF, DOCX & TXT files • Max 10MB • RAG-indexed with text-embedding-3-large</span>
      </div>
    </div>
  );
}

export default FileUpload;
