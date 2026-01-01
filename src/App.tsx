import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { LengthOption, ToneOption } from './types';
import { copyToClipboard } from './utils/clipboard';
import { downloadAsText, downloadAsMarkdown } from './utils/export';
import { useStreamingSummarizer } from './hooks/useStreamingSummarizer';
import { ProcessingProgress } from './components/ProcessingProgress';
import './App.css';

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [lengthOption, setLengthOption] = useState<LengthOption>('Medium');
  const [toneOption, setToneOption] = useState<ToneOption>('Neutral');
  const [isDragging, setIsDragging] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [copyStatus, setCopyStatus] = useState<'idle' | 'copied' | 'error'>('idle');
  const [mousePos, setMousePos] = useState({ x: 50, y: 50 });
  const [showDropdown, setShowDropdown] = useState(false);
  const [showLanding, setShowLanding] = useState(true);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const { processingState, result, error, summarizeStreaming } = useStreamingSummarizer();

  // Helper variables for mutually exclusive conditional rendering
  const isProcessing =
    processingState.stage !== 'idle' &&
    processingState.stage !== 'complete' &&
    processingState.stage !== 'error';
  const isComplete = result !== null && processingState.stage === 'complete';
  const isIdle = result === null && processingState.stage === 'idle';

  const validateFile = (file: File): string | null => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      return 'Only PDF files are supported';
    }
    if (file.size > 10 * 1024 * 1024) {
      return 'File too large (max 10MB)';
    }
    return null;
  };

  const handleFileSelect = (selectedFile: File) => {
    const validationError = validateFile(selectedFile);
    if (!validationError) {
      setFile(selectedFile);
    }
  };

  const getEstimatedTime = (fileSizeBytes: number): string => {
    const sizeMB = fileSizeBytes / (1024 * 1024);
    if (sizeMB < 1) return '~15-30 seconds';
    if (sizeMB < 3) return '~30-60 seconds';
    if (sizeMB < 5) return '~1-2 minutes';
    return '~2-3 minutes';
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) handleFileSelect(droppedFile);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    setMousePos({ x, y });
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) handleFileSelect(selectedFile);
  };

  const handleSummarize = () => {
    if (!file) return;
    summarizeStreaming(file, lengthOption, toneOption);
  };

  const handleCopy = async () => {
    if (!result?.formatted_summary) return;

    const success = await copyToClipboard(result.formatted_summary);
    setCopyStatus(success ? 'copied' : 'error');

    // Reset after 2 seconds
    setTimeout(() => setCopyStatus('idle'), 2000);
  };

  const handleDownloadTxt = () => {
    if (!result || !file) return;
    const baseFilename = file.name.replace('.pdf', '');
    downloadAsText(result, baseFilename);
  };

  const handleDownloadMd = () => {
    if (!result || !file) return;
    const baseFilename = file.name.replace('.pdf', '');
    downloadAsMarkdown(result, baseFilename);
    setShowDropdown(false);
  };

  const handleDownloadTxtClick = () => {
    handleDownloadTxt();
    setShowDropdown(false);
  };

  const handleDownloadMdClick = () => {
    handleDownloadMd();
    setShowDropdown(false);
  };

  const toggleDropdown = () => {
    setShowDropdown(!showDropdown);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    if (showDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showDropdown]);

  return (
    <div className="app">
      {/* Animated background grid */}
      <div className="bg-grid" />

      <AnimatePresence mode="wait">
        {showLanding ? (
          <motion.div
            key="landing"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.5 }}
            className="landing-container"
          >
            {/* Landing Hero */}
            <motion.div
              className="landing-hero"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
            >
              <div className="hero-badge">
                <span className="badge-icon">✨</span>
                <span>AI-Powered Analysis</span>
              </div>

              <h1 className="hero-title">
                <img src="/docsnap.svg" alt="DocSnap" className="hero-logo-icon" />
                <span className="hero-title-highlight">DocSnap</span>
                <br />
                <span className="hero-title-subtitle">Transform PDFs into Clear Summaries</span>
              </h1>

              <p className="hero-description">
                Instantly summarize lengthy PDF documents with advanced AI. Customize length and
                tone to match your needs—perfect for research papers, reports, articles, and
                documentation.
              </p>

              <motion.button
                className="cta-button"
                onClick={() => setShowLanding(false)}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <span className="cta-icon">🚀</span>
                Start Summarizing
                <span className="cta-arrow">→</span>
              </motion.button>
            </motion.div>

            {/* Features Grid */}
            <motion.div
              className="features-grid"
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.4 }}
            >
              <div className="feature-card">
                <div className="feature-icon">🤖</div>
                <h3 className="feature-title">AI-Powered</h3>
                <p className="feature-description">
                  Advanced BART model analyzes and condenses your documents with precision
                </p>
              </div>

              <div className="feature-card">
                <div className="feature-icon">⚡</div>
                <h3 className="feature-title">Instant Results</h3>
                <p className="feature-description">
                  Real-time processing with progress tracking—see your summary come to life
                </p>
              </div>

              <div className="feature-card">
                <div className="feature-icon">🎨</div>
                <h3 className="feature-title">Fully Customizable</h3>
                <p className="feature-description">
                  Choose summary length (Short, Medium, Long) and tone (Neutral, Professional,
                  Casual)
                </p>
              </div>

              <div className="feature-card">
                <div className="feature-icon">📊</div>
                <h3 className="feature-title">Smart Export</h3>
                <p className="feature-description">
                  Copy to clipboard or download as TXT/Markdown for easy sharing and integration
                </p>
              </div>
            </motion.div>

            {/* Requirements Section */}
            <motion.div
              className="requirements-section"
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.6 }}
            >
              <h3 className="requirements-title">What You Need to Know</h3>
              <div className="requirements-grid">
                <div className="requirement-item">
                  <span className="requirement-icon">📄</span>
                  <div>
                    <strong>PDF Files Only</strong>
                    <p>Upload standard PDF documents with extractable text</p>
                  </div>
                </div>
                <div className="requirement-item">
                  <span className="requirement-icon">💾</span>
                  <div>
                    <strong>Max 10MB Size</strong>
                    <p>Keep files under 10MB for optimal processing speed</p>
                  </div>
                </div>
                <div className="requirement-item">
                  <span className="requirement-icon">📝</span>
                  <div>
                    <strong>Text-Based PDFs</strong>
                    <p>Works best with text PDFs, not scanned images</p>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        ) : (
          <motion.div
            key="main"
            initial={{ opacity: 0, scale: 1.05 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
            className="container"
          >
            {/* Header */}
            <motion.header
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="header"
            >
              <button
                className="back-button"
                onClick={() => setShowLanding(true)}
                aria-label="Back to landing page"
              >
                <span className="back-arrow">←</span>
                <span className="back-text">Back</span>
              </button>
              <h1 className="title">
                <img src="/docsnap.svg" alt="DocSnap" className="title-icon" />
                DocSnap
              </h1>
              <p className="subtitle">
                Transform lengthy documents into concise, readable summaries with customizable
                length and tone.
              </p>
            </motion.header>

            {/* Quick Tips Card - Full Width */}
            <motion.div
              className="tips-card-fullwidth"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.5 }}
            >
              <div className="tips-header">
                <span className="tips-icon">💡</span>
                <h3 className="tips-title">Quick Tips</h3>
              </div>
              <div className="tips-list-horizontal">
                <motion.div
                  className="tip-item"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3, duration: 0.4 }}
                >
                  <div className="tip-icon-wrapper">
                    <span className="tip-emoji">🎓</span>
                  </div>
                  <div className="tip-content">
                    <h4 className="tip-title">Professional Tone</h4>
                    <p className="tip-description">Best for academic papers and reports</p>
                  </div>
                </motion.div>
                <motion.div
                  className="tip-item"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.4, duration: 0.4 }}
                >
                  <div className="tip-icon-wrapper">
                    <span className="tip-emoji">✍️</span>
                  </div>
                  <div className="tip-content">
                    <h4 className="tip-title">Casual Tone</h4>
                    <p className="tip-description">Perfect for blog posts and articles</p>
                  </div>
                </motion.div>
                <motion.div
                  className="tip-item"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.5, duration: 0.4 }}
                >
                  <div className="tip-icon-wrapper">
                    <span className="tip-emoji">⚡</span>
                  </div>
                  <div className="tip-content">
                    <h4 className="tip-title">Short Summaries</h4>
                    <p className="tip-description">Quick overviews (1-2 paragraphs)</p>
                  </div>
                </motion.div>
                <motion.div
                  className="tip-item"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.6, duration: 0.4 }}
                >
                  <div className="tip-icon-wrapper">
                    <span className="tip-emoji">📊</span>
                  </div>
                  <div className="tip-content">
                    <h4 className="tip-title">Long Summaries</h4>
                    <p className="tip-description">Comprehensive analysis (3-5 para )</p>
                  </div>
                </motion.div>
              </div>
            </motion.div>

            <div className="main-grid">
              {/* Left Panel: Upload & Controls */}
              <motion.div
                initial={{ opacity: 0, x: -30 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6, delay: 0.1 }}
                className="controls-panel"
              >
                {/* File Upload Zone */}
                <div className="section">
                  <h3 className="section-label">Document Upload</h3>
                  <div
                    className={`upload-zone ${isDragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onMouseMove={handleMouseMove}
                    onClick={() => fileInputRef.current?.click()}
                    style={
                      {
                        '--mouse-x': `${mousePos.x}%`,
                        '--mouse-y': `${mousePos.y}%`,
                      } as React.CSSProperties
                    }
                    role="button"
                    tabIndex={0}
                    onKeyDown={e => e.key === 'Enter' && fileInputRef.current?.click()}
                    aria-label="Upload PDF file"
                  >
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".pdf,application/pdf"
                      onChange={handleFileInputChange}
                      style={{ display: 'none' }}
                      aria-label="File input"
                    />

                    {file ? (
                      <motion.div
                        className="file-info"
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                      >
                        <div className="file-icon">📎</div>
                        <div className="file-details">
                          <div className="file-name">{file.name}</div>
                          <div className="file-metadata">
                            <span className="file-size">{formatFileSize(file.size)}</span>
                            <span className="file-separator">•</span>
                            <span className="file-time">{getEstimatedTime(file.size)}</span>
                          </div>
                        </div>
                        <button
                          className="file-remove"
                          onClick={e => {
                            e.stopPropagation();
                            setFile(null);
                          }}
                          aria-label="Remove file"
                        >
                          ✕
                        </button>
                      </motion.div>
                    ) : (
                      <div className="upload-prompt">
                        <div className="upload-icon">↑</div>
                        <div className="upload-text">
                          <span className="upload-primary">Drop PDF here or click to browse</span>
                          <span className="upload-secondary">Maximum file size: 10MB</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Summary Options */}
                <div className="section">
                  <h3 className="section-label">Summary Options</h3>
                  <div className="options-grid">
                    <div className="option-group">
                      <label htmlFor="length" className="option-label">
                        Length
                      </label>
                      <select
                        id="length"
                        className="select"
                        value={lengthOption}
                        onChange={e => setLengthOption(e.target.value as LengthOption)}
                      >
                        <option value="Short">Short</option>
                        <option value="Medium">Medium</option>
                        <option value="Long">Long</option>
                      </select>
                    </div>

                    <div className="option-group">
                      <label htmlFor="tone" className="option-label">
                        Tone
                      </label>
                      <select
                        id="tone"
                        className="select"
                        value={toneOption}
                        onChange={e => setToneOption(e.target.value as ToneOption)}
                      >
                        <option value="Neutral">Neutral</option>
                        <option value="Professional">Professional</option>
                        <option value="Casual">Casual</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Summarize Button */}
                <button
                  className="btn-primary"
                  onClick={handleSummarize}
                  disabled={
                    !file ||
                    (processingState.stage !== 'idle' &&
                      processingState.stage !== 'complete' &&
                      processingState.stage !== 'error')
                  }
                  aria-label="Summarize document"
                >
                  {processingState.stage !== 'idle' &&
                  processingState.stage !== 'complete' &&
                  processingState.stage !== 'error' ? (
                    <>
                      <span className="loading-spinner" />
                      Processing...
                    </>
                  ) : (
                    'Summarize Document'
                  )}
                </button>

                {/* Error Display */}
                <AnimatePresence>
                  {error && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="error-message"
                    >
                      <span className="error-icon">⚠</span>
                      {error}
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>

              {/* Right Panel: Results */}
              <AnimatePresence mode="wait" initial={false}>
                {/* Show progress during processing */}
                {isProcessing && (
                  <ProcessingProgress
                    key="processing"
                    stage={processingState.stage}
                    message={processingState.message}
                    progress={processingState.progress}
                    partialSummary={processingState.partialSummary}
                  />
                )}

                {/* Show results when complete */}
                {isComplete && (
                  <motion.div
                    key="result"
                    initial={{ opacity: 0, x: 30, scale: 0.98 }}
                    animate={{ opacity: 1, x: 0, scale: 1 }}
                    exit={{ opacity: 0, x: -30, scale: 0.98 }}
                    transition={{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
                    className="results-panel"
                  >
                    <div className="section">
                      <div className="section-header">
                        <h3 className="section-label">Summary</h3>
                        <span className="badge">
                          {lengthOption} · {toneOption}
                        </span>
                      </div>

                      <motion.div
                        className="summary-content"
                        initial="hidden"
                        animate="visible"
                        variants={{
                          hidden: {},
                          visible: {
                            transition: {
                              staggerChildren: 0.08,
                              delayChildren: 0.1,
                            },
                          },
                        }}
                      >
                        {result.formatted_summary.split('\n\n').map((paragraph, idx) => (
                          <motion.p
                            key={idx}
                            className="summary-paragraph"
                            variants={{
                              hidden: { opacity: 0, y: 20 },
                              visible: { opacity: 1, y: 0 },
                            }}
                            transition={{ duration: 0.5 }}
                          >
                            {paragraph}
                          </motion.p>
                        ))}
                      </motion.div>

                      {/* Action Buttons */}
                      <div className="summary-actions">
                        <button
                          className="btn-copy"
                          onClick={handleCopy}
                          data-copied={copyStatus === 'copied'}
                          aria-label="Copy summary to clipboard"
                        >
                          <span className="icon">{copyStatus === 'copied' ? '✓' : '📋'}</span>
                          {copyStatus === 'copied' ? 'Copied!' : 'Copy Summary'}
                        </button>

                        <div className="dropdown" ref={dropdownRef}>
                          <button
                            className="btn-download"
                            onClick={toggleDropdown}
                            aria-label="Download summary"
                            aria-expanded={showDropdown}
                          >
                            <span className="icon">⬇️</span>
                            Download
                          </button>
                          {showDropdown && (
                            <div className="dropdown-menu">
                              <button onClick={handleDownloadTxtClick}>Download as TXT</button>
                              <button onClick={handleDownloadMdClick}>Download as Markdown</button>
                            </div>
                          )}
                        </div>

                        {copyStatus === 'error' && (
                          <span className="copy-error">Failed to copy</span>
                        )}
                      </div>
                    </div>

                    {/* Extracted Text Preview */}
                    <div className="section">
                      <button
                        className="collapsible-header"
                        onClick={() => setShowPreview(!showPreview)}
                        aria-expanded={showPreview}
                        aria-controls="text-preview"
                      >
                        <span className="section-label">Extracted Text Preview</span>
                        <span className={`collapse-icon ${showPreview ? 'open' : ''}`}>▼</span>
                      </button>

                      <AnimatePresence>
                        {showPreview && (
                          <motion.div
                            id="text-preview"
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.3 }}
                            className="preview-content"
                          >
                            <pre className="preview-text">{result.extracted_text_preview}</pre>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  </motion.div>
                )}

                {/* Show placeholder only when idle */}
                {isIdle && (
                  <motion.div
                    key="placeholder"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="results-placeholder"
                  >
                    <div className="placeholder-content">
                      <div className="placeholder-icon">✨</div>
                      <p className="placeholder-text">
                        Your summary will appear here once processing is complete
                      </p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default App;
