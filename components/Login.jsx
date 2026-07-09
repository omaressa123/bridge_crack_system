import React, { useEffect, useState } from 'react';
import { API_URL } from '../api';

export default function Login({ onLoginSuccess, language, setLanguage }) {
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const translations = {
    en: {
      title: 'Bridge Crack Detection System',
      subtitle: 'Bilingual Infrastructure Monitoring Platform',
      welcome: 'Welcome Back',
      signInText: 'Please sign in with your Google account to access the dashboard.',
      languageText: 'اللغة العربية',
      loading: 'Signing in...',
      errorHeader: 'Authentication Error',
      footer: 'Protected System. Unauthorized access is prohibited.'
    },
    ar: {
      title: 'نظام كشف شروخ الجسور',
      subtitle: 'منصة ثنائية اللغة لمراقبة البنية التحتية',
      welcome: 'مرحباً بك مجدداً',
      signInText: 'يرجى تسجيل الدخول باستخدام حساب Google الخاص بك للوصول إلى لوحة التحكم.',
      languageText: 'English',
      loading: 'جاري تسجيل الدخول...',
      errorHeader: 'خطأ في تسجيل الدخول',
      footer: 'نظام محمي. يمنع الدخول غير المصرح به.'
    }
  };

  const t = translations[language];

  useEffect(() => {
    // Handle the response from Google
    window.handleCredentialResponse = async (response) => {
      setLoading(true);
      setError('');
      try {
        const res = await fetch(`${API_URL}/api/auth/google`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ credential: response.credential }),
        });

        if (!res.ok) {
          const errData = await res.json();
          throw new Error(errData.detail || 'Failed to authenticate with backend');
        }

        const data = await res.json();
        onLoginSuccess(data.token, data.user);
      } catch (err) {
        console.error('Login error:', err);
        setError(err.message || 'An error occurred during authentication.');
      } finally {
        setLoading(false);
      }
    };

    // Initialize Google Identity Services
    const initializeGoogleSignIn = () => {
      if (window.google) {
        window.google.accounts.id.initialize({
          client_id: '393156804705-v60ojlk1pc0cono9crvn56bjumf6sffv.apps.googleusercontent.com',
          callback: window.handleCredentialResponse,
        });

        window.google.accounts.id.renderButton(
          document.getElementById('google-signin-btn'),
          { 
            theme: 'filled_blue', 
            size: 'large', 
            width: '320', 
            text: 'signin_with',
            shape: 'pill'
          }
        );
      } else {
        // Retry in 500ms if script is not fully loaded yet
        setTimeout(initializeGoogleSignIn, 500);
      }
    };

    initializeGoogleSignIn();
  }, [onLoginSuccess]);

  return (
    <div className={`login-page ${language === 'ar' ? 'rtl' : 'ltr'}`}>
      <button 
        className="login-language-btn"
        onClick={() => setLanguage(language === 'en' ? 'ar' : 'en')}
      >
        {t.languageText}
      </button>

      <div className="login-card">
        <div className="login-logo">🌉</div>
        <h1>{t.title}</h1>
        <p className="login-subtitle">{t.subtitle}</p>

        <hr className="login-divider" />

        <h2>{t.welcome}</h2>
        <p className="login-desc">{t.signInText}</p>

        {error && (
          <div className="login-error">
            <strong>⚠️ {t.errorHeader}:</strong> {error}
          </div>
        )}

        <div className="signin-button-wrapper">
          {loading ? (
            <div className="login-loader">
              <span className="spinner"></span>
              {t.loading}
            </div>
          ) : (
            <div id="google-signin-btn"></div>
          )}
        </div>

        <p className="login-footer">{t.footer}</p>
      </div>
    </div>
  );
}
