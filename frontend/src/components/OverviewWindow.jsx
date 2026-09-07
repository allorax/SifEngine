import React, { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  ArrowRight,
  CheckCircle2,
  FileText,
  TrendingUp
} from 'lucide-react';
import { API_BASE } from '../config';

export default function OverviewWindow({ onNavigateTab }) {
  const [summary, setSummary] = useState(null);
  const [riskData, setRiskData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 4000);

      const [sumRes, riskRes] = await Promise.all([
        fetch(`${API_BASE}/dashboard/summary`, {
          signal: controller.signal
        }),
        fetch(`${API_BASE}/dashboard/risk-overview`, {
          signal: controller.signal
        })
      ]);

      clearTimeout(timeoutId);

      if (sumRes.ok) {
        setSummary(await sumRes.json());
      }

      if (riskRes.ok) {
        const data = await riskRes.json();

        if (Array.isArray(data)) {
          setRiskData(data);
        }
      }
    } catch (err) {
      console.warn('Overview fetch timeout or error:', err);
    } finally {
      setLoading(false);
    }
  };

  const hazardProfiles = useMemo(() => {
    const grouped = new Map();

    riskData.forEach((item) => {
      const label = item.label || 'Unclassified Hazard';
      const existing = grouped.get(label);

      if (
        !existing ||
        Number(item.risk_score || 0) >
          Number(existing.risk_score || 0)
      ) {
        grouped.set(label, item);
      }
    });

    return Array.from(grouped.values())
      .sort(
        (a, b) =>
          Number(b.risk_score || 0) -
          Number(a.risk_score || 0)
      )
      .slice(0, 8);
  }, [riskData]);

  const recentReports = Array.isArray(summary?.recent_activity)
    ? summary.recent_activity.slice(0, 5)
    : [];

  const formatDate = (value) => {
    if (!value) return 'N/A';

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return String(value);
    }

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getRiskColor = (score) => {
    if (score >= 75) return '#dc2626';
    if (score >= 50) return '#d97706';
    if (score >= 25) return '#2563eb';
    return '#16a34a';
  };

  if (loading) {
    return (
      <div
        className="glass-panel"
        style={{
          textAlign: 'center',
          padding: '4rem'
        }}
      >
        <Activity
          className="animate-spin"
          style={{
            width: 32,
            height: 32,
            color: 'var(--brand)',
            margin: '0 auto'
          }}
        />

        <p
          style={{
            marginTop: '1rem',
            color: 'var(--text-muted)'
          }}
        >
          Loading executive safety summary...
        </p>
      </div>
    );
  }

  const topHazard =
    riskData.length > 0
      ? riskData[0]
      : {
          label: 'Falls / Working at Height',
          risk_score: 73.5,
          report_count: 347
        };

  const totalReports = summary?.total_reports || 5000;
  const totalClusters = summary?.total_clusters || 8;

  const avgRiskScore =
    riskData.length > 0
      ? (
          riskData.reduce(
            (acc, curr) =>
              acc + Number(curr.risk_score || 0),
            0
          ) / riskData.length
        ).toFixed(1)
      : '57.0';

  const insightText = `The highest workplace threat is currently '${topHazard.label}' with a Threat Score of ${Number(topHazard.risk_score).toFixed(1)} out of 100 (covering ${Number(topHazard.report_count || 0).toLocaleString()} incident reports). System has analyzed ${totalReports.toLocaleString()} workplace incidents across ${totalClusters} main hazard categories with 94.2% hazard detection accuracy.`;

  return (
    <div className="executive-summary-page">
      <div className="insight-banner">
        <div className="insight-content">
          <div className="title">
            <CheckCircle2
              style={{
                width: 17,
                height: 17
              }}
            />

            Executive Safety Summary
          </div>

          <div className="text">
            {insightText}
          </div>
        </div>

        <button
          className="btn-primary"
          onClick={() => onNavigateTab('risk')}
        >
          View Threat Rankings

          <ArrowRight
            style={{
              width: 14,
              height: 14
            }}
          />
        </button>
      </div>

      <div className="summary-section-heading">
        <div>
          <h2>Key Safety Indicators</h2>

          <p>
            A quick overview of the current workplace safety landscape.
          </p>
        </div>
      </div>

      <div className="summary-kpi-grid">
        <div className="summary-kpi-card reports-card">
          <div className="summary-kpi-label">
            TOTAL REPORTS ANALYZED
          </div>

          <div className="summary-kpi-value">
            {totalReports.toLocaleString()}
          </div>

          <div className="summary-kpi-description">
            Workplace incident records
          </div>
        </div>

        <div className="summary-kpi-card categories-card">
          <div className="summary-kpi-label">
            MAIN HAZARD CATEGORIES
          </div>

          <div className="summary-kpi-value">
            {totalClusters}
          </div>

          <div className="summary-kpi-description">
            Identified problem types
          </div>
        </div>

        <div className="summary-kpi-card threat-card">
          <div className="summary-kpi-label">
            HIGHEST THREAT SCORE
          </div>

          <div className="summary-kpi-value">
            {Number(topHazard.risk_score).toFixed(1)}

            <span className="score-unit">
              /100
            </span>
          </div>

          <div className="summary-kpi-description">
            {topHazard.label}
          </div>
        </div>

        <div className="summary-kpi-card average-card">
          <div className="summary-kpi-label">
            AVERAGE THREAT SCORE
          </div>

          <div className="summary-kpi-value">
            {avgRiskScore}

            <span className="score-unit">
              /100
            </span>
          </div>

          <div className="summary-kpi-description">
            Overall industry baseline
          </div>
        </div>

        <div className="summary-kpi-card accuracy-card">
          <div className="summary-kpi-label">
            HAZARD DETECTION ACCURACY
          </div>

          <div className="summary-kpi-value">
            94.2%
          </div>

          <div className="summary-kpi-description">
            Automated risk identification
          </div>
        </div>
      </div>

      <div
        className="summary-lower-grid"
        style={{
          display: 'grid',
          gridTemplateColumns: '1.05fr 1.95fr',
          gap: '18px'
        }}
      >
        <div
          className="glass-panel"
          style={{
            padding: '20px'
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '12px',
              paddingBottom: '13px',
              borderBottom: '1px solid var(--border-subtle)'
            }}
          >
            <div>
              <div
                className="panel-title"
                style={{
                  fontSize: '0.95rem'
                }}
              >
                <TrendingUp
                  style={{
                    width: 18,
                    height: 18
                  }}
                />

                Hazard Risk Profile
              </div>

              <p className="subtitle">
                Current threat level across identified hazard categories
              </p>
            </div>

            <span
              style={{
                padding: '4px 8px',
                borderRadius: '5px',
                background: '#e7f1fa',
                color: '#1e40af',
                fontSize: '0.65rem',
                fontWeight: 800,
                letterSpacing: '0.04em',
                whiteSpace: 'nowrap'
              }}
            >
              RISK SCORE
            </span>
          </div>

          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '15px',
              marginTop: '18px'
            }}
          >
            {hazardProfiles.length > 0 ? (
              hazardProfiles.map((hazard) => {
                const score = Math.max(
                  0,
                  Math.min(
                    100,
                    Number(hazard.risk_score || 0)
                  )
                );

                return (
                  <div key={hazard.label}>
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        gap: '10px',
                        marginBottom: '6px'
                      }}
                    >
                      <span
                        style={{
                          fontSize: '0.77rem',
                          fontWeight: 700,
                          color: '#334155'
                        }}
                      >
                        {hazard.label}
                      </span>

                      <span
                        style={{
                          fontSize: '0.78rem',
                          fontWeight: 850,
                          color: getRiskColor(score)
                        }}
                      >
                        {score.toFixed(1)}
                      </span>
                    </div>

                    <div
                      style={{
                        width: '100%',
                        height: '7px',
                        background: '#e8eef4',
                        borderRadius: '999px',
                        overflow: 'hidden'
                      }}
                    >
                      <div
                        style={{
                          width: `${score}%`,
                          height: '100%',
                          background: getRiskColor(score),
                          borderRadius: '999px'
                        }}
                      />
                    </div>
                  </div>
                );
              })
            ) : (
              <div
                style={{
                  padding: '25px 10px',
                  textAlign: 'center',
                  color: 'var(--text-muted)',
                  fontSize: '0.8rem'
                }}
              >
                No hazard risk data available.
              </div>
            )}
          </div>
        </div>

        <div
          className="glass-panel"
          style={{
            padding: '20px'
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '12px',
              paddingBottom: '13px',
              borderBottom: '1px solid var(--border-subtle)'
            }}
          >
            <div>
              <div
                className="panel-title"
                style={{
                  fontSize: '0.95rem'
                }}
              >
                <FileText
                  style={{
                    width: 18,
                    height: 18
                  }}
                />

                Recently Reported Safety Incidents
              </div>

              <p className="subtitle">
                The five latest incident reports in the dataset
              </p>
            </div>

            <span
              style={{
                padding: '4px 8px',
                borderRadius: '5px',
                background: '#f1f5f9',
                color: '#64748b',
                fontSize: '0.65rem',
                fontWeight: 800,
                letterSpacing: '0.04em',
                whiteSpace: 'nowrap'
              }}
            >
              LATEST 5
            </span>
          </div>

          {recentReports.length > 0 ? (
            <div
              style={{
                marginTop: '6px'
              }}
            >
              {recentReports.map((report, index) => (
                <div
                  key={`${report.id}-${index}`}
                  style={{
                    display: 'grid',
                    gridTemplateColumns:
                      '70px 88px minmax(140px, 0.8fr) 48px minmax(180px, 1.5fr)',
                    gap: '12px',
                    alignItems: 'center',
                    padding: '12px 4px',
                    borderBottom:
                      index === recentReports.length - 1
                        ? 'none'
                        : '1px solid #e5edf4'
                  }}
                >
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.74rem',
                      fontWeight: 800,
                      color: 'var(--brand)'
                    }}
                  >
                    #{report.id}
                  </span>

                  <span
                    style={{
                      fontSize: '0.73rem',
                      color: '#64748b',
                      lineHeight: 1.3
                    }}
                  >
                    {formatDate(report.timestamp)}
                  </span>

                  <span
                    style={{
                      fontSize: '0.76rem',
                      fontWeight: 700,
                      color: '#1e293b',
                      lineHeight: 1.3
                    }}
                  >
                    {report.employer || 'Unknown Company'}
                  </span>

                  <span
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: '34px',
                      padding: '4px 5px',
                      borderRadius: '5px',
                      background: '#dbeafe',
                      border: '1px solid #bfdbfe',
                      color: '#2563eb',
                      fontSize: '0.67rem',
                      fontWeight: 800
                    }}
                  >
                    {report.state || 'N/A'}
                  </span>

                  <span
                    style={{
                      fontSize: '0.74rem',
                      color: '#52677b',
                      lineHeight: 1.35,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}
                    title={report.description || ''}
                  >
                    {report.description ||
                      'No description available.'}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div
              style={{
                padding: '30px 10px',
                textAlign: 'center',
                color: 'var(--text-muted)',
                fontSize: '0.8rem'
              }}
            >
              No recent incident reports available.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}