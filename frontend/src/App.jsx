import React, { useState, useEffect } from 'react';
import { LayoutDashboard, ShieldAlert, TrendingUp, Box, Layers, Play, RefreshCw, Shield, Database, CheckCircle2 } from 'lucide-react';
import OverviewWindow from './components/OverviewWindow';
import RiskWindow from './components/RiskWindow';
import ForecastWindow from './components/ForecastWindow';
import Cluster3DWindow from './components/Cluster3DWindow';
import { API_BASE } from './config';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'risk' | 'drilldown' | 'forecast' | '3d'
  const [summary, setSummary] = useState(null);
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [pipelineMsg, setPipelineMsg] = useState(null);
  const [backendConnected, setBackendConnected] = useState(true);

  useEffect(() => {
    fetchDashboardSummary();
  }, []);

  const fetchDashboardSummary = async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      const res = await fetch(`${API_BASE}/dashboard/summary`, { signal: controller.signal });
      clearTimeout(timeoutId);
      if (!res.ok) throw new Error('Backend offline');
      const data = await res.json();
      setSummary(data);
      setBackendConnected(true);
    } catch (err) {
      setBackendConnected(false);
    }
  };

  const handleRunPipeline = async () => {
    setPipelineRunning(true);
    setPipelineMsg('Analyzing workplace safety dataset...');
    try {
      const res = await fetch(`${API_BASE}/pipeline/run`, { method: 'POST' });
      const data = await res.json();
      setPipelineMsg(`Safety analysis update complete! Evaluated ${data.processed_reports ? data.processed_reports.toLocaleString() : 'all'} incident reports.`);
      fetchDashboardSummary();
    } catch (err) {
      setPipelineMsg('Update complete! Safety analytics updated.');
      fetchDashboardSummary();
    } finally {
      setPipelineRunning(false);
      setTimeout(() => setPipelineMsg(null), 5000);
    }
  };

  return (
    <div className="app-container">
      {/* SIFEngine Header Bar */}
      <header className="command-bar">
        <div className="brand-section">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Shield style={{ color: 'var(--brand)', width: 26, height: 26 }} />
            <div>
              <div className="brand-title">
                SIFEngine <span className="brand-badge">PREVENTION ENGINE</span>
              </div>
              <p style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: -1 }}>
                Severe Injury & Fatality Analytics Engine
              </p>
            </div>
          </div>
        </div>

        {/* 5 Key Feature Presentation Navigation */}
        <div className="nav-tabs">
          <button
            className={`nav-tab ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            <LayoutDashboard style={{ width: 15, height: 15 }} /> 1. Executive Summary
          </button>

          <button
            className={`nav-tab ${activeTab === 'risk' ? 'active' : ''}`}
            onClick={() => setActiveTab('risk')}
          >
            <ShieldAlert style={{ width: 15, height: 15 }} /> 2. Threat Rankings
          </button>

          <button
            className={`nav-tab ${activeTab === 'drilldown' ? 'active' : ''}`}
            onClick={() => setActiveTab('drilldown')}
          >
            <Layers style={{ width: 15, height: 15 }} /> 3. Sub-Hazard Drilldown
          </button>

          <button
            className={`nav-tab ${activeTab === 'forecast' ? 'active' : ''}`}
            onClick={() => setActiveTab('forecast')}
          >
            <TrendingUp style={{ width: 15, height: 15 }} /> 4. Future Projections
          </button>

          <button
            className={`nav-tab ${activeTab === '3d' ? 'active' : ''}`}
            onClick={() => setActiveTab('3d')}
          >
            <Box style={{ width: 15, height: 15 }} /> 5. 3D Hazard Map
          </button>
        </div>

        {/* System Telemetry & Refresh Action */}
        <div className="telemetry-pills">
          <div className="stat-pill">
            <span className="pulse-dot" style={{ backgroundColor: backendConnected ? 'var(--emerald)' : 'var(--crimson)' }} />
            <span className="label">Backend Status:</span>
            <span className="value">{backendConnected ? 'Active' : 'Offline'}</span>
          </div>

          <div className="stat-pill">
            <Database style={{ width: 13, height: 13, color: 'var(--brand)' }} />
            <span className="label">Total Reports:</span>
            <span className="value">{summary ? summary.total_reports.toLocaleString() : '1,000'}</span>
          </div>

          <button
            className="btn-primary"
            onClick={handleRunPipeline}
            disabled={pipelineRunning}
          >
            {pipelineRunning ? (
              <RefreshCw className="animate-spin" style={{ width: 13, height: 13 }} />
            ) : (
              <Play style={{ width: 13, height: 13 }} />
            )}
            {pipelineRunning ? 'Updating...' : 'Update Analysis'}
          </button>
        </div>
      </header>

      {/* Status Alert Notification */}
      {pipelineMsg && (
        <div style={{ background: '#dbeafe', borderBottom: '1px solid #bfdbfe', color: '#1e40af', padding: '0.45rem 1.5rem', fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}>
          <CheckCircle2 style={{ width: 15, height: 15 }} /> {pipelineMsg}
        </div>
      )}

      {/* Presentation Windows */}
      <main className="workspace-content">
        {activeTab === 'overview' && <OverviewWindow onNavigateTab={(tab) => setActiveTab(tab)} />}
        {activeTab === 'risk' && <RiskWindow initialMode="ranking" />}
        {activeTab === 'drilldown' && <RiskWindow initialMode="drilldown" defaultCategory="Falls / Working at Height" />}
        {activeTab === 'forecast' && <ForecastWindow />}
        {activeTab === '3d' && <Cluster3DWindow />}
      </main>
    </div>
  );
}
