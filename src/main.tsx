import React from 'react';
import ReactDOM from 'react-dom/client';
import * as Sentry from '@sentry/react';
import App from './App.tsx';

// Initialize Sentry for error tracking (production only)
const SENTRY_DSN = import.meta.env.VITE_SENTRY_DSN;
if (SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration({
        maskAllText: false,
        blockAllMedia: false,
      }),
    ],
    // Performance Monitoring
    tracesSampleRate: 0.1, // Capture 10% of transactions for performance monitoring
    tracePropagationTargets: ['localhost', /^https:\/\/.*\.vercel\.app/],

    // Session Replay
    replaysSessionSampleRate: 0.1, // Sample 10% of sessions for replay
    replaysOnErrorSampleRate: 1.0, // Capture 100% of sessions with errors

    environment: import.meta.env.MODE, // 'development' or 'production'
    enabled: import.meta.env.MODE === 'production', // Only enable in production
  });
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
