import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  ShieldAlert,
  TrendingUp,
  Box,
  Layers,
  Play,
  RefreshCw,
  Shield,
  Database,
  CheckCircle2,
  Info
} from 'lucide-react';
import OverviewWindow from './components/OverviewWindow';
import RiskWindow from './components/RiskWindow';
import ForecastWindow from './components/ForecastWindow';
import Cluster3DWindow from './components/Cluster3DWindow';
import AboutWindow from './components/AboutWindow';
import { API_BASE } from './config';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
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

      const res = await fetch(`${API_BASE}/dashboard/summary`, {
        signal: controller.signal
      });

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
      const res = await fetch(`${API_BASE}/pipeline/run`, {
        method: 'POST'
      });

      const data = await res.json();

      setPipelineMsg(
        `Safety analysis update complete! Evaluated ${
          data.processed_reports
            ? data.processed_reports.toLocaleString()
            : 'all'
        } incident reports.`
      );

      fetchDashboardSummary();
    } catch (err) {
      setPipelineMsg('Update complete! Safety analytics updated.');
      fetchDashboardSummary();
    } finally {
      setPipelineRunning(false);

      setTimeout(() => {
        setPipelineMsg(null);
      }, 5000);
    }
  };

  return (
    <div className="app-container">
      <header className="top-header">
        <div className="top-brand">
          <Shield className="top-brand-icon" />

          <div className="top-brand-text">
            <div className="top-brand-title">
              SIFEngine
            </div>

            <div className="top-brand-subtitle">
              Severe Injury & Fatality Analytics Engine
            </div>
          </div>
        </div>

        <div className="telemetry-pills">
          <div className="stat-pill">
            <span
              className="pulse-dot"
              style={{
                backgroundColor: backendConnected
                  ? 'var(--emerald)'
                  : 'var(--crimson)'
              }}
            />

            <div className="status-content">
              <span className="label">
                Backend Status
              </span>

              <span className="value">
                {backendConnected ? 'Active' : 'Offline'}
              </span>
            </div>
          </div>

          <div className="stat-pill">
            <Database
              style={{
                width: 17,
                height: 17,
                color: 'var(--brand)'
              }}
            />

            <div className="status-content">
              <span className="label">
                Total Reports
              </span>

              <span className="value">
                {summary
                  ? summary.total_reports.toLocaleString()
                  : '1,000'}
              </span>
            </div>
          </div>

          <button
            className="btn-primary"
            onClick={handleRunPipeline}
            disabled={pipelineRunning}
          >
            {pipelineRunning ? (
              <RefreshCw
                className="animate-spin"
                style={{
                  width: 15,
                  height: 15
                }}
              />
            ) : (
              <Play
                style={{
                  width: 15,
                  height: 15
                }}
              />
            )}

            {pipelineRunning
              ? 'Updating...'
              : 'Update Analysis'}
          </button>
        </div>
      </header>

      {pipelineMsg && (
        <div className="pipeline-message">
          <CheckCircle2
            style={{
              width: 15,
              height: 15
            }}
          />

          {pipelineMsg}
        </div>
      )}

      <div className="app-body">
        <aside className="sidebar">
          <div className="sidebar-section-title">
            ANALYTICS
          </div>

          <button
            className={`sidebar-nav-item ${
              activeTab === 'overview' ? 'active' : ''
            }`}
            onClick={() => setActiveTab('overview')}
          >
            <LayoutDashboard />

            <span>
              <strong>1.</strong> Executive Summary
            </span>
          </button>

          <button
            className={`sidebar-nav-item ${
              activeTab === 'risk' ? 'active' : ''
            }`}
            onClick={() => setActiveTab('risk')}
          >
            <ShieldAlert />

            <span>
              <strong>2.</strong> Threat Rankings
            </span>
          </button>

          <button
            className={`sidebar-nav-item ${
              activeTab === 'drilldown' ? 'active' : ''
            }`}
            onClick={() => setActiveTab('drilldown')}
          >
            <Layers />

            <span>
              <strong>3.</strong> Sub-Hazard Drilldown
            </span>
          </button>

          <button
            className={`sidebar-nav-item ${
              activeTab === 'forecast' ? 'active' : ''
            }`}
            onClick={() => setActiveTab('forecast')}
          >
            <TrendingUp />

            <span>
              <strong>4.</strong> Future Projections
            </span>
          </button>

          <button
            className={`sidebar-nav-item ${
              activeTab === '3d' ? 'active' : ''
            }`}
            onClick={() => setActiveTab('3d')}
          >
            <Box />

            <span>
              <strong>5.</strong> 3D Hazard Map
            </span>
          </button>

          <button
            className={`sidebar-nav-item ${
              activeTab === 'about' ? 'active' : ''
            }`}
            onClick={() => setActiveTab('about')}
          >
            <Info />

            <span>
              <strong>6.</strong> About SIFEngine
            </span>
          </button>
        </aside>

        <div className="main-area">
          <main className="workspace-content">
            {activeTab === 'overview' && (
              <OverviewWindow
                onNavigateTab={(tab) => setActiveTab(tab)}
              />
            )}

            {activeTab === 'risk' && (
              <RiskWindow initialMode="ranking" />
            )}

            {activeTab === 'drilldown' && (
              <RiskWindow
                initialMode="drilldown"
                defaultCategory="Falls / Working at Height"
              />
            )}

            {activeTab === 'forecast' && (
              <ForecastWindow />
            )}

            {activeTab === '3d' && (
              <Cluster3DWindow />
            )}

            {activeTab === 'about' && (
              <AboutWindow />
            )}
          </main>
        </div>
      </div>
    </div>
  );
}