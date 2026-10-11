import React, { useState, useEffect } from 'react';
import type { AuditEntry, ModelInfo } from '../types';
import { fetchLogs } from '../api';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  models: ModelInfo[];
}

export default function DetailedAnalysisModal({ isOpen, onClose, models }: Props) {
  const [logs, setLogs] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    fetchLogs()
      .then((data) => setLogs(data))
      .catch((err) => console.warn('Failed to load logs:', err))
      .finally(() => setLoading(false));
  }, [isOpen]);

  if (!isOpen) return null;

  const totalReqs = logs.length;
  const successfulReqs = logs.filter((l) => l.success !== false).length;
  const successRate = totalReqs > 0 ? Math.round((successfulReqs / totalReqs) * 100) : 100;
  const avgLatency =
    totalReqs > 0
      ? Math.round(
          logs.reduce((acc, l) => acc + (l.response_time_ms || 0), 0) / totalReqs
        )
      : 0;

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div style={styles.header}>
          <div style={styles.headerLeft}>
            <div style={styles.iconWrap}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <rect x="3" y="3" width="18" height="18" rx="2" />
                <line x1="9" y1="9" x2="9" y2="15" />
                <line x1="12" y1="6" x2="12" y2="15" />
                <line x1="15" y1="11" x2="15" y2="15" />
              </svg>
            </div>
            <div>
              <h2 style={styles.title}>Detailed Routing Analysis</h2>
              <p style={styles.subtitle}>Historical audit logs, metrics, and model performance</p>
            </div>
          </div>

          <button style={styles.closeBtn} onClick={onClose} aria-label="Close">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Metric Cards Banner */}
        <div style={styles.metricsRow}>
          <div style={styles.metricCard}>
            <span style={styles.metricLabel}>Total Inferences</span>
            <span style={styles.metricVal}>{totalReqs}</span>
          </div>
          <div style={styles.metricCard}>
            <span style={styles.metricLabel}>Success Rate</span>
            <span style={{ ...styles.metricVal, color: '#34d399' }}>{successRate}%</span>
          </div>
          <div style={styles.metricCard}>
            <span style={styles.metricLabel}>Avg Response Time</span>
            <span style={{ ...styles.metricVal, color: '#8ab4f8' }}>{avgLatency}ms</span>
          </div>
          <div style={styles.metricCard}>
            <span style={styles.metricLabel}>Registered Models</span>
            <span style={styles.metricVal}>{models.length}</span>
          </div>
        </div>

        {/* Content Body: Audit Logs */}
        <div style={styles.body}>
          <div style={styles.tableHeader}>
            <span style={{ flex: 1 }}>Timestamp & Request</span>
            <span style={{ width: 140 }}>Selected Model</span>
            <span style={{ width: 100 }}>Latency</span>
            <span style={{ width: 80, textAlign: 'right' }}>Status</span>
          </div>

          {loading ? (
            <div style={styles.loadingBox}>Loading routing telemetry…</div>
          ) : logs.length === 0 ? (
            <div style={styles.emptyBox}>No inference logs recorded yet. Send a prompt to generate telemetry.</div>
          ) : (
            <div style={styles.logsList}>
              {logs.map((log, idx) => {
                const isOk = log.success !== false;
                const timeStr = log.timestamp_iso
                  ? new Date(log.timestamp_iso).toLocaleTimeString()
                  : '--:--:--';
                const reqId = log.request_id || log.log_id || `#${idx + 1}`;

                return (
                  <div key={log.log_id || idx} style={styles.logRow}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={styles.rowTop}>
                        <span style={styles.timeTag}>[{timeStr}]</span>
                        <span style={styles.reqTag}>{reqId}</span>
                      </div>
                      {log.prompt_preview && (
                        <div style={styles.promptPreview}>"{log.prompt_preview}"</div>
                      )}
                    </div>

                    <div style={{ width: 140 }}>
                      <span style={styles.modelTag}>{log.model_used || log.model || 'Auto'}</span>
                      {log.simulated && <span style={styles.simBadge}>SIMULATED</span>}
                    </div>

                    <div style={{ width: 100 }}>
                      <span style={styles.latVal}>{log.response_time_ms ?? 0}ms</span>
                    </div>

                    <div style={{ width: 80, textAlign: 'right' }}>
                      <span
                        style={{
                          ...styles.statusTag,
                          background: isOk ? 'rgba(52,211,153,0.12)' : 'rgba(248,113,113,0.12)',
                          color: isOk ? '#34d399' : '#f87171',
                        }}
                      >
                        {isOk ? 'SUCCESS' : 'FAILED'}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={styles.footer}>
          <span style={styles.footerText}>Model Router v4.0 Telemetry Gateway</span>
          <button style={styles.doneBtn} onClick={onClose}>
            Done
          </button>
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  overlay: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(0, 0, 0, 0.75)',
    backdropFilter: 'blur(10px)',
    WebkitBackdropFilter: 'blur(10px)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
    animation: 'fadeIn 0.2s ease',
  },
  modal: {
    background: '#1e1f20',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: 20,
    width: '92%',
    maxWidth: 820,
    maxHeight: '85vh',
    display: 'flex',
    flexDirection: 'column',
    boxShadow: '0 24px 64px rgba(0, 0, 0, 0.6)',
    overflow: 'hidden',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '20px 24px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: 14,
  },
  iconWrap: {
    width: 36,
    height: 36,
    borderRadius: 10,
    background: 'rgba(138, 180, 248, 0.12)',
    color: '#8ab4f8',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: 18,
    fontWeight: 600,
    color: '#e3e3e3',
    margin: 0,
  },
  subtitle: {
    fontSize: 12,
    color: '#9aa0a6',
    margin: '2px 0 0',
  },
  closeBtn: {
    background: 'none',
    border: 'none',
    color: '#9aa0a6',
    cursor: 'pointer',
    padding: 6,
    borderRadius: 8,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  metricsRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: 12,
    padding: '16px 24px',
    background: 'rgba(0, 0, 0, 0.15)',
    borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
  },
  metricCard: {
    background: 'rgba(255, 255, 255, 0.03)',
    border: '1px solid rgba(255, 255, 255, 0.06)',
    borderRadius: 10,
    padding: '10px 14px',
    display: 'flex',
    flexDirection: 'column',
    gap: 3,
  },
  metricLabel: {
    fontSize: 10,
    color: '#9aa0a6',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.04em',
  },
  metricVal: {
    fontSize: 20,
    fontWeight: 700,
    color: '#e3e3e3',
    fontFamily: 'monospace',
  },
  body: {
    flex: 1,
    overflowY: 'auto',
    padding: '16px 24px',
    display: 'flex',
    flexDirection: 'column',
  },
  tableHeader: {
    display: 'flex',
    alignItems: 'center',
    padding: '8px 12px',
    fontSize: 11,
    color: '#9aa0a6',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.04em',
    borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
  },
  logsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
    marginTop: 8,
  },
  logRow: {
    display: 'flex',
    alignItems: 'center',
    padding: '10px 12px',
    borderRadius: 8,
    background: 'rgba(255, 255, 255, 0.02)',
    border: '1px solid rgba(255, 255, 255, 0.05)',
  },
  rowTop: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
  },
  timeTag: {
    fontSize: 11,
    color: '#9aa0a6',
    fontFamily: 'monospace',
  },
  reqTag: {
    fontSize: 11,
    fontWeight: 600,
    color: '#e3e3e3',
    fontFamily: 'monospace',
  },
  promptPreview: {
    fontSize: 12,
    color: '#9aa0a6',
    marginTop: 3,
    whiteSpace: 'nowrap' as const,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    maxWidth: '90%',
  },
  modelTag: {
    fontSize: 12,
    fontWeight: 600,
    color: '#8ab4f8',
  },
  simBadge: {
    fontSize: 9,
    color: '#9aa0a6',
    background: 'rgba(255, 255, 255, 0.06)',
    padding: '1px 5px',
    borderRadius: 4,
    marginLeft: 6,
  },
  latVal: {
    fontSize: 12,
    color: '#e3e3e3',
    fontFamily: 'monospace',
  },
  statusTag: {
    fontSize: 10,
    fontWeight: 700,
    padding: '2px 7px',
    borderRadius: 4,
    display: 'inline-block',
  },
  loadingBox: {
    padding: '40px 0',
    textAlign: 'center' as const,
    color: '#9aa0a6',
    fontSize: 13,
  },
  emptyBox: {
    padding: '40px 0',
    textAlign: 'center' as const,
    color: '#9aa0a6',
    fontSize: 13,
  },
  footer: {
    padding: '14px 24px',
    borderTop: '1px solid rgba(255, 255, 255, 0.08)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    background: 'rgba(0, 0, 0, 0.1)',
  },
  footerText: {
    fontSize: 11,
    color: '#5f6368',
  },
  doneBtn: {
    background: '#8ab4f8',
    color: '#131314',
    border: 'none',
    borderRadius: 8,
    padding: '7px 18px',
    fontSize: 13,
    fontWeight: 600,
    cursor: 'pointer',
  },
};
