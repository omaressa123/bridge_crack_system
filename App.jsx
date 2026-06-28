import React, { useState, useEffect } from 'react';
import './App.css';
import Dashboard from './components/Dashboard';
import CrackDetection from './components/CrackDetection';
import SensorMonitor from './components/SensorMonitor';
import InspectionReport from './components/InspectionReport';
import Header from './components/Header';
import Navigation from './components/Navigation';

const API_URL = 'http://localhost:8000';

export default function App() {
  const [language, setLanguage] = useState('en'); // 'en' or 'ar'
  const [currentTab, setCurrentTab] = useState('dashboard'); // dashboard, cracks, sensors, report
  const [bridgeId, setBridgeId] = useState(null);
  const [bridges, setBridges] = useState([]);
  const [isConnected, setIsConnected] = useState(false);

  // Fetch bridges from backend on load
  useEffect(() => {
    const fetchBridges = async () => {
      try {
        const response = await fetch(`${API_URL}/bridges`);
        const data = await response.json();
        setBridges(data.bridges || []);
        if (data.bridges && data.bridges.length > 0 && !bridgeId) {
          setBridgeId(data.bridges[0].id);
        }
      } catch (error) {
        console.error('Failed to fetch bridges:', error);
      }
    };
    fetchBridges();
  }, []);

  // WebSocket connection to Raspberry Pi
  useEffect(() => {
    let ws;
    let reconnectTimer;

    const connect = () => {
      ws = new WebSocket('ws://localhost:8000/ws');
      
      ws.onopen = () => {
        setIsConnected(true);
        console.log(' Connected to Raspberry Pi');
      };
      
      ws.onerror = () => {
        setIsConnected(false);
        console.error(' Failed to connect to Raspberry Pi');
      };
      
      ws.onclose = () => {
        setIsConnected(false);
        console.log(' Disconnected, trying to reconnect...');
        // Auto-reconnect after 3 seconds without page reload
        reconnectTimer = setTimeout(connect, 3000);
      };
    };

    connect();
    
    return () => {
      if (ws) ws.close();
      if (reconnectTimer) clearTimeout(reconnectTimer);
    };
  }, []);

  const translations = {
    en: {
      appTitle: 'Bridge Crack Detection',
      dashboard: 'Dashboard',
      cracks: 'Crack Detection',
      sensors: 'Sensors',
      report: 'Report',
      bridgeName: 'Bridge Name',
      selectBridge: 'Select Bridge',
      status: 'Status',
      connected: 'Connected',
      disconnected: 'Disconnected',
      language: 'اللغة العربية',
    },
    ar: {
      appTitle: 'نظام كشف شروخ الجسور',
      dashboard: 'لوحة التحكم',
      cracks: 'كشف الشروخ',
      sensors: 'المستشعرات',
      report: 'التقرير',
      bridgeName: 'اسم الجسر',
      selectBridge: 'اختر الجسر',
      status: 'الحالة',
      connected: 'متصل',
      disconnected: 'غير متصل',
      language: 'English',
    }
  };

  const t = translations[language];

  return (
    <div className={`app ${language === 'ar' ? 'rtl' : 'ltr'}`}>
      <Header 
        language={language} 
        setLanguage={setLanguage}
        t={t}
        isConnected={isConnected}
        bridges={bridges}
        bridgeId={bridgeId}
        setBridgeId={setBridgeId}
      />
      
      <div className="app-container">
        <div className="main-content">
          {currentTab === 'dashboard' && (
            <Dashboard language={language} t={t} bridgeId={bridgeId} />
          )}
          {currentTab === 'cracks' && (
            <CrackDetection language={language} t={t} bridgeId={bridgeId} />
          )}
          {currentTab === 'sensors' && (
            <SensorMonitor language={language} t={t} bridgeId={bridgeId} />
          )}
          {currentTab === 'report' && (
            <InspectionReport language={language} t={t} bridgeId={bridgeId} />
          )}
        </div>
      </div>

      <Navigation 
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        language={language}
        t={t}
      />
    </div>
  );
}
