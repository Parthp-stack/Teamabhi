import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { authService } from '../services/authService';
import AdaptiveLogo from '../components/AdaptiveLogo';
import { Lock, Eye, EyeOff, CheckCircle2, AlertCircle, ArrowRight, ShieldCheck } from 'lucide-react';
import './Login.css';

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const navigate = useNavigate();

  // Verification state
  const [verifying, setVerifying] = useState(true);
  const [verifiedAccount, setVerifiedAccount] = useState(null);
  const [tokenError, setTokenError] = useState('');

  // Password form states
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState('');
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    async function validateToken() {
      if (!token) {
        setTokenError('No reset token was provided in the link. Please request a new password reset link.');
        setVerifying(false);
        return;
      }

      try {
        const data = await authService.verifyResetToken(token);
        if (data && data.valid) {
          setVerifiedAccount(data);
        } else {
          setTokenError('This password reset link is invalid or has expired.');
        }
      } catch (err) {
        const msg = err.response?.data?.detail;
        if (msg === 'Reset link expired') {
          setTokenError('This password reset link has expired. Reset links are valid for 15 minutes.');
        } else if (msg === 'Reset link already used') {
          setTokenError('This password reset link has already been used. Please request a new link.');
        } else {
          setTokenError(msg || 'Invalid or expired password reset link.');
        }
      } finally {
        setVerifying(false);
      }
    }

    validateToken();
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError('');

    if (!newPassword || newPassword.length < 6) {
      setFormError('New password must be at least 6 characters long.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setFormError('Passwords do not match. Please re-enter.');
      return;
    }

    setSubmitting(true);
    try {
      const res = await authService.resetPassword({
        token,
        new_password: newPassword,
        confirm_password: confirmPassword
      });

      if (res && res.success) {
        setSuccess(true);
      } else {
        setFormError(res?.message || 'Password reset failed. Please try again.');
      }
    } catch (err) {
      const msg = err.response?.data?.detail;
      setFormError(msg || 'Password reset failed. The link may have expired.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="login-page-container">
      {/* Top Navbar */}
      <header className="login-navbar">
        <Link to="/login" className="login-nav-logo" style={{ textDecoration: 'none' }}>
          <AdaptiveLogo size={42} light={true} />
          <div className="login-nav-logo-text">
            <span className="login-nav-brand">
              Adapt<span>IQ</span>
            </span>
            <span className="login-nav-tagline">
              Adaptive Assessment & Learning Platform
            </span>
          </div>
        </Link>
        <Link to="/login" className="login-nav-link" style={{ textDecoration: 'none' }}>
          Return to Sign In
        </Link>
      </header>

      {/* Main Container */}
      <main className="login-main-content" style={{ justifyContent: 'center', alignItems: 'center', minHeight: 'calc(100vh - 120px)' }}>
        <div className="login-white-card" style={{ maxWidth: '480px', width: '100%', margin: '0 auto' }}>
          {/* Header */}
          <div className="login-card-header" style={{ textAlign: 'center' }}>
            <div style={{ display: 'inline-flex', justifyContent: 'center', marginBottom: '12px' }}>
              <AdaptiveLogo size={48} light={false} />
            </div>
            <h2 className="login-card-welcome-title">Set New Password</h2>
            <p className="login-card-welcome-subtitle">
              Choose a secure new password for your AdaptIQ account.
            </p>
          </div>

          {/* Loading validation */}
          {verifying && (
            <div style={{ textAlign: 'center', padding: '32px 0', color: '#64748b' }}>
              <div style={{ marginBottom: '12px', fontSize: '14px', fontWeight: 600 }}>Verifying reset link...</div>
              <div style={{ fontSize: '12px', color: '#94a3b8' }}>Please wait while we validate your security token.</div>
            </div>
          )}

          {/* Token Error State */}
          {!verifying && tokenError && (
            <div>
              <div className="login-alert login-alert-error" style={{ marginBottom: '20px' }}>
                <AlertCircle size={18} />
                <span>{tokenError}</span>
              </div>
              <p style={{ fontSize: '13.5px', color: '#64748b', lineHeight: 1.5, marginBottom: '20px' }}>
                For security, password reset links are single-use and expire after 15 minutes. Please return to the login page to request a fresh reset link.
              </p>
              <button
                type="button"
                onClick={() => navigate('/login')}
                className="login-submit-btn"
                style={{ width: '100%' }}
              >
                <span>Request New Reset Link</span>
                <ArrowRight size={18} />
              </button>
            </div>
          )}

          {/* Success State */}
          {!verifying && !tokenError && success && (
            <div style={{ textAlign: 'center', padding: '16px 0' }}>
              <div style={{
                width: '60px',
                height: '60px',
                borderRadius: '50%',
                background: '#ecfdf5',
                color: '#059669',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 16px auto',
                border: '2px solid #a7f3d0'
              }}>
                <CheckCircle2 size={36} />
              </div>
              <h3 style={{ margin: '0 0 8px 0', fontSize: '20px', fontWeight: 800, color: '#0f172a' }}>
                Password Reset Successful!
              </h3>
              <p style={{ fontSize: '14px', color: '#475569', margin: '0 0 24px 0', lineHeight: 1.5 }}>
                Your password has been updated in the database. You can now sign in using your new password.
              </p>
              <button
                type="button"
                onClick={() => navigate('/login')}
                className="login-submit-btn"
                style={{ width: '100%' }}
              >
                <span>Sign In to AdaptIQ</span>
                <ArrowRight size={18} />
              </button>
            </div>
          )}

          {/* Reset Password Form */}
          {!verifying && !tokenError && !success && (
            <form onSubmit={handleSubmit}>
              {/* Account Badge */}
              {verifiedAccount && (
                <div className="forgot-verified-badge" style={{ marginBottom: '18px' }}>
                  <ShieldCheck size={20} color="#059669" />
                  <div>
                    <div style={{ fontWeight: 700, color: '#166534' }}>
                      {verifiedAccount.name}
                      <span className={`forgot-role-tag ${verifiedAccount.role === 'TRAINER' ? 'trainer' : 'student'}`}>
                        {verifiedAccount.role}
                      </span>
                    </div>
                    <div style={{ fontSize: '12px', color: '#15803d' }}>{verifiedAccount.email}</div>
                  </div>
                </div>
              )}

              {formError && (
                <div className="login-alert login-alert-error" style={{ marginBottom: '16px' }}>
                  <AlertCircle size={16} />
                  <span>{formError}</span>
                </div>
              )}

              <div className="login-form-group">
                <label className="login-form-label">New Password</label>
                <div className="login-input-wrapper">
                  <Lock size={18} className="login-input-icon" />
                  <input
                    type={showNewPassword ? 'text' : 'password'}
                    placeholder="At least 6 characters"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                    className="login-input-field"
                    autoFocus
                  />
                  <button
                    type="button"
                    className="login-password-toggle"
                    onClick={() => setShowNewPassword(!showNewPassword)}
                    tabIndex="-1"
                  >
                    {showNewPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              <div className="login-form-group">
                <label className="login-form-label">Confirm New Password</label>
                <div className="login-input-wrapper">
                  <Lock size={18} className="login-input-icon" />
                  <input
                    type={showConfirmPassword ? 'text' : 'password'}
                    placeholder="Re-enter new password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    className="login-input-field"
                  />
                  <button
                    type="button"
                    className="login-password-toggle"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    tabIndex="-1"
                  >
                    {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="login-submit-btn"
                style={{ marginTop: '16px', width: '100%' }}
              >
                <span>{submitting ? 'Updating Password...' : 'Reset Password'}</span>
                {!submitting && <ArrowRight size={18} />}
              </button>

              <div style={{ textAlign: 'center', marginTop: '16px' }}>
                <Link to="/login" style={{ fontSize: '13px', color: '#64748b', textDecoration: 'none' }}>
                  ← Cancel and return to sign in
                </Link>
              </div>
            </form>
          )}
        </div>
      </main>
    </div>
  );
}
