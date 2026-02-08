"use client";

import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  // Check if this is an auth-related error
  const isAuthError = 
    error.message?.includes('Refresh Token') ||
    error.message?.includes('refresh_token') ||
    error.message?.includes('AuthApiError') ||
    error.message?.includes('session') ||
    error.message?.includes('JWT') ||
    error.message?.includes('token');

  useEffect(() => {
    console.error("Global error:", error);
    
    // Auto-redirect to login for auth errors
    if (isAuthError && typeof window !== 'undefined') {
      const timeout = setTimeout(() => {
        window.location.href = '/login';
      }, 3000);
      return () => clearTimeout(timeout);
    }
  }, [error, isAuthError]);

  const handleLogin = () => {
    if (typeof window !== 'undefined') {
      window.location.href = '/logout';
    }
  };

  const handleRetry = () => {
    reset();
  };

  return (
    <html lang="en">
      <body style={{ margin: 0, fontFamily: 'system-ui, -apple-system, sans-serif', backgroundColor: '#fafafa' }}>
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '16px',
          boxSizing: 'border-box',
        }}>
          <div style={{
            width: '100%',
            maxWidth: '400px',
            textAlign: 'center',
          }}>
            {/* Error Icon */}
            <div style={{
              display: 'flex',
              justifyContent: 'center',
              marginBottom: '24px',
            }}>
              <div style={{
                width: '64px',
                height: '64px',
                borderRadius: '50%',
                backgroundColor: '#fee2e2',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}>
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#dc2626" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="12" y1="8" x2="12" y2="12"/>
                  <line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
              </div>
            </div>

            {/* Title */}
            <h1 style={{
              fontSize: '24px',
              fontWeight: 'bold',
              color: '#111',
              margin: '0 0 12px 0',
            }}>
              {isAuthError ? 'Session Expired' : 'Something went wrong'}
            </h1>

            {/* Description */}
            <p style={{
              fontSize: '14px',
              color: '#666',
              margin: '0 0 24px 0',
              padding: '0 16px',
              lineHeight: '1.5',
            }}>
              {isAuthError 
                ? 'Your session has expired. Please sign in again to continue.'
                : 'An unexpected error occurred. Please try again.'}
            </p>

            {/* Buttons */}
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
              padding: '0 16px',
            }}>
              {isAuthError ? (
                <>
                  <button
                    onClick={handleLogin}
                    style={{
                      width: '100%',
                      padding: '12px 24px',
                      fontSize: '16px',
                      fontWeight: '500',
                      color: '#fff',
                      backgroundColor: '#000',
                      border: 'none',
                      borderRadius: '8px',
                      cursor: 'pointer',
                    }}
                  >
                    Sign In Again
                  </button>
                  <p style={{
                    fontSize: '12px',
                    color: '#999',
                    margin: 0,
                  }}>
                    Redirecting automatically in 3 seconds...
                  </p>
                </>
              ) : (
                <>
                  <button
                    onClick={handleRetry}
                    style={{
                      width: '100%',
                      padding: '12px 24px',
                      fontSize: '16px',
                      fontWeight: '500',
                      color: '#fff',
                      backgroundColor: '#000',
                      border: 'none',
                      borderRadius: '8px',
                      cursor: 'pointer',
                    }}
                  >
                    Try Again
                  </button>
                  <button
                    onClick={() => { if (typeof window !== 'undefined') window.location.href = '/'; }}
                    style={{
                      width: '100%',
                      padding: '12px 24px',
                      fontSize: '16px',
                      fontWeight: '500',
                      color: '#000',
                      backgroundColor: '#fff',
                      border: '1px solid #ddd',
                      borderRadius: '8px',
                      cursor: 'pointer',
                    }}
                  >
                    Go Home
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </body>
    </html>
  );
}
