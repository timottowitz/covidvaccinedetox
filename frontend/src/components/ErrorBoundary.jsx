import React from 'react';

export default class ErrorBoundary extends React.Component {
  constructor(props){
    super(props);
    this.state = { hasError: false, message: '' };
  }
  // Do not set error state here; we filter in componentDidCatch to avoid false positives from extensions
  static getDerivedStateFromError(error){
    return null;
  }
  componentDidCatch(error, info){
    // Ignore noisy browser extensions (e.g., MetaMask)
    const msg = String((error && error.message) || '').toLowerCase();
    const stackTrace = String((error && error.stack) || '').toLowerCase();
    
    if (msg.includes('metamask') || 
        msg.includes('failed to connect to metamask') ||
        msg.includes('ethereum') ||
        msg.includes('web3') ||
        msg.includes('wallet') ||
        stackTrace.includes('chrome-extension') ||
        stackTrace.includes('metamask')) {
      // swallow extension error
      console.log('Suppressed browser extension error:', error.message);
      return;
    }
    
    // Set fallback only for real app errors
    this.setState({ hasError: true, message: msg || 'Something went wrong' });
    console.error('App error:', error, info);
  }
  render(){
    if (this.state.hasError){
      return (
        <div className="container" style={{padding:24}}>
          <div className="card-meta" style={{marginBottom:8}}>Oops, something went wrong.</div>
          <div className="card-meta">{this.state.message}</div>
        </div>
      );
    }
    return this.props.children;
  }
}