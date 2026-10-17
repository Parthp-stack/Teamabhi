import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { authService } from '../services/authService';
import AdaptiveLogo from '../components/AdaptiveLogo';
import {
  Lock,
  Mail,
  Eye,
  EyeOff,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  ShieldCheck,
  KeyRound,
  RefreshCw
} from 'lucide-react';
import './Login.css';

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const navigate = useNavigate();

  // Mode: if token is present, token-based verification; otherwise, 3-step demo OTP workflow
  const [hasToken] = useState(Boolean(token));
  const [verifying, setVerifying] = useState(Boolean(token));
  const [verifiedAccount, setVerifiedAccount] = useState(null);
  const [tokenError, setTokenError] = useState('');

  // 3-step Demo OTP state: 1 = Email, 2 = Verify OTP, 3 = Create New Password, 4 = Success
  const [step, setStep] = useState(token ? 3 : 1);
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('STUDENT');
  const [demoOtp, setDemoOtp] = useState('');
  const [enteredOtp, setEnteredOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState('');
  const [success, setSuccess] = useState(false);
  const [resetToken, setResetToken] = useState(token || null);

  useEffect(() => {
    async function validateToken() {
      if (!token) {
        setVerifying(false);
        return;
      }

      try {
        const data = await authService.verifyResetToken(token);
        if (data && data.valid) {
          setVerifiedAccount(data);
          setEmail(data.email);
          setRole(data.role);
          setStep(3);
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

  // Step 1: Generate Demo OTP
  const handleGenerateOtp = async (e) => {
    if (e) e.preventDefault();
    const cleanEmail = email.trim();
    if (!cleanEmail) {
      setFormError('Please enter your registered email address.');
      return;
    }

    setSubmitting(true);
    setFormError('');
    try {
      const data = await authService.generateDemoOtp(cleanEmail, role);
      if (data && data.demo_otp) {
        setDemoOtp(data.demo_otp);
        setEnteredOtp('');
        setStep(2);
      } else {
        setFormError(data?.message || 'Email not found');
      }
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Email not found in database.');
    } finally {
      setSubmitting(false);
    }
  };

  // Step 2: Verify OTP
  const handleVerifyOtp = async (e) => {
    if (e) e.preventDefault();
    const cleanOtp = enteredOtp.trim();
    if (!cleanOtp) {
      setFormError('Please enter the 6-digit OTP.');
      return;
    }

    setSubmitting(true);
    setFormError('');
    try {
      const data = await authService.verifyResetOtp(email.trim(), cleanOtp, role);
      if (data && data.verified) {
        if (data.reset_token) setResetToken(data.reset_token);
        setStep(3);
      } else {
        setFormError('Invalid OTP.');
      }
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Invalid OTP.');
    } finally {
      setSubmitting(false);
    }
  };

  // Step 3: Set New Password
  const handleResetPassword = async (e) => {
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
        email: email.trim(),
        new_password: newPassword,
        confirm_password: confirmPassword,
        otp: enteredOtp.trim(),
        token: resetToken,
        role: role
      });

      if (res && res.success) {
        setSuccess(true);
        setStep(4);
      } else {
        setFormError(res?.message || 'Password reset failed. Please try again.');
      }
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Password reset failed. Please try again.');
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
            <h2 className="login-card-welcome-title">
              {step === 4 ? 'Password Changed!' : 'Forgot Password'}
            </h2>
            <p className="login-card-welcome-subtitle">
              {step === 1 && 'Enter your registered email to generate a demo OTP.'}
              {step === 2 && 'Enter the generated demo OTP to verify your account.'}
              {step === 3 && 'Choose a secure new password for your account.'}
              {step === 4 && 'Your password has been updated in the database.'}
            </p>
          </div>

          {/* Steps Bar */}
          {!hasToken && step < 4 && (
            <div className="forgot-steps-bar" style={{ marginBottom: '20px' }}>
              <div className={`forgot-step-chip ${step === 1 ? 'active' : ''}`}>
                <span className="forgot-step-num">1</span>
                <span>Email</span>
              </div>
              <div className="forgot-step-line" />
              <div className={`forgot-step-chip ${step === 2 ? 'active' : ''}`}>
                <span className="forgot-step-num">2</span>
                <span>Verify OTP</span>
              </div>
              <div className="forgot-step-line" />
              <div className={`forgot-step-chip ${step === 3 ? 'active' : ''}`}>
                <span className="forgot-step-num">3</span>
                <span>New Password</span>
              </div>
            </div>
          )}

          {/* Loading verification */}
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
                For security, password reset links are single-use and expire after 15 minutes. You can use the Demo OTP flow below to reset your password.
              </p>
              <button
                type="button"
                onClick={() => { setTokenError(''); setStep(1); }}
                className="login-submit-btn"
                style={{ width: '100%' }}
              >
                <span>Use Demo OTP Recovery</span>
                <ArrowRight size={18} />
              </button>
            </div>
          )}

          {/* Step 1: Email */}
          {!verifying && !tokenError && step === 1 && (
            <form onSubmit={handleGenerateOtp}>
              {formError && (
                <div className="login-alert login-alert-error" style={{ marginBottom: '16px' }}>
                  <AlertCircle size={16} />
                  <span>{formError}</span>
                </div>
              )}

              <div className="login-form-group">
                <label className="login-form-label">Email Address</label>
                <div className="login-input-wrapper">
                  <Mail size={18} className="login-input-icon" />
                  <input
                    type="text"
                    placeholder="e.g. student.a@adaptive.edu"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="login-input-field"
                    autoFocus
                  />
                </div>
              </div>

              {/* Quick Demo Account Chips */}
              <div style={{ marginTop: '-4px', marginBottom: '18px' }}>
                <div style={{ fontSize: '11.5px', fontWeight: 700, color: '#64748b', marginBottom: '6px' }}>
                  Quick Select Account:
                </div>
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                  <button
                    type="button"
                    className="login-demo-chip"
                    onClick={() => { setEmail('student.a@adaptive.edu'); setRole('STUDENT'); }}
                    style={{ fontSize: '11.5px', padding: '4px 10px' }}
                  >
                    👤 student.a@adaptive.edu
                  </button>
                  <button
                    type="button"
                    className="login-demo-chip"
                    onClick={() => { setEmail('student.b@adaptive.edu'); setRole('STUDENT'); }}
                    style={{ fontSize: '11.5px', padding: '4px 10px' }}
                  >
                    👤 student.b@adaptive.edu
                  </button>
                  <button
                    type="button"
                    className="login-demo-chip"
                    onClick={() => { setEmail('trainer@adaptive.edu'); setRole('TRAINER'); }}
                    style={{ fontSize: '11.5px', padding: '4px 10px' }}
                  >
                    🎓 trainer@adaptive.edu
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="login-submit-btn"
                style={{ width: '100%' }}
              >
                <span>{submitting ? 'Generating Demo OTP...' : 'Generate OTP'}</span>
                {!submitting && <ArrowRight size={18} />}
              </button>
            </form>
          )}

          {/* Step 2: Verify OTP */}
          {!verifying && !tokenError && step === 2 && (
            <form onSubmit={handleVerifyOtp}>
              {/* Prominent Demo OTP Display */}
              <div style={{
                background: 'linear-gradient(135deg, #f8fafc 0%, #eff6ff 100%)',
                border: '2px dashed #6366f1',
                borderRadius: '12px',
                padding: '16px',
                marginBottom: '16px',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '11px', fontWeight: 800, color: '#4f46e5', letterSpacing: '1.5px', textTransform: 'uppercase', marginBottom: '4px' }}>
                  DEMO OTP
                </div>
                <div style={{
                  fontSize: '32px',
                  fontWeight: 900,
                  letterSpacing: '8px',
                  color: '#1e1b4b',
                  fontFamily: 'monospace',
                  margin: '6px 0'
                }}>
                  {demoOtp}
                </div>
                <div style={{ fontSize: '12.5px', color: '#4338ca', fontWeight: 700 }}>
                  Use this OTP to continue.
                </div>
                <div style={{ marginTop: '8px', fontSize: '11px', color: '#64748b' }}>
                  Demo mode — OTP is displayed here for testing.
                </div>
              </div>

              {formError && (
                <div className="login-alert login-alert-error" style={{ marginBottom: '14px' }}>
                  <AlertCircle size={16} />
                  <span>{formError}</span>
                </div>
              )}

              <div className="login-form-group">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <label className="login-form-label" style={{ margin: 0 }}>Enter OTP:</label>
                  <button
                    type="button"
                    onClick={() => setEnteredOtp(demoOtp)}
                    style={{
                      background: '#e0e7ff',
                      border: '1px solid #c7d2fe',
                      borderRadius: '4px',
                      color: '#4338ca',
                      fontSize: '11px',
                      fontWeight: 700,
                      cursor: 'pointer',
                      padding: '2px 8px'
                    }}
                  >
                    Auto-fill Demo OTP
                  </button>
                </div>
                <div className="login-input-wrapper">
                  <KeyRound size={18} className="login-input-icon" />
                  <input
                    type="text"
                    maxLength={6}
                    placeholder="000000"
                    value={enteredOtp}
                    onChange={(e) => setEnteredOtp(e.target.value.replace(/\D/g, ''))}
                    required
                    className="login-input-field"
                    style={{ letterSpacing: '6px', fontSize: '18px', fontWeight: 700, textAlign: 'center' }}
                    autoFocus
                  />
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '14px' }}>
                <button
                  type="submit"
                  disabled={submitting}
                  className="login-submit-btn"
                  style={{ width: '100%' }}
                >
                  <span>{submitting ? 'Verifying OTP...' : 'Verify OTP'}</span>
                  {!submitting && <ArrowRight size={18} />}
                </button>

                <button
                  type="button"
                  disabled={submitting}
                  onClick={handleGenerateOtp}
                  className="login-demo-chip"
                  style={{
                    width: '100%',
                    justifyContent: 'center',
                    padding: '10px',
                    fontSize: '13px',
                    fontWeight: 700,
                    background: '#f1f5f9',
                    border: '1px solid #cbd5e1',
                    color: '#334155'
                  }}
                >
                  <RefreshCw size={14} style={{ marginRight: '6px' }} />
                  Generate New OTP
                </button>
              </div>

              <div style={{ textAlign: 'center', marginTop: '12px' }}>
                <button
                  type="button"
                  onClick={() => { setStep(1); setFormError(''); }}
                  style={{ background: 'none', border: 'none', color: '#64748b', fontSize: '12.5px', cursor: 'pointer' }}
                >
                  ← Change email address
                </button>
              </div>
            </form>
          )}

          {/* Step 3: Create New Password */}
          {!verifying && !tokenError && step === 3 && (
            <form onSubmit={handleResetPassword}>
              {/* Account Badge if verified */}
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
                <label className="login-form-label">Confirm Password</label>
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

          {/* Step 4 / Success State */}
          {!verifying && !tokenError && (success || step === 4) && (
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
                Password Changed Successfully
              </h3>
              <p style={{ fontSize: '14px', color: '#475569', margin: '0 0 24px 0', lineHeight: 1.5 }}>
                Your password has been updated.
              </p>
              <button
                type="button"
                onClick={() => navigate('/login')}
                className="login-submit-btn"
                style={{ width: '100%' }}
              >
                <span>Login</span>
                <ArrowRight size={18} />
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
