import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";

// Filter noisy runtime errors from injected browser extensions (e.g., MetaMask)
if (typeof window !== 'undefined') {
  const isNoise = (msg) => {
    const s = String(msg || '').toLowerCase();
    return s.includes('metamask') || s.includes('chrome-extension') || s.includes("ws://localhost:443/ws");
  };
  window.addEventListener('error', (e) => {
    const msg = (e && (e.message || (e.error && e.error.message))) || '';
    if (isNoise(msg)) {
      e.preventDefault();
    }
  });
  window.addEventListener('unhandledrejection', (e) => {
    const reason = (e && (e.reason && (e.reason.message || e.reason))) || '';
    if (isNoise(reason)) {
      e.preventDefault();
    }
  });
}


const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
