import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";

// Filter noisy runtime errors from injected browser extensions (e.g., MetaMask)
if (typeof window !== 'undefined') {
  const isNoise = (msg) => {
    const s = String(msg || '').toLowerCase();
    return s.includes('metamask') || 
           s.includes('chrome-extension') || 
           s.includes("ws://localhost:443/ws") ||
           s.includes('failed to connect to metamask') ||
           s.includes('ethereum') ||
           s.includes('web3') ||
           s.includes('wallet') ||
           s.includes('nkbihfbeogaeaoehlefnkodbefgpgknn') ||  // MetaMask extension ID
           s.includes('scripts/inpage.js') ||                 // MetaMask script
           s.includes('connect') && s.includes('metamask');   // Connect to MetaMask
  };
  
  // Handle script errors
  window.addEventListener('error', (e) => {
    const msg = (e && (e.message || (e.error && e.error.message))) || '';
    if (isNoise(msg)) {
      e.preventDefault();
      e.stopPropagation();
      return false;
    }
  });
  
  // Handle promise rejections
  window.addEventListener('unhandledrejection', (e) => {
    const reason = (e && (e.reason && (e.reason.message || e.reason))) || '';
    if (isNoise(reason)) {
      e.preventDefault();
      e.stopPropagation();
      return false;
    }
  });
  
  // Override console.error to filter MetaMask noise in development
  if (process.env.NODE_ENV === 'development') {
    const originalError = console.error;
    console.error = (...args) => {
      const message = args.join(' ');
      if (!isNoise(message)) {
        originalError.apply(console, args);
      }
    };
    
    // Override React error reporting for development overlay
    if (window.__REACT_ERROR_OVERLAY_GLOBAL_HOOK__) {
      const originalCaptureConsoleMessages = window.__REACT_ERROR_OVERLAY_GLOBAL_HOOK__.onUnhandledError;
      window.__REACT_ERROR_OVERLAY_GLOBAL_HOOK__.onUnhandledError = (error) => {
        const msg = String(error && error.message || '').toLowerCase();
        if (!isNoise(msg)) {
          originalCaptureConsoleMessages && originalCaptureConsoleMessages(error);
        }
      };
    }
  }
}


const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
