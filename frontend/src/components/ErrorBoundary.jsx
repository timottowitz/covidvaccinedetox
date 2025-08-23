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
    if (msg.includes('metamask')) {
      // swallow extension error
      return;
    }
    // Set fallback only for real app errors
    this.setState({ hasError: true, message: msg || 'Something went wrong' });
    // Optional: console.error('App error:', error, info);
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