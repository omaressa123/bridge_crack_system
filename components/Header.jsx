import React from 'react';

export default function Header({ language, setLanguage, t, isConnected, bridges, bridgeId, setBridgeId, user, onSignOut, onOpenAdmin }) {
  return (
    <header className="app-header">
      <div className="header-content">
        <div className="header-title">
          <h1>{t.appTitle}</h1>
          <p className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? '🟢 ' + t.connected : '🔴 ' + t.disconnected}
          </p>
        </div>

        <div className="bridge-selector">
          <label>{t.selectBridge}:</label>
          <select 
            value={bridgeId || ''} 
            onChange={(e) => setBridgeId(parseInt(e.target.value))}
          >
            {bridges.map(bridge => (
              <option key={bridge.id} value={bridge.id}>
                {bridge.name} ({bridge.city})
              </option>
            ))}
          </select>
        </div>
        
        <div className="header-right">
          {onOpenAdmin && (
            <button className="language-btn admin-entry-btn" onClick={onOpenAdmin} type="button">
              {language === 'en' ? '⚙ Admin' : '⚙ الإدارة'}
            </button>
          )}
          {user && (
            <div className="user-profile">
              <img src={user.picture} alt={user.name} className="user-avatar" referrerPolicy="no-referrer" />
              <span className="user-name">{user.name}</span>
              <button className="signout-btn" onClick={onSignOut}>
                {language === 'en' ? 'Sign Out' : 'خروج'}
              </button>
            </div>
          )}
          
          <button 
            className="language-btn"
            onClick={() => setLanguage(language === 'en' ? 'ar' : 'en')}
          >
            {t.language}
          </button>
        </div>
      </div>
    </header>
  );
}
