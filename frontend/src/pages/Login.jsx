import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';
import {
  GraduationCap,
  Users,
  Mail,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  BookOpen,
  Target,
  BarChart3,
  User,
  Sparkles,
  AlertCircle,
  CheckCircle2,
  X,
  HelpCircle,
  Info,
  KeyRound,
  ShieldCheck,
  RefreshCw
} from 'lucide-react';
import './Login.css';
import AdaptiveLogo from '../components/AdaptiveLogo';

// Assets
import studentWorkspaceImg from '../assets/student-workspace.png';

export default function Login() {
  const navigate = useNavigate();
  const [activeRole, setActiveRole] = useState('STUDENT'); // 'STUDENT' or 'TRAINER'
  const [isRegistering, setIsRegistering] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  // Form fields
  const [name, setName] = useState('');
  const [email, setEmail] = useState('student.a@adaptive.edu');
  const [password, setPassword] = useState('student123');
  const [targetSubject, setTargetSubject] = useState('Data Structures');
  const [department, setDepartment] = useState('Computer Science');

  // Status feedback
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Info Modal states for top nav
  const [activeModal, setActiveModal] = useState(null); // 'features' | 'about' | 'contact' | 'forgot' | null

  // Forgot Password flow states (Demo / Hackathon OTP Flow)
  const [resetStep, setResetStep] = useState(1); // 1: Email, 2: Verify OTP, 3: Create New Password, 4: Success
  const [resetEmail, setResetEmail] = useState('');
  const [demoOtp, setDemoOtp] = useState('');
  const [enteredOtp, setEnteredOtp] = useState('');
  const [resetNewPassword, setResetNewPassword] = useState('');
  const [resetConfirmPassword, setResetConfirmPassword] = useState('');
  const [resetShowNewPassword, setResetShowNewPassword] = useState(false);
  const [resetShowConfirmPassword, setResetShowConfirmPassword] = useState(false);
  const [resetLoading, setResetLoading] = useState(false);
  const [resetError, setResetError] = useState('');
  const [resetSuccess, setResetSuccess] = useState('');
  const [resetToken, setResetToken] = useState(null);

  const handleOpenForgotModal = () => {
    setResetStep(1);
    setResetEmail(email || '');
    setDemoOtp('');
    setEnteredOtp('');
    setResetNewPassword('');
    setResetConfirmPassword('');
    setResetLoading(false);
    setResetError('');
    setResetSuccess('');
    setResetToken(null);
    setActiveModal('forgot');
  };

  const handleGenerateDemoOtp = async (e) => {
    if (e) e.preventDefault();
    const cleanInput = resetEmail.trim();
    if (!cleanInput) {
      setResetError('Please enter your registered email address.');
      return;
    }
    setResetLoading(true);
    setResetError('');
    setResetSuccess('');
    try {
      const data = await authService.generateDemoOtp(cleanInput, activeRole);
      if (data && data.demo_otp) {
        setDemoOtp(data.demo_otp);
        setEnteredOtp('');
        setResetStep(2);
      } else {
        setResetError(data?.message || 'Email not found');
      }
    } catch (err) {
      const msg = err.response?.data?.detail;
      if (msg) {
        setResetError(msg);
      } else if (!err.response) {
        setResetError('Cannot connect to backend server. Ensure backend is running.');
      } else {
        setResetError('Email not found');
      }
    } finally {
      setResetLoading(false);
    }
  };

  const handleVerifyOtp = async (e) => {
    if (e) e.preventDefault();
    const cleanOtp = enteredOtp.trim();
    if (!cleanOtp) {
      setResetError('Please enter the 6-digit OTP.');
      return;
    }
    setResetLoading(true);
    setResetError('');
    try {
      const data = await authService.verifyResetOtp(resetEmail.trim(), cleanOtp, activeRole);
      if (data && data.verified) {
        if (data.reset_token) {
          setResetToken(data.reset_token);
        }
        setResetStep(3);
      } else {
        setResetError('Invalid OTP.');
      }
    } catch (err) {
      const msg = err.response?.data?.detail;
      setResetError(msg || 'Invalid OTP.');
    } finally {
      setResetLoading(false);
    }
  };

  const handleResetPasswordSubmit = async (e) => {
    if (e) e.preventDefault();
    setResetError('');

    if (!resetNewPassword || resetNewPassword.length < 6) {
      setResetError('New password must be at least 6 characters long.');
      return;
    }

    if (resetNewPassword !== resetConfirmPassword) {
      setResetError('Passwords do not match. Please re-enter.');
      return;
    }

    setResetLoading(true);
    try {
      const data = await authService.resetPassword({
        email: resetEmail.trim(),
        new_password: resetNewPassword,
        confirm_password: resetConfirmPassword,
        otp: enteredOtp.trim(),
        token: resetToken,
        role: activeRole
      });

      if (data && data.success) {
        setResetStep(4);
      } else {
        setResetError(data?.message || 'Password reset failed. Please try again.');
      }
    } catch (err) {
      const msg = err.response?.data?.detail;
      setResetError(msg || 'Password reset failed. Please try again.');
    } finally {
      setResetLoading(false);
    }
  };

  const handleSuccessLogin = () => {
    setEmail(resetEmail.trim());
    setPassword(resetNewPassword);
    setActiveModal(null);
    setSuccessMsg('Password changed successfully! You can now sign in with your new password.');
  };



  const handleAuth = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError('');
    setSuccessMsg('');

    try {
      if (isRegistering) {
        if (!name.trim()) {
          setError('Please enter your full name to create an account.');
          setLoading(false);
          return;
        }
        const data = await authService.register(name, email, password, activeRole);
        setSuccessMsg('Account created successfully! Redirecting...');
        setTimeout(() => {
          if (data.user.role === 'TRAINER') {
            navigate('/trainer/dashboard');
          } else {
            navigate('/student/dashboard');
          }
        }, 600);
      } else {
        const data = await authService.login(email, password);
        if (data.user.role === 'TRAINER') {
          navigate('/trainer/dashboard');
        } else {
          navigate('/student/dashboard');
        }
      }
    } catch (err) {
      if (!err.response) {
        setError('Cannot connect to backend server. Ensure backend is running on http://localhost:8000.');
      } else {
        setError(err.response?.data?.detail || 'Authentication failed. Please check your credentials.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRoleSwitch = (role) => {
    setActiveRole(role);
    setError('');
    setSuccessMsg('');
    if (role === 'STUDENT') {
      setEmail('student.a@adaptive.edu');
      setPassword('student123');
    } else {
      setEmail('trainer@adaptive.edu');
      setPassword('trainer123');
    }
  };

  const setDemoAccount = (demoEmail, demoPass, role) => {
    setActiveRole(role);
    setIsRegistering(false);
    setEmail(demoEmail);
    setPassword(demoPass);
    setError('');
    setSuccessMsg('');
  };

  return (
    <div className="login-page-container">
      {/* Top Navigation Bar */}
      <header className="login-navbar">
        <div className="login-nav-logo" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
          <AdaptiveLogo size={42} light={true} />
          <div className="login-nav-logo-text">
            <span className="login-nav-brand">
              Adapt<span>IQ</span>
            </span>
            <span className="login-nav-tagline">
              Adaptive Assessment & Learning Platform
            </span>
          </div>
        </div>

        <nav className="login-nav-links">
          <button
            type="button"
            className="login-nav-link"
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          >
            Home
          </button>
          <button
            type="button"
            className="login-nav-link"
            onClick={() => setActiveModal('features')}
          >
            Features
          </button>
          <button
            type="button"
            className="login-nav-link"
            onClick={() => setActiveModal('about')}
          >
            About
          </button>
          <button
            type="button"
            className="login-nav-link"
            onClick={() => setActiveModal('contact')}
          >
            Contact
          </button>
        </nav>
      </header>

      {/* Main Hero & Auth Section */}
      <main className="login-main-content">
        {/* Left Column: Hero Text, Feature Badges & 3D Artwork */}
        <section className="login-hero-section">
          <h1 className="login-hero-headline">
            Learn at <span className="login-text-gradient-purple">your pace.</span>
            <br />
            Prove what <span className="login-text-gradient-cyan">you know.</span>
          </h1>

          <p className="login-hero-subtitle">
            Personalized learning paths, adaptive assessments and verified skills for a brighter future.
          </p>

          {/* 3 Highlight Badges */}
          <div className="login-features-row">
            <div className="login-feature-card">
              <div className="login-feature-icon-box purple">
                <BookOpen size={20} />
              </div>
              <div>
                <div className="login-feature-title">Adaptive Learning</div>
                <div className="login-feature-desc">Learn what you need</div>
              </div>
            </div>

            <div className="login-feature-card">
              <div className="login-feature-icon-box blue">
                <Target size={20} />
              </div>
              <div>
                <div className="login-feature-title">Smart Assessments</div>
                <div className="login-feature-desc">Questions that adapt</div>
              </div>
            </div>

            <div className="login-feature-card">
              <div className="login-feature-icon-box indigo">
                <BarChart3 size={20} />
              </div>
              <div>
                <div className="login-feature-title">Verified Skills</div>
                <div className="login-feature-desc">Real progress. Real results.</div>
              </div>
            </div>
          </div>

          {/* 3D Student Character & Floating UI Cards */}
          <div className="login-illustration-container">
            <img
              src={studentWorkspaceImg}
              alt="Interactive learning journey with adaptive mastery visualization"
              className="login-illustration-img"
            />
          </div>
        </section>

        {/* Right Column: Clean White Sign-in / Register Card */}
        <section className="login-card-section">
          <div className="login-white-card">
            {/* Card Header & Logo */}
            <div className="login-card-header">
              <div className="login-card-brand-row">
                <AdaptiveLogo size={42} light={false} />
                <div>
                  <div className="login-card-brand-title">
                    Adapt<span>IQ</span>
                  </div>
                  <div className="login-card-brand-sub">
                    Adaptive Assessment & Learning Platform
                  </div>
                </div>
              </div>

              <h2 className="login-card-welcome-title">
                {isRegistering ? 'Create Account 🚀' : 'Welcome Back 👋'}
              </h2>
              <p className="login-card-welcome-subtitle">
                {isRegistering
                  ? 'Join to start your personalized learning pathway.'
                  : 'Sign in to continue your learning journey.'}
              </p>
            </div>

            {/* Role Switcher Tabs */}
            <div className="login-role-tabs">
              <button
                type="button"
                className={`login-role-tab-btn ${activeRole === 'STUDENT' ? 'active' : ''}`}
                onClick={() => handleRoleSwitch('STUDENT')}
              >
                <GraduationCap size={18} />
                Student
              </button>
              <button
                type="button"
                className={`login-role-tab-btn ${activeRole === 'TRAINER' ? 'trainer-active' : ''}`}
                onClick={() => handleRoleSwitch('TRAINER')}
              >
                <Users size={18} />
                Trainer
              </button>
            </div>

            {/* Error & Success Feedback */}
            {error && (
              <div className="login-alert login-alert-error">
                <AlertCircle size={16} />
                <span>{error}</span>
              </div>
            )}
            {successMsg && (
              <div className="login-alert login-alert-success">
                <CheckCircle2 size={16} />
                <span>{successMsg}</span>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleAuth}>
              {isRegistering && (
                <div className="login-form-group">
                  <label className="login-form-label">Full Name</label>
                  <div className="login-input-wrapper">
                    <User size={18} className="login-input-icon" />
                    <input
                      type="text"
                      placeholder={activeRole === 'STUDENT' ? 'e.g. John Doe' : 'e.g. Prof. Alan Turing'}
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      required
                      className="login-input-field"
                    />
                  </div>
                </div>
              )}

              <div className="login-form-group">
                <label className="login-form-label">Email / Student ID</label>
                <div className="login-input-wrapper">
                  <Mail size={18} className="login-input-icon" />
                  <input
                    type="email"
                    placeholder="Enter your email or student ID"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="login-input-field"
                  />
                </div>
              </div>

              <div className="login-form-group">
                <label className="login-form-label">Password</label>
                <div className="login-input-wrapper">
                  <Lock size={18} className="login-input-icon" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="login-input-field"
                  />
                  <button
                    type="button"
                    className="login-password-toggle"
                    onClick={() => setShowPassword(!showPassword)}
                    tabIndex="-1"
                    title={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              {isRegistering && activeRole === 'STUDENT' && (
                <div className="login-form-group">
                  <label className="login-form-label">Target Subject</label>
                  <div className="login-input-wrapper">
                    <select
                      value={targetSubject}
                      onChange={(e) => setTargetSubject(e.target.value)}
                      className="login-input-field"
                      style={{ paddingLeft: '14px' }}
                    >
                      <option value="Data Structures">Data Structures (Searching, Sorting, Linked Lists)</option>
                      <option value="Object Oriented Programming">Object Oriented Programming (Classes, Inheritance)</option>
                    </select>
                  </div>
                </div>
              )}

              {isRegistering && activeRole === 'TRAINER' && (
                <div className="login-form-group">
                  <label className="login-form-label">Academic Department</label>
                  <div className="login-input-wrapper">
                    <input
                      type="text"
                      placeholder="e.g. Computer Science"
                      value={department}
                      onChange={(e) => setDepartment(e.target.value)}
                      className="login-input-field"
                      style={{ paddingLeft: '14px' }}
                    />
                  </div>
                </div>
              )}

              {!isRegistering && (
                <div className="login-forgot-row">
                  <button
                    type="button"
                    className="login-forgot-btn"
                    onClick={handleOpenForgotModal}
                  >
                    Forgot Password?
                  </button>
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className={`login-submit-btn ${activeRole === 'TRAINER' ? 'trainer-btn' : ''}`}
              >
                <span>
                  {loading
                    ? 'Authenticating...'
                    : isRegistering
                    ? `Create ${activeRole === 'STUDENT' ? 'Student' : 'Trainer'} Account`
                    : 'Sign In'}
                </span>
                {!loading && <ArrowRight size={18} />}
              </button>
            </form>

            {/* Divider */}
            <div className="login-divider-row">
              <div className="login-divider-line" />
              <div className="login-divider-text">OR</div>
              <div className="login-divider-line" />
            </div>

            {/* Footer: Toggle Mode */}
            <div className="login-card-footer">
              {!isRegistering ? (
                <>
                  Don't have an account?{' '}
                  <button
                    type="button"
                    className="login-switch-mode-btn"
                    onClick={() => {
                      setIsRegistering(true);
                      setError('');
                      setSuccessMsg('');
                    }}
                  >
                    Create account
                  </button>
                </>
              ) : (
                <>
                  Already have an account?{' '}
                  <button
                    type="button"
                    className="login-switch-mode-btn"
                    onClick={() => {
                      setIsRegistering(false);
                      setError('');
                      setSuccessMsg('');
                    }}
                  >
                    Sign in
                  </button>
                </>
              )}
            </div>

            {/* Demo Quick Accounts Bar */}
            {!isRegistering && (
              <div className="login-demo-bar">
                <div className="login-demo-title">
                  <Sparkles size={13} color="#6366f1" />
                  <span>Demo Access (Click to Load)</span>
                </div>
                <div className="login-demo-chips">
                  <button
                    type="button"
                    className={`login-demo-chip ${email === 'student.a@adaptive.edu' ? 'active-chip' : ''}`}
                    onClick={() => setDemoAccount('student.a@adaptive.edu', 'student123', 'STUDENT')}
                  >
                    👤 Alice (Student)
                  </button>
                  <button
                    type="button"
                    className={`login-demo-chip ${email === 'student.b@adaptive.edu' ? 'active-chip' : ''}`}
                    onClick={() => setDemoAccount('student.b@adaptive.edu', 'student123', 'STUDENT')}
                  >
                    👤 Bob (Student)
                  </button>
                  <button
                    type="button"
                    className={`login-demo-chip ${email === 'trainer@adaptive.edu' ? 'active-chip' : ''}`}
                    onClick={() => setDemoAccount('trainer@adaptive.edu', 'trainer123', 'TRAINER')}
                  >
                    🎓 Dr. Turing (Trainer)
                  </button>
                </div>
              </div>
            )}
          </div>
        </section>
      </main>

      {/* Info Modals for Top Nav Links & Forgot Password */}
      {activeModal && (
        <div className="login-modal-backdrop" onClick={() => setActiveModal(null)}>
          <div className="login-modal-box" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AdaptiveLogo size={28} />
                <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 800, color: '#0f172a' }}>
                  {activeModal === 'features' && 'Platform Features'}
                  {activeModal === 'about' && 'About AdaptIQ'}
                  {activeModal === 'contact' && 'Academic Support'}
                  {activeModal === 'forgot' && 'Reset Account Password'}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setActiveModal(null)}
                style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '4px' }}
              >
                <X size={20} />
              </button>
            </div>

            {activeModal === 'features' && (
              <div style={{ fontSize: '14px', color: '#475569', lineHeight: 1.6 }}>
                <p><strong>🎯 Bayesian Knowledge Tracing:</strong> Dynamically calculates concept mastery scores based on real-time question responses.</p>
                <p><strong>⚡ Adaptive Question Generator:</strong> Adjusts difficulty based on your exact weak spots and prerequisite mastery.</p>
                <p><strong>🔒 Verified Coding Sandbox:</strong> Executes code in isolated containers with full telemetry and automated integrity scoring.</p>
              </div>
            )}

            {activeModal === 'about' && (
              <div style={{ fontSize: '14px', color: '#475569', lineHeight: 1.6 }}>
                <p><strong>AdaptIQ</strong> is an intelligent assessment and learning environment designed for university computer science cohorts.</p>
                <p>Our mission is to help every student master core algorithms and programming skills through personalized, evidence-based feedback.</p>
              </div>
            )}

            {activeModal === 'contact' && (
              <div style={{ fontSize: '14px', color: '#475569', lineHeight: 1.6 }}>
                <p>Need support or instructor credentials?</p>
                <p>📧 Email: <a href="mailto:support@adaptiq.edu" style={{ color: '#4f46e5', fontWeight: 700 }}>support@adaptiq.edu</a></p>
                <p>🏢 Campus Center: Turing Hall, Suite 402</p>
                <p>For immediate testing, use the <strong>Demo Access</strong> buttons on the login card.</p>
              </div>
            )}

            {activeModal === 'forgot' && (
              <div className="forgot-modal-content">
                {/* Steps Navigation Bar */}
                <div className="forgot-steps-bar" style={{ marginBottom: '18px' }}>
                  <div className={`forgot-step-chip ${resetStep === 1 ? 'active' : ''}`}>
                    <span className="forgot-step-num">1</span>
                    <span>Email</span>
                  </div>
                  <div className="forgot-step-line" />
                  <div className={`forgot-step-chip ${resetStep === 2 ? 'active' : ''}`}>
                    <span className="forgot-step-num">2</span>
                    <span>Verify OTP</span>
                  </div>
                  <div className="forgot-step-line" />
                  <div className={`forgot-step-chip ${resetStep === 3 ? 'active' : ''}`}>
                    <span className="forgot-step-num">3</span>
                    <span>New Password</span>
                  </div>
                </div>

                {/* Step 1: Enter Email */}
                {resetStep === 1 && (
                  <form onSubmit={handleGenerateDemoOtp}>
                    <h4 style={{ margin: '0 0 6px 0', fontSize: '18px', fontWeight: 800, color: '#0f172a' }}>
                      Forgot Password
                    </h4>
                    <p style={{ fontSize: '13.5px', color: '#64748b', margin: '0 0 16px 0', lineHeight: 1.5 }}>
                      Enter your registered email for your <strong>{activeRole === 'STUDENT' ? 'Student' : 'Trainer'}</strong> account.
                    </p>

                    {resetError && (
                      <div className="login-alert login-alert-error" style={{ marginBottom: '14px' }}>
                        <AlertCircle size={16} />
                        <span>{resetError}</span>
                      </div>
                    )}

                    <div className="login-form-group">
                      <label className="login-form-label">Email</label>
                      <div className="login-input-wrapper">
                        <Mail size={18} className="login-input-icon" />
                        <input
                          type="text"
                          placeholder={activeRole === 'STUDENT' ? 'e.g. student.a@adaptive.edu' : 'e.g. trainer@adaptive.edu'}
                          value={resetEmail}
                          onChange={(e) => setResetEmail(e.target.value)}
                          required
                          className="login-input-field"
                          autoFocus
                        />
                      </div>
                    </div>

                    {/* Quick Demo Account Chips */}
                    <div style={{ marginTop: '-4px', marginBottom: '16px' }}>
                      <div style={{ fontSize: '11.5px', fontWeight: 700, color: '#64748b', marginBottom: '6px' }}>
                        Quick Select Account:
                      </div>
                      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                        <button
                          type="button"
                          className="login-demo-chip"
                          onClick={() => { setResetEmail('student.a@adaptive.edu'); setActiveRole('STUDENT'); }}
                          style={{ fontSize: '11.5px', padding: '4px 10px' }}
                        >
                          👤 student.a@adaptive.edu
                        </button>
                        <button
                          type="button"
                          className="login-demo-chip"
                          onClick={() => { setResetEmail('student.b@adaptive.edu'); setActiveRole('STUDENT'); }}
                          style={{ fontSize: '11.5px', padding: '4px 10px' }}
                        >
                          👤 student.b@adaptive.edu
                        </button>
                        <button
                          type="button"
                          className="login-demo-chip"
                          onClick={() => { setResetEmail('trainer@adaptive.edu'); setActiveRole('TRAINER'); }}
                          style={{ fontSize: '11.5px', padding: '4px 10px' }}
                        >
                          🎓 trainer@adaptive.edu
                        </button>
                      </div>
                    </div>

                    <button
                      type="submit"
                      disabled={resetLoading}
                      className="login-submit-btn"
                      style={{ marginTop: '4px', width: '100%' }}
                    >
                      <span>{resetLoading ? 'Generating Demo OTP...' : 'Generate OTP'}</span>
                      {!resetLoading && <ArrowRight size={18} />}
                    </button>
                  </form>
                )}

                {/* Step 2: Verify OTP */}
                {resetStep === 2 && (
                  <form onSubmit={handleVerifyOtp}>
                    <h4 style={{ margin: '0 0 6px 0', fontSize: '18px', fontWeight: 800, color: '#0f172a' }}>
                      Verify OTP
                    </h4>

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

                    {resetError && (
                      <div className="login-alert login-alert-error" style={{ marginBottom: '14px' }}>
                        <AlertCircle size={16} />
                        <span>{resetError}</span>
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
                        disabled={resetLoading}
                        className="login-submit-btn"
                        style={{ width: '100%' }}
                      >
                        <span>{resetLoading ? 'Verifying OTP...' : 'Verify OTP'}</span>
                        {!resetLoading && <ArrowRight size={18} />}
                      </button>

                      <button
                        type="button"
                        disabled={resetLoading}
                        onClick={handleGenerateDemoOtp}
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
                        onClick={() => { setResetStep(1); setResetError(''); }}
                        style={{ background: 'none', border: 'none', color: '#64748b', fontSize: '12.5px', cursor: 'pointer' }}
                      >
                        ← Change email address
                      </button>
                    </div>
                  </form>
                )}

                {/* Step 3: Create New Password */}
                {resetStep === 3 && (
                  <form onSubmit={handleResetPasswordSubmit}>
                    <h4 style={{ margin: '0 0 6px 0', fontSize: '18px', fontWeight: 800, color: '#0f172a' }}>
                      Create New Password
                    </h4>
                    <p style={{ fontSize: '13.5px', color: '#64748b', margin: '0 0 16px 0', lineHeight: 1.5 }}>
                      Enter and confirm your new password for <strong>{resetEmail}</strong>.
                    </p>

                    {resetError && (
                      <div className="login-alert login-alert-error" style={{ marginBottom: '14px' }}>
                        <AlertCircle size={16} />
                        <span>{resetError}</span>
                      </div>
                    )}

                    <div className="login-form-group">
                      <label className="login-form-label">New Password</label>
                      <div className="login-input-wrapper">
                        <Lock size={18} className="login-input-icon" />
                        <input
                          type={resetShowNewPassword ? 'text' : 'password'}
                          placeholder="At least 6 characters"
                          value={resetNewPassword}
                          onChange={(e) => setResetNewPassword(e.target.value)}
                          required
                          className="login-input-field"
                          autoFocus
                        />
                        <button
                          type="button"
                          className="login-password-toggle"
                          onClick={() => setResetShowNewPassword(!resetShowNewPassword)}
                          tabIndex="-1"
                        >
                          {resetShowNewPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                        </button>
                      </div>
                    </div>

                    <div className="login-form-group">
                      <label className="login-form-label">Confirm Password</label>
                      <div className="login-input-wrapper">
                        <Lock size={18} className="login-input-icon" />
                        <input
                          type={resetShowConfirmPassword ? 'text' : 'password'}
                          placeholder="Re-enter new password"
                          value={resetConfirmPassword}
                          onChange={(e) => setResetConfirmPassword(e.target.value)}
                          required
                          className="login-input-field"
                        />
                        <button
                          type="button"
                          className="login-password-toggle"
                          onClick={() => setResetShowConfirmPassword(!resetShowConfirmPassword)}
                          tabIndex="-1"
                        >
                          {resetShowConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                        </button>
                      </div>
                    </div>

                    <button
                      type="submit"
                      disabled={resetLoading}
                      className="login-submit-btn"
                      style={{ marginTop: '8px', width: '100%' }}
                    >
                      <span>{resetLoading ? 'Updating Password...' : 'Reset Password'}</span>
                      {!resetLoading && <CheckCircle2 size={18} />}
                    </button>
                  </form>
                )}

                {/* Success: Password Changed Successfully */}
                {resetStep === 4 && (
                  <div style={{ textAlign: 'center', padding: '12px 0 6px 0' }}>
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
                    <h4 style={{ margin: '0 0 8px 0', fontSize: '20px', fontWeight: 800, color: '#0f172a' }}>
                      Password Changed Successfully
                    </h4>
                    <p style={{ fontSize: '14px', color: '#475569', margin: '0 0 20px 0', lineHeight: 1.5 }}>
                      Your password has been updated.
                    </p>
                    <button
                      type="button"
                      onClick={handleSuccessLogin}
                      className="login-submit-btn"
                      style={{ width: '100%' }}
                    >
                      <span>Login</span>
                      <ArrowRight size={18} />
                    </button>
                  </div>
                )}
              </div>

            )}
          </div>
        </div>
      )}
    </div>
  );
}
