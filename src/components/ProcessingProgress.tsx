import { motion } from 'framer-motion';

interface ProcessingProgressProps {
  stage: string;
  message: string;
  progress: number;
  partialSummary?: string;
}

export function ProcessingProgress({
  stage,
  message,
  progress,
  partialSummary,
}: ProcessingProgressProps) {
  const stageIcons: Record<string, string> = {
    extracting: '📄',
    summarizing: '✨',
    formatting: '📝',
    complete: '✅',
    error: '❌',
  };

  return (
    <motion.div
      className="processing-progress"
      role="status"
      aria-live="polite"
      aria-label={`Processing stage: ${message}, ${Math.round(progress)}% complete`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
    >
      <div className="progress-header">
        <motion.span
          className="stage-icon"
          animate={{ scale: [1, 1.1, 1] }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        >
          {stageIcons[stage] || '⏳'}
        </motion.span>
        <h3>{message}</h3>
      </div>

      <div className="progress-bar-container">
        <motion.div
          className="progress-bar-fill"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.3 }}
        />
        <span className="progress-text">{Math.round(progress)}%</span>
      </div>

      {partialSummary && (
        <motion.div
          className="partial-summary"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <h4>Summary (in progress):</h4>
          <p>{partialSummary}</p>
        </motion.div>
      )}
    </motion.div>
  );
}
