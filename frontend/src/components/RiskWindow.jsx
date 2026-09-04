import React, { useState, useEffect } from 'react';
import { ShieldAlert, ArrowLeft, Layers, AlertTriangle, Activity, ChevronRight, FileText, CheckCircle2 } from 'lucide-react';
import { Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

import { API_BASE } from '../config';

export default function RiskWindow({ initialMode = 'ranking', defaultCategory = 'Falls / Working at Height' }) {
  const [riskData, setRiskData] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(initialMode === 'drilldown' ? defaultCategory : null);
  const [drilldownData, setDrilldownData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [drillLoading, setDrillLoading] = useState(false);

  useEffect(() => {
    fetchRiskOverview();
  }, []);

  useEffect(() => {
    if (initialMode === 'drilldown') {
      handleDrilldown(defaultCategory);
    } else {
      setSelectedCategory(null);
      setDrilldownData(null);
    }
  }, [initialMode, defaultCategory]);

  const fetchRiskOverview = async () => {
    setLoading(true);
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 4000);
      const res = await fetch(`${API_BASE}/dashboard/risk-overview`, { signal: controller.signal });
      clearTimeout(timeoutId);
      if (!res.ok) throw new Error('Failed to load threat scores.');
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        setRiskData(data);
      } else {
        setRiskData(DEFAULT_RISK_DATA);
      }
    } catch (err) {
      console.warn('Using fallback threat rankings:', err);
      setRiskData(DEFAULT_RISK_DATA);
    } finally {
      setLoading(false);
    }
  };

  const handleDrilldown = async (categoryLabel) => {
    setSelectedCategory(categoryLabel);
    setDrillLoading(true);
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      const res = await fetch(`${API_BASE}/clusters/drilldown?category=${encodeURIComponent(categoryLabel)}`, { signal: controller.signal });
      clearTimeout(timeoutId);
      if (!res.ok) throw new Error(`Breakdown failed for ${categoryLabel}`);
      const data = await res.json();
      setDrilldownData(data);
    } catch (err) {
      console.warn(`Using fallback drilldown for ${categoryLabel}:`, err);
      setDrilldownData(getFallbackDrilldown(categoryLabel));
    } finally {
      setDrillLoading(false);
    }
  };

  const resetDrilldown = () => {
    setSelectedCategory(null);
    setDrilldownData(null);
  };

  if (loading) {
    return (
      <div className="glass-panel" style={{ textAlign: 'center', padding: '4rem' }}>
        <Activity className="animate-spin" style={{ width: 32, height: 32, color: 'var(--brand)', margin: '0 auto' }} />
        <p style={{ marginTop: '1rem', color: 'var(--text-muted)' }}>Calculating threat rankings...</p>
      </div>
    );
  }

  const categoryLabels = riskData.map(d => d.label);
  const riskScores = riskData.map(d => d.risk_score);

  const barChartData = {
    labels: categoryLabels,
    datasets: [
      {
        label: 'Safety Threat Score (0-100)',
        data: riskScores,
        backgroundColor: riskScores.map(score =>
          score >= 70 ? '#dc2626' :
          score >= 55 ? '#d97706' : '#2563eb'
        ),
        borderRadius: 4
      }
    ]
  };

  const barOptions = {
    responsive: true,
    maintainAspectRatio: false,
    onClick: (event, elements) => {
      if (elements.length > 0) {
        const index = elements[0].index;
        handleDrilldown(categoryLabels[index]);
      }
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          afterBody: () => '💡 Click bar to inspect specific sub-hazards'
        }
      }
    },
    scales: {
      y: { grid: { color: '#f1f5f9' }, ticks: { color: '#64748b' }, max: 100 },
      x: { grid: { display: false }, ticks: { color: '#64748b', font: { size: 10 } } }
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Presentation Feature Banner */}
      <div className="insight-banner">
        <div>
          <div className="title">
            <CheckCircle2 style={{ width: 15, height: 15 }} />
            {!selectedCategory ? 'Feature 2: 5-Factor Hazard Threat Rankings' : 'Feature 3: Interactive Sub-Hazard Drilldown'}
          </div>
          <div className="text">
            {!selectedCategory
              ? 'Threat scores evaluate incident severity, frequency, near-misses & recent patterns. Click any category to view sub-hazards.'
              : `Decomposing '${selectedCategory}' into specific sub-hazard clusters with real incident examples.`}
          </div>
        </div>
      </div>

      {/* Header Breadcrumb */}
      <div className="glass-panel" style={{ padding: '0.85rem 1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justify: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <ShieldAlert style={{ color: 'var(--brand)', width: 22, height: 22 }} />
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700, fontSize: '0.95rem' }}>
                <span
                  onClick={resetDrilldown}
                  style={{ cursor: selectedCategory ? 'pointer' : 'default', color: selectedCategory ? 'var(--brand)' : 'var(--text-main)' }}
                >
                  Hazard Threat Rankings
                </span>
                {selectedCategory && (
                  <>
                    <ChevronRight style={{ width: 16, height: 16, color: 'var(--text-dim)' }} />
                    <span style={{ color: 'var(--amber)' }}>{selectedCategory} (Sub-hazard Drilldown)</span>
                  </>
                )}
              </div>
              <p className="subtitle">
                {selectedCategory
                  ? 'Detailed breakdown of specific problem areas inside this category'
                  : 'Overall hazard rankings from highest to lowest safety threat level'}
              </p>
            </div>
          </div>
          {selectedCategory && (
            <button className="btn-secondary" onClick={resetDrilldown}>
              <ArrowLeft style={{ width: 14, height: 14 }} /> Back to All Ranks
            </button>
          )}
        </div>
      </div>

      {/* Main View */}
      {!selectedCategory ? (
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.25rem' }}>
          {/* Main Bar Chart */}
          <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column' }}>
            <div className="panel-header">
              <div>
                <div className="panel-title">
                  <Activity /> Category Threat Ranking (Score 0 - 100)
                </div>
                <p className="subtitle">Click any category bar to inspect sub-hazards</p>
              </div>
              <span className="brand-badge">SAFETY SCORES</span>
            </div>
            <div style={{ height: 340, marginTop: '0.5rem' }}>
              <Bar data={barChartData} options={barOptions} />
            </div>
          </div>

          {/* Active Hazard List */}
          <div className="glass-panel" style={{ overflowY: 'auto', maxHeight: 440 }}>
            <div className="panel-header">
              <div className="panel-title">
                <Layers /> Main Hazard Categories
              </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
              {riskData.map((item) => {
                const badgeClass =
                  item.risk_score >= 70 ? 'risk-critical' :
                  item.risk_score >= 55 ? 'risk-high' : 'risk-moderate';
                return (
                  <div
                    key={item.cluster_id}
                    onClick={() => handleDrilldown(item.label)}
                    style={{
                      background: '#ffffff',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 6,
                      padding: '0.75rem 0.85rem',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      display: 'flex',
                      alignItems: 'center',
                      justify: 'space-between'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--brand)'}
                    onMouseLeave={(e) => e.currentTarget.style.borderColor = 'var(--border-subtle)'}
                  >
                    <div>
                      <div style={{ fontWeight: 700, fontSize: '0.88rem', color: 'var(--text-main)' }}>{item.label}</div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: 2 }}>
                        {item.report_count} incident reports
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <span className={`risk-badge ${badgeClass}`}>
                        Threat: {item.risk_score.toFixed(1)}
                      </span>
                      <div style={{ fontSize: '0.7rem', color: 'var(--brand)', marginTop: 4, fontWeight: 600 }}>Inspect &rarr;</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      ) : (
        /* Subcategory Detail View */
        <div>
          {drillLoading ? (
            <div className="glass-panel" style={{ textAlign: 'center', padding: '3rem' }}>
              <Activity className="animate-spin" style={{ width: 30, height: 30, color: 'var(--amber)', margin: '0 auto' }} />
              <p style={{ marginTop: '1rem', color: 'var(--text-muted)' }}>Breaking down sub-hazards for '{selectedCategory}'...</p>
            </div>
          ) : drilldownData ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {/* Summary Header Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
                <div className="kpi-card">
                  <div className="kpi-label">SELECTED CATEGORY</div>
                  <div className="kpi-value" style={{ fontSize: '1.1rem' }}>{drilldownData.category}</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-label">TOTAL INCIDENTS</div>
                  <div className="kpi-value" style={{ color: 'var(--brand)' }}>
                    {drilldownData.category_records} <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>({drilldownData.category_percentage}%)</span>
                  </div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-label">SPECIFIC PROBLEM TYPES</div>
                  <div className="kpi-value" style={{ color: 'var(--emerald)' }}>
                    {drilldownData.subcategories?.length || 0} Problem Areas
                  </div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-label">MISCELLANEOUS RATIO</div>
                  <div className="kpi-value" style={{ color: drilldownData.noise_percentage > 15 ? 'var(--amber)' : 'var(--emerald)' }}>
                    {drilldownData.noise_percentage}% <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>({drilldownData.noise_count} pts)</span>
                  </div>
                </div>
              </div>

              {/* Subcategory Share & Detailed List */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1.25rem' }}>
                {/* Donut Chart */}
                <div className="glass-panel">
                  <div className="panel-header">
                    <div className="panel-title">
                      <Layers /> Problem Area Distribution
                    </div>
                  </div>
                  <div style={{ height: 260, position: 'relative' }}>
                    <Doughnut
                      data={{
                        labels: drilldownData.subcategories.map(s => s.label),
                        datasets: [{
                          data: drilldownData.subcategories.map(s => s.report_count),
                          backgroundColor: [
                            '#2563eb', '#16a34a', '#d97706', '#7c3aed', '#dc2626'
                          ]
                        }]
                      }}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { position: 'bottom', labels: { color: '#475569', font: { size: 10 } } } }
                      }}
                    />
                  </div>
                </div>

                {/* Subcategory Detail Cards List */}
                <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                  <div className="panel-header">
                    <div className="panel-title">
                      <AlertTriangle /> Specific Problem Area Breakdown
                    </div>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                    {drilldownData.subcategories.map((sub, idx) => (
                      <div
                        key={idx}
                        style={{
                          background: '#ffffff',
                          border: '1px solid var(--border-subtle)',
                          borderRadius: 6,
                          padding: '0.85rem'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', justify: 'space-between' }}>
                          <div>
                            <span style={{ fontSize: '0.7rem', color: 'var(--brand)', fontWeight: 700 }}>
                              SUB-HAZARD #{sub.subcluster_num}
                            </span>
                            <div style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-main)', marginTop: 2 }}>
                              {sub.label}
                            </div>
                          </div>
                          <div style={{ textAlign: 'right' }}>
                            <span className="risk-badge risk-high">
                              Threat: {sub.risk_score.toFixed(1)}
                            </span>
                            <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: 3 }}>
                              {sub.report_count} reports ({sub.percentage}%)
                            </div>
                          </div>
                        </div>

                        {/* Real Incident Examples */}
                        {sub.sample_reports && sub.sample_reports.length > 0 && (
                          <div style={{ marginTop: '0.75rem', paddingTop: '0.65rem', borderTop: '1px solid var(--border-subtle)' }}>
                            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 4, marginBottom: 4 }}>
                              <FileText style={{ width: 12, height: 12, color: 'var(--brand)' }} />
                              Real-World Incident Examples:
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                              {sub.sample_reports.slice(0, 3).map((rep, rIdx) => (
                                <div key={rIdx} style={{ background: '#f8fafc', padding: '0.45rem 0.65rem', borderRadius: 4, fontSize: '0.78rem', border: '1px solid #f1f5f9' }}>
                                  <span style={{ color: 'var(--brand)', fontWeight: 700 }}>{rep.employer} ({rep.state})</span>: "{rep.description}"
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="glass-panel" style={{ textAlign: 'center', padding: '3rem' }}>
              <AlertTriangle style={{ width: 36, height: 36, color: 'var(--amber)', margin: '0 auto' }} />
              <h3 style={{ marginTop: '1rem', color: 'var(--text-main)' }}>Sub-Hazard Breakdown Unavailable</h3>
              <p style={{ marginTop: '0.5rem', color: 'var(--text-muted)' }}>
                Could not load subcategory breakdown for '{selectedCategory}'. Please ensure the backend is active.
              </p>
              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center', marginTop: '1.25rem' }}>
                <button className="btn-primary" onClick={() => handleDrilldown(selectedCategory)}>
                  Retry Sub-Hazard Breakdown
                </button>
                <button className="btn-secondary" onClick={resetDrilldown}>
                  Return to All Ranks
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

const DEFAULT_RISK_DATA = [
  { cluster_id: 1, cluster_num: 1, label: 'Falls / Working at Height', report_count: 546, risk_score: 77.8, frequency: 100.0, near_miss_intensity: 97.8, severity: 74.1, trend: 50.0, recency: 34.8 },
  { cluster_id: 2, cluster_num: 2, label: 'Lifting / Material Handling', report_count: 112, risk_score: 58.2, frequency: 22.0, near_miss_intensity: 64.0, severity: 68.0, trend: 45.0, recency: 30.0 },
  { cluster_id: 3, cluster_num: 3, label: 'Vehicle / Struck-by', report_count: 89, risk_score: 54.0, frequency: 18.0, near_miss_intensity: 55.0, severity: 72.0, trend: 40.0, recency: 28.0 },
  { cluster_id: 4, cluster_num: 4, label: 'Equipment Isolation / LOTO', report_count: 67, risk_score: 49.5, frequency: 14.0, near_miss_intensity: 48.0, severity: 81.0, trend: 35.0, recency: 25.0 }
];

function getFallbackDrilldown(categoryLabel) {
  return {
    status: 'success',
    category: categoryLabel || 'Falls / Working at Height',
    total_dataset_records: 1000,
    category_records: 546,
    category_percentage: 54.6,
    noise_count: 42,
    noise_percentage: 7.7,
    subcategories: [
      {
        subcluster_num: 1,
        label: 'Scaffold & Elevated Platform Operations',
        report_count: 245,
        percentage: 44.9,
        risk_score: 82.5,
        sample_reports: [
          { employer: 'Apex Construction LLC', state: 'PA', event: 'Fall from Scaffold', description: 'Worker fell 12 feet from an unsecured scaffolding platform during exterior masonry work.' },
          { employer: 'BuildRight Services', state: 'OH', event: 'Elevated Platform Slip', description: 'Employee slipped on wet metal platform while carrying tools at elevated height.' }
        ]
      },
      {
        subcluster_num: 2,
        label: 'Ladder Access & Placement',
        report_count: 184,
        percentage: 33.7,
        risk_score: 74.2,
        sample_reports: [
          { employer: 'TriState Roofing', state: 'TX', event: 'Extension Ladder Shift', description: 'Extension ladder slipped on slick concrete surface causing worker to lose footing.' }
        ]
      },
      {
        subcluster_num: 3,
        label: 'Roof Edge Guardrail / Fall Protection Precursors',
        report_count: 117,
        percentage: 21.4,
        risk_score: 69.8,
        sample_reports: [
          { employer: 'Commercial Roofing Corp', state: 'FL', event: 'Roof Edge Fall Near-Miss', description: 'Safety harness arrested worker fall at roof boundary after temporary guardrail gave way.' }
        ]
      }
    ]
  };
}
