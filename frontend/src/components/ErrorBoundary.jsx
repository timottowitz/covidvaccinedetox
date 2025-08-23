import React from 'react';

export default class ErrorBoundary extends React.Component {
  constructor(props){
    super(props);
    this.state = { hasError: false, message: '' };
  }
  static getDerivedStateFromError(error){
    return { hasError: true, message: String(error && error.message ? error.message : 'Something went wrong') };
  }
  componentDidCatch(error, info){
    // Ignore noisy browser extensions (e.g., MetaMask) that throw global errors
    const msg = String(error && error.message || '').toLowerCase();
    if (msg.includes('metamask')) {
      // swallow
      return;
    }
    // You can add logging here if needed
    // console.error('App error:', error, info);
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