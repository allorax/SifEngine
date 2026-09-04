import React, { useState, useEffect } from 'react';
import { Search, Filter, FileText, Sparkles, Activity, X, ChevronLeft, ChevronRight, CheckCircle2 } from 'lucide-react';

import { API_BASE } from '../config';

export default function IncidentExplorerWindow({ searchQuery }) {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [offset, setOffset] = useState(0);
  const [limit] = useState(25);
  const [selectedReportForSimilarity, setSelectedReportForSimilarity] = useState(null);
  const [similarResults, setSimilarResults] = useState(null);
  const [similarityLoading, setSimilarityLoading] = useState(false);
  const [stateFilter, setStateFilter] = useState('');

  useEffect(() => {
    fetchReports();
  }, [offset, stateFilter]);

  const fetchReports = async () => {
    setLoading(true);
    try {
      let url = `${API_BASE}/reports?limit=${limit}&offset=${offset}`;
      if (stateFilter) url += `&state=${encodeURIComponent(stateFilter)}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch reports');
      const data = await res.json();
      setReports(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenSimilarity = async (report) => {
    setSelectedReportForSimilarity(report);
    setSimilarityLoading(true);
    setSimilarResults(null);
    try {
      const res = await fetch(`${API_BASE}/reports/${report.id}/similar?top_n=5`);
      if (!res.ok) throw new Error('Failed to load similar incidents');
      const data = await res.json();
      setSimilarResults(data);
    } catch (err) {
      console.error(err);
    } finally {
      setSimilarityLoading(false);
    }
  };

  const filteredReports = reports.filter(r => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      r.description?.toLowerCase().includes(q) ||
      r.employer?.toLowerCase().includes(q) ||
      r.event?.toLowerCase().includes(q) ||
      r.state?.toLowerCase().includes(q)
    );
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Layman Takeaway Banner */}
      <div className="insight-banner">
        <div>
          <div className="title">
            <CheckCircle2 style={{ width: 15, height: 15 }} /> Incident Search & Matching Guide
          </div>
          <div className="text">
            Search workplace incident records by company name, location state, or keyword. Click 'Find Matching Incidents' on any row to automatically locate similar past workplace incidents.
          </div>
        </div>
      </div>

      {/* Header & Controls Panel */}
      <div className="glass-panel" style={{ padding: '0.85rem 1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <FileText style={{ color: 'var(--brand)', width: 22, height: 22 }} />
            <div>
              <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-main)' }}>
                Workplace Incident Search & Matching
              </div>
              <p className="subtitle">
                Browse workplace safety reports and find matching incidents across the dataset
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', color: 'var(--text-dim)' }}>
              <Filter style={{ width: 14, height: 14 }} /> Location State:
            </div>
            <select
              value={stateFilter}
              onChange={(e) => { setStateFilter(e.target.value); setOffset(0); }}
              className="filter-select"
            >
              <option value="">All States</option>
              <option value="PA">Pennsylvania (PA)</option>
              <option value="OH">Ohio (OH)</option>
              <option value="TX">Texas (TX)</option>
              <option value="FL">Florida (FL)</option>
              <option value="CA">California (CA)</option>
              <option value="IL">Illinois (IL)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Reports Data Table */}
      <div className="glass-panel">
        {loading ? (
          <div style={{ textAlign: 'center', padding: '3rem' }}>
            <Activity className="animate-spin" style={{ width: 32, height: 32, color: 'var(--brand)', margin: '0 auto' }} />
            <p style={{ marginTop: '1rem', color: 'var(--text-muted)' }}>Loading incident records...</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Report ID</th>
                  <th>Employer / Company</th>
                  <th>State</th>
                  <th>Incident Type</th>
                  <th>Incident Description</th>
                  <th>Find Matching</th>
                </tr>
              </thead>
              <tbody>
                {filteredReports.map((r) => {
                  return (
                    <tr key={r.id}>
                      <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--brand)' }}>
                        #{r.id}
                      </td>
                      <td style={{ fontWeight: 600, color: 'var(--text-main)' }}>{r.employer || 'Unknown Company'}</td>
                      <td>
                        <span className="risk-badge risk-moderate">{r.state || 'N/A'}</span>
                      </td>
                      <td style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>{r.event || 'General Incident'}</td>
                      <td style={{ maxWidth: 460 }}>
                        <div style={{ color: 'var(--text-main)', fontSize: '0.82rem' }}>
                          "{r.description}"
                        </div>
                      </td>
                      <td>
                        <button
                          className="btn-secondary"
                          style={{ padding: '0.3rem 0.65rem', fontSize: '0.78rem', color: 'var(--brand)', borderColor: '#bfdbfe', background: '#eff6ff' }}
                          onClick={() => handleOpenSimilarity(r)}
                        >
                          <Sparkles style={{ width: 13, height: 13 }} /> Find Matching
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {/* Pagination Controls */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '1rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)', fontWeight: 600 }}>
                Showing records {offset + 1} - {offset + filteredReports.length}
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  className="btn-secondary"
                  disabled={offset === 0}
                  onClick={() => setOffset(Math.max(0, offset - limit))}
                >
                  <ChevronLeft style={{ width: 14, height: 14 }} /> Previous
                </button>
                <button
                  className="btn-secondary"
                  onClick={() => setOffset(offset + limit)}
                >
                  Next <ChevronRight style={{ width: 14, height: 14 }} />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Similarity Match Modal */}
      {selectedReportForSimilarity && (
        <div className="modal-overlay" onClick={() => setSelectedReportForSimilarity(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', paddingBottom: '0.75rem', borderBottom: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700, fontSize: '1.05rem', color: 'var(--brand)' }}>
                <Sparkles style={{ width: 18, height: 18 }} /> Find Matching Workplace Incidents
              </div>
              <button className="btn-secondary" style={{ padding: '0.2rem 0.5rem' }} onClick={() => setSelectedReportForSimilarity(null)}>
                <X style={{ width: 16, height: 16 }} />
              </button>
            </div>

            <div style={{ background: '#f8fafc', padding: '0.85rem', borderRadius: 8, marginBottom: '1.25rem', border: '1px solid #e2e8f0' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 700 }}>SELECTED INCIDENT REPORT #{selectedReportForSimilarity.id}</div>
              <div style={{ fontWeight: 700, color: 'var(--text-main)', marginTop: 2 }}>{selectedReportForSimilarity.employer} ({selectedReportForSimilarity.state})</div>
              <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: 4 }}>"{selectedReportForSimilarity.description}"</div>
            </div>

            <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '0.75rem' }}>
              Top 5 Matching Past Incidents:
            </div>

            {similarityLoading ? (
              <div style={{ textAlign: 'center', padding: '2rem' }}>
                <Activity className="animate-spin" style={{ width: 28, height: 28, color: 'var(--brand)', margin: '0 auto' }} />
                <p style={{ marginTop: '0.75rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>Searching matching incidents...</p>
              </div>
            ) : similarResults?.similar_reports ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {similarResults.similar_reports.map((item, idx) => (
                  <div
                    key={idx}
                    style={{
                      background: '#ffffff',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 8,
                      padding: '0.85rem'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justify: 'space-between' }}>
                      <div style={{ fontWeight: 700, fontSize: '0.88rem', color: 'var(--text-main)' }}>
                        Report #{item.id} &mdash; {item.employer || 'Company N/A'}
                      </div>
                      <span className="risk-badge risk-critical" style={{ fontSize: '0.75rem' }}>
                        {(item.similarity * 100).toFixed(1)}% Similar Match
                      </span>
                    </div>
                    <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: 6, lineHeight: 1.45 }}>
                      "{item.description}"
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>No matching reports returned.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
