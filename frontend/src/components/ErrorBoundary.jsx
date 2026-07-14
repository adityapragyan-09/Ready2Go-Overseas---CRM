import React from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    // Log to monitoring in production
    if (import.meta.env.PROD) {
      console.error('ErrorBoundary caught:', error);
    }
  }

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/dashboard';
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50 p-8">
          <div className="max-w-md w-full bg-white rounded-2xl border border-slate-100 shadow-xl p-8 text-center space-y-6">
            <div className="mx-auto w-16 h-16 rounded-2xl bg-red-50 border border-red-100 flex items-center justify-center">
              <AlertTriangle className="h-8 w-8 text-red-500" />
            </div>

            <div className="space-y-2">
              <h2 className="text-xl font-bold text-slate-800 font-display">Something went wrong</h2>
              <p className="text-sm text-slate-500 leading-relaxed">
                An unexpected error occurred. Our team has been notified.
              </p>
            </div>

            <div className="flex gap-3 justify-center">
              <button
                onClick={this.handleReload}
                className="inline-flex items-center gap-2 px-4 py-2.5 bg-brand-orange text-white font-semibold text-sm rounded-xl hover:bg-brand-orange/90 transition-colors"
              >
                <RefreshCw size={16} />
                Reload Page
              </button>
              <button
                onClick={this.handleGoHome}
                className="inline-flex items-center gap-2 px-4 py-2.5 border border-slate-200 text-slate-700 font-semibold text-sm rounded-xl hover:bg-slate-50 transition-colors"
              >
                <Home size={16} />
                Go to Dashboard
              </button>
            </div>

            {import.meta.env.DEV && this.state.error && (
              <details className="text-left mt-4 p-3 bg-slate-50 rounded-xl border border-slate-100">
                <summary className="text-xs font-bold text-slate-500 cursor-pointer">Error Details</summary>
                <pre className="mt-2 text-xs text-red-600 overflow-auto whitespace-pre-wrap">
                  {this.state.error.toString()}
                </pre>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
