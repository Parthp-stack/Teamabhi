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
  Info
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

  // Forgot Password flow states
  const [resetStep, setResetStep] = useState(1); // 1: verify email, 2: enter new password, 3: completed
  const [resetEmail, setResetEmail] = useState('');
  const [resetVerifiedUser, setResetVerifiedUser] = useState(null);
  const [resetNewPassword, setResetNewPassword] = useState('');
  const [resetConfirmPassword, setResetConfirmPassword] = useState('');
  const [resetShowNewPassword, setResetShowNewPassword] = useState(false);
  const [resetShowConfirmPassword, setResetShowConfirmPassword] = useState(false);
  const [resetLoading, setResetLoading] = useState(false);
  const [resetError, setResetError] = useState('');
  const [resetSuccess, setResetSuccess] = useState('');

  const handleOpenForgotModal = () => {
    setResetEmail(email || '');
    setResetStep(1);
    setResetVerifiedUser(null);
    setResetNewPassword('');
    setResetConfirmPassword('');
    setResetShowNewPassword(false);
    setResetShowConfirmPassword(false);
    setResetLoading(false);
    setResetError('');
    setResetSuccess('');
    setActiveModal('forgot');
  };

  const handleVerifyEmail = async (e) => {
    if (e) e.preventDefault();
    const cleanInput = resetEmail.trim();
    if (!cleanInput) {
      setResetError('Please enter your registered email address or student ID.');
      return;
    }
    setResetLoading(true);
    setResetError('');
    try {
      const data = await authService.verifyResetEmail(cleanInput, activeRole);
      if (data && data.exists) {
        setResetVerifiedUser(data);
        setResetStep(2);
      } else {
        setResetError('No account found with this email in the database.');
      }
    } catch (err) {
      const msg = err.response?.data?.detail;
      if (msg) {
        setResetError(msg);
      } else if (!err.response) {
        setResetError('Cannot connect to backend server. Ensure backend is running.');
      } else {
        setResetError(`No account registered with "${cleanInput}" was found in the database. Please check your email or create an account.`);
      }
      // Stays on Step 1: NEVER advance to Step 2 if account is not found in database!
    } finally {
      setResetLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    if (e) e.preventDefault();
    setResetError('');

    if (resetNewPassword.length < 6) {
      setResetError('New password must be at least 6 characters long.');
      return;
    }
    if (resetNewPassword !== resetConfirmPassword) {
      setResetError('Passwords do not match. Please re-enter.');
      return;
    }

    setResetLoading(true);
    const targetEmail = resetVerifiedUser?.email || resetEmail.trim();
    try {
      const data = await authService.resetPassword(targetEmail, resetNewPassword, resetVerifiedUser?.role);
      if (data && data.success) {
        setResetSuccess(data.message || 'Password successfully updated in database!');
        setResetStep(3);
      } else {
        setResetError(data?.message || 'Failed to update password in database.');
      }
    } catch (err) {
      if (!err.response) {
        setResetError('Cannot connect to backend server. Ensure backend is running.');
      } else {
        setResetError(err.response?.data?.detail || 'Failed to update password in database. Please try again.');
      }
      // Stays on Step 2: NEVER advance to Step 3 if update failed!
    } finally {
      setResetLoading(false);
    }
  };

  const handleApplyNewPasswordAndLogin = () => {
    const finalEmail = resetVerifiedUser?.email || resetEmail.trim();
    setEmail(finalEmail);
    setPassword(resetNewPassword);
    if (resetVerifiedUser?.role) {
      setActiveRole(resetVerifiedUser.role);
    }
    setIsRegistering(false);
    setError('');
    setSuccessMsg('Password successfully updated in database! Click "Sign In" below to log in.');
    setActiveModal(null);
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
                {/* 3-Step Progress Header */}
                <div className="forgot-steps-bar">
                  <div className={`forgot-step-chip ${resetStep >= 1 ? 'active' : ''}`}>
                    <span className="forgot-step-num">1</span>
                    <span>Verify Email</span>
                  </div>
                  <div className="forgot-step-line" />
                  <div className={`forgot-step-chip ${resetStep >= 2 ? 'active' : ''}`}>
                    <span className="forgot-step-num">2</span>
                    <span>New Password</span>
                  </div>
                  <div className="forgot-step-line" />
                  <div className={`forgot-step-chip ${resetStep >= 3 ? 'active' : ''}`}>
                    <span className="forgot-step-num">3</span>
                    <span>Done</span>
                  </div>
                </div>

                {resetError && (
                  <div className="login-alert login-alert-error" style={{ marginBottom: '14px' }}>
                    <AlertCircle size={16} />
                    <span>{resetError}</span>
                  </div>
                )}

                {/* Step 1: Search and Verify Registered Email */}
                {resetStep === 1 && (
                  <form onSubmit={handleVerifyEmail}>
                    <p style={{ fontSize: '13.5px', color: '#64748b', margin: '0 0 16px 0', lineHeight: 1.5 }}>
                      Enter your registered email address stored in the database. If it matches an existing account (Student or Trainer), you will be able to restore and save a new password.
                    </p>
                    <div className="login-form-group">
                      <label className="login-form-label">Email Address / Student ID</label>
                      <div className="login-input-wrapper">
                        <Mail size={18} className="login-input-icon" />
                        <input
                          type="text"
                          placeholder="e.g. student.a@adaptive.edu or trainer@adaptive.edu"
                          value={resetEmail}
                          onChange={(e) => setResetEmail(e.target.value)}
                          required
                          className="login-input-field"
                          autoFocus
                        />
                      </div>
                    </div>

                    {/* Quick Demo Account Chips */}
                    <div style={{ marginTop: '-4px', marginBottom: '14px' }}>
                      <div style={{ fontSize: '11.5px', fontWeight: 700, color: '#64748b', marginBottom: '6px' }}>
                        Quick Select Account:
                      </div>
                      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                        <button
                          type="button"
                          className="login-demo-chip"
                          onClick={() => setResetEmail('student.a@adaptive.edu')}
                          style={{ fontSize: '11.5px', padding: '4px 10px' }}
                        >
                          👤 student.a@adaptive.edu
                        </button>
                        <button
                          type="button"
                          className="login-demo-chip"
                          onClick={() => setResetEmail('student.b@adaptive.edu')}
                          style={{ fontSize: '11.5px', padding: '4px 10px' }}
                        >
                          👤 student.b@adaptive.edu
                        </button>
                        <button
                          type="button"
                          className="login-demo-chip"
                          onClick={() => setResetEmail('trainer@adaptive.edu')}
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
                      <span>{resetLoading ? 'Checking Database...' : 'Find & Verify Email'}</span>
                      {!resetLoading && <ArrowRight size={18} />}
                    </button>
                  </form>
                )}

                {/* Step 2: Enter New Password */}
                {resetStep === 2 && (
                  <form onSubmit={handleResetPassword}>
                    <div className="forgot-verified-badge" style={{ marginBottom: '14px' }}>
                      <CheckCircle2 size={20} color="#059669" />
                      <div>
                        <div style={{ fontWeight: 700, color: '#166534' }}>
                          Account Found: {resetVerifiedUser?.name}
                          <span className={`forgot-role-tag ${resetVerifiedUser?.role === 'TRAINER' ? 'trainer' : 'student'}`}>
                            {resetVerifiedUser?.role}
                          </span>
                        </div>
                        <div style={{ fontSize: '12px', color: '#15803d' }}>{resetVerifiedUser?.email}</div>
                      </div>
                    </div>

                    <p style={{ fontSize: '13px', color: '#64748b', margin: '0 0 14px 0' }}>
                      Enter and confirm your new password below. It will be immediately updated in the database for future logins.
                    </p>

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
                      <label className="login-form-label">Confirm New Password</label>
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
                      style={{ marginTop: '10px', width: '100%' }}
                    >
                      <span>{resetLoading ? 'Saving in Database...' : 'Save New Password'}</span>
                      {!resetLoading && <CheckCircle2 size={18} />}
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setResetStep(1);
                        setResetError('');
                      }}
                      style={{
                        marginTop: '12px',
                        background: 'none',
                        border: 'none',
                        color: '#64748b',
                        fontSize: '13px',
                        cursor: 'pointer',
                        width: '100%',
                        textAlign: 'center'
                      }}
                    >
                      ← Use a different email address
                    </button>
                  </form>
                )}

                {/* Step 3: Success Confirmation */}
                {resetStep === 3 && (
                  <div style={{ textAlign: 'center', padding: '12px 0 6px 0' }}>
                    <div style={{
                      width: '56px',
                      height: '56px',
                      borderRadius: '50%',
                      background: '#ecfdf5',
                      color: '#059669',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      margin: '0 auto 16px auto',
                      border: '2px solid #a7f3d0'
                    }}>
                      <CheckCircle2 size={32} />
                    </div>
                    <h4 style={{ margin: '0 0 8px 0', fontSize: '18px', fontWeight: 800, color: '#0f172a' }}>
                      Password Updated Successfully!
                    </h4>
                    <p style={{ fontSize: '13.5px', color: '#475569', margin: '0 0 20px 0', lineHeight: 1.5 }}>
                      The new password for <strong>{resetVerifiedUser?.email}</strong> is now saved in the database.
                      Click below to return to the sign-in screen and log in with your new password.
                    </p>
                    <button
                      type="button"
                      onClick={handleApplyNewPasswordAndLogin}
                      className="login-submit-btn"
                      style={{ width: '100%' }}
                    >
                      <span>Sign In with New Password</span>
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
