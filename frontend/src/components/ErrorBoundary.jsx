import React from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props){
    super(props);
    this.state = { hasError: false, message: '', error: null };
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
    
    // Log error to console for debugging
    console.error('App error caught by ErrorBoundary:', error, info);
    
    // Set fallback only for real app errors
    this.setState({ 
      hasError: true, 
      message: error.message || 'Something went wrong',
      error: error
    });
  }
  
  handleRetry = () => {
    this.setState({ hasError: false, message: '', error: null });
  };
  
  handleReload = () => {
    window.location.reload();
  };
  
  render(){
    if (this.state.hasError){
      return (
        <div className="container" style={{padding: 40, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px'}}>
          <Card style={{maxWidth: '500px', width: '100%'}}>
            <CardHeader style={{textAlign: 'center'}}>
              <div style={{display: 'flex', justifyContent: 'center', marginBottom: '16px'}}>
                <AlertTriangle size={48} style={{color: '#f59e0b'}} />
              </div>
              <CardTitle style={{fontSize: '1.5rem', marginBottom: '8px'}}>
                Oops! Something went wrong
              </CardTitle>
            </CardHeader>
            <CardContent style={{textAlign: 'center'}}>
              <p style={{color: '#64748b', marginBottom: '24px', lineHeight: '1.5'}}>
                We encountered an unexpected error. This has been logged for investigation.
              </p>
              {process.env.NODE_ENV === 'development' && (
                <details style={{marginBottom: '24px', textAlign: 'left'}}>
                  <summary style={{cursor: 'pointer', color: '#64748b', fontSize: '0.875rem'}}>
                    Technical Details (Development)
                  </summary>
                  <pre style={{
                    marginTop: '8px', 
                    padding: '12px', 
                    backgroundColor: '#f8fafc', 
                    borderRadius: '6px',
                    fontSize: '0.75rem',
                    overflow: 'auto',
                    color: '#e11d48'
                  }}>
                    {this.state.message}
                  </pre>
                </details>
              )}
              <div style={{display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap'}}>
                <Button 
                  onClick={this.handleRetry}
                  style={{display: 'flex', alignItems: 'center', gap: '8px'}}
                >
                  <RefreshCw size={16} />
                  Try Again
                </Button>
                <Button 
                  variant="outline" 
                  onClick={this.handleReload}
                >
                  Reload Page
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      );
    }
    return this.props.children;
  }
}