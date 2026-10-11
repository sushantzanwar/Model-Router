import React from 'react';
import type { Decision } from '../types';

interface Props {
  decision: Decision | null;
}

export default function ExplainabilityBox({ decision }: Props) {
  if (!decision) {
    return (
      <div style={styles.empty}>
        <div style={styles.emptyIcon}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
        </div>
        <p style={styles.emptyText}>Send a prompt to see routing decision & parameters.</p>
      </div>
    );
  }

  const { complexity, candidates = [], selected, explanation, status, message, preference_used } = decision;
  const isNoValid = status === 'NO_VALID_MODEL' || !selected;

  const complexityScore = complexity?.score ?? 0;
  const complexityPct = Math.min(100, Math.max(0, (complexityScore / 10) * 100));

  const inferredCap = complexity?.inferred_min_capability ?? complexity?.score ?? 4.0;
  const capPct = Math.min(100, Math.max(0, (inferredCap / 10) * 100));

  return (
    <div style={styles.container}>
      {/* 1. Winner / Outcome Short Summary */}
      {isNoValid ? (
        <div style={{ ...styles.banner, ...styles.bannerError }}>
          <div style={styles.bannerIcon}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          </div>
          <div>
            <div style={styles.bannerTitle}>No Valid Model Selected</div>
            <div style={styles.bannerDesc}>{message || 'No available model satisfies prompt constraints.'}</div>
          </div>
        </div>
      ) : (
        <div style={{ ...styles.banner, ...styles.bannerSuccess }}>
          <div style={styles.bannerIcon}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          <div>
            <div style={styles.bannerTitle}>
              Selected: {decision.selected_name || selected}
            </div>
            <div style={styles.bannerDesc}>{explanation}</div>
          </div>
        </div>
      )}

      {/* 2. Values of Parameters at the Time of Prompt (With Visual Slider Bars) */}
      <div style={styles.paramCard}>
        <div style={styles.paramCardTitle}>Parameters at Time of Prompt</div>

        <div style={styles.paramGrid}>
          {/* Parameter 1: Complexity Score with Slider Bar */}
          <div style={styles.paramCol}>
            <div style={styles.paramColHeader}>
              <span style={styles.paramColLabel}>Complexity Score</span>
              <span style={styles.paramColVal}>
                {complexity ? `${complexity.score}/10 (${complexity.label})` : 'N/A'}
              </span>
            </div>
            {/* Visual Slider Bar */}
            <div style={styles.sliderTrack}>
              <div
                style={{
                  ...styles.sliderFill,
                  width: `${complexityPct}%`,
                  background:
                    complexityScore >= 8
                      ? 'linear-gradient(90deg, #fb923c, #f87171)'
                      : complexityScore >= 5
                      ? 'linear-gradient(90deg, #fbbf24, #f59e0b)'
                      : 'linear-gradient(90deg, #34d399, #60a5fa)',
                }}
              />
              <div style={{ ...styles.sliderThumb, left: `calc(${complexityPct}% - 5px)` }} />
            </div>
          </div>

          {/* Parameter 2: Inferred Capability with Slider Bar */}
          <div style={styles.paramCol}>
            <div style={styles.paramColHeader}>
              <span style={styles.paramColLabel}>Inferred Capability</span>
              <span style={styles.paramColVal}>≥ {inferredCap}/10</span>
            </div>
            {/* Visual Slider Bar */}
            <div style={styles.sliderTrack}>
              <div
                style={{
                  ...styles.sliderFill,
                  width: `${capPct}%`,
                  background: 'linear-gradient(90deg, #818cf8, #a78bfa)',
                }}
              />
              <div style={{ ...styles.sliderThumb, left: `calc(${capPct}% - 5px)` }} />
            </div>
          </div>

          {/* Parameter 3: Routing Objective */}
          <div style={styles.paramCol}>
            <div style={styles.paramColHeader}>
              <span style={styles.paramColLabel}>Routing Objective</span>
              <span style={styles.paramColVal}>{preference_used || 'lowest_latency'}</span>
            </div>
            <div style={styles.sliderTrack}>
              <div
                style={{
                  ...styles.sliderFill,
                  width: '85%',
                  background: 'linear-gradient(90deg, #38bdf8, #818cf8)',
                }}
              />
              <div style={{ ...styles.sliderThumb, left: 'calc(85% - 5px)' }} />
            </div>
          </div>

          {/* Parameter 4: Candidates Tested */}
          <div style={styles.paramCol}>
            <div style={styles.paramColHeader}>
              <span style={styles.paramColLabel}>Candidates Tested</span>
              <span style={styles.paramColVal}>{candidates.length} models</span>
            </div>
            <div style={styles.sliderTrack}>
              <div
                style={{
                  ...styles.sliderFill,
                  width: `${Math.min(100, (candidates.length / 5) * 100)}%`,
                  background: 'linear-gradient(90deg, #34d399, #10b981)',
                }}
              />
              <div
                style={{
                  ...styles.sliderThumb,
                  left: `calc(${Math.min(100, (candidates.length / 5) * 100)}% - 5px)`,
                }}
              />
            </div>
          </div>
        </div>

        {complexity?.matched_keywords && complexity.matched_keywords.length > 0 && (
          <div style={styles.kwWrap}>
            <span style={styles.kwLabel}>Matched Keywords:</span>
            <div style={styles.kwTags}>
              {complexity.matched_keywords.map((kw) => (
                <span key={kw} style={styles.kwTag}>{kw}</span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 3. Models Evaluation Breakdown */}
      <div style={styles.modelsSection}>
        <div style={styles.sectionLabel}>
          Model Candidates Evaluated ({candidates.length})
        </div>
        <div style={styles.modelsList}>
          {candidates.map((c) => {
            const isWinner = c.status === 'selected' || c.model_key === selected;
            const isRejected = c.status === 'rejected';
            return (
              <div
                key={c.model_key || c.name}
                style={{
                  ...styles.modelCard,
                  borderColor: isWinner
                    ? 'rgba(52,211,153,0.3)'
                    : isRejected
                    ? 'rgba(248,113,113,0.2)'
                    : 'rgba(255,255,255,0.06)',
                  background: isWinner
                    ? 'rgba(52,211,153,0.06)'
                    : isRejected
                    ? 'rgba(248,113,113,0.04)'
                    : 'rgba(255,255,255,0.02)',
                }}
              >
                <div style={styles.cardTop}>
                  <div style={styles.cardLeft}>
                    <span
                      style={{
                        ...styles.statusIcon,
                        color: isWinner ? '#34d399' : isRejected ? '#f87171' : '#9aa0a6',
                      }}
                    >
                      {isWinner ? (
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
                        </svg>
                      ) : isRejected ? (
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
                        </svg>
                      ) : (
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                          <circle cx="12" cy="12" r="5" opacity="0.4" />
                        </svg>
                      )}
                    </span>
                    <strong style={styles.cardName}>{c.name}</strong>
                  </div>
                  <span
                    style={{
                      ...styles.pill,
                      background: isWinner
                        ? 'rgba(52,211,153,0.15)'
                        : isRejected
                        ? 'rgba(248,113,113,0.15)'
                        : 'rgba(255,255,255,0.06)',
                      color: isWinner ? '#34d399' : isRejected ? '#f87171' : '#9aa0a6',
                    }}
                  >
                    {isWinner ? 'Selected' : isRejected ? 'Rejected' : 'Passed'}
                  </span>
                </div>

                <div style={styles.metricRow}>
                  <MetricTag label="Avg Latency" value={`${c.avg_latency_ms}ms`} />
                  <MetricTag label="Capability" value={`${c.capability_score}/10`} />
                  <MetricTag label="Bound" value={`${c.max_latency_ms}ms`} />
                </div>

                {isRejected && c.rejection_reason && (
                  <div style={styles.rejectionBox}>
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <circle cx="12" cy="12" r="10" />
                      <line x1="12" y1="8" x2="12" y2="12" />
                      <line x1="12" y1="16" x2="12.01" y2="16" />
                    </svg>
                    <span>{c.rejection_reason}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function MetricTag({ label, value }: { label: string; value: string }) {
  return (
    <div style={metricStyles.wrap}>
      <span style={metricStyles.label}>{label}</span>
      <span style={metricStyles.value}>{value}</span>
    </div>
  );
}

const metricStyles: Record<string, React.CSSProperties> = {
  wrap: {
    display: 'flex',
    flexDirection: 'column',
    gap: 1,
  },
  label: {
    fontSize: 9,
    color: '#9aa0a6',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.04em',
  },
  value: {
    fontSize: 11,
    fontWeight: 600,
    color: '#e3e3e3',
    fontFamily: 'monospace',
  },
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: 10,
  },
  empty: {
    padding: '24px 0',
    textAlign: 'center',
    color: '#9aa0a6',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 8,
  },
  emptyIcon: {
    opacity: 0.6,
  },
  emptyText: {
    fontSize: 12,
  },
  banner: {
    borderRadius: 10,
    padding: '10px 12px',
    display: 'flex',
    alignItems: 'flex-start',
    gap: 10,
    border: '1px solid',
  },
  bannerSuccess: {
    background: 'rgba(52,211,153,0.06)',
    borderColor: 'rgba(52,211,153,0.25)',
  },
  bannerError: {
    background: 'rgba(248,113,113,0.06)',
    borderColor: 'rgba(248,113,113,0.25)',
  },
  bannerIcon: {
    flexShrink: 0,
    marginTop: 1,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: 22,
    height: 22,
    borderRadius: 6,
    background: 'rgba(255,255,255,0.06)',
  },
  bannerTitle: {
    fontSize: 13,
    fontWeight: 600,
    color: '#e3e3e3',
    marginBottom: 3,
  },
  bannerDesc: {
    fontSize: 11,
    color: '#9aa0a6',
    lineHeight: 1.5,
  },
  paramCard: {
    background: 'rgba(255, 255, 255, 0.02)',
    border: '1px solid rgba(255, 255, 255, 0.06)',
    borderRadius: 10,
    padding: '12px 14px',
    display: 'flex',
    flexDirection: 'column',
    gap: 10,
  },
  paramCardTitle: {
    fontSize: 10,
    fontWeight: 600,
    color: '#9aa0a6',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.05em',
  },
  paramGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 10,
  },
  paramCol: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
    background: 'rgba(255, 255, 255, 0.02)',
    padding: '8px 10px',
    borderRadius: 8,
    border: '1px solid rgba(255, 255, 255, 0.04)',
  },
  paramColHeader: {
    display: 'flex',
    flexDirection: 'column',
    gap: 1,
  },
  paramColLabel: {
    fontSize: 9,
    color: '#5f6368',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.04em',
  },
  paramColVal: {
    fontSize: 11,
    fontWeight: 600,
    color: '#e3e3e3',
  },
  sliderTrack: {
    position: 'relative',
    width: '100%',
    height: 4,
    background: 'rgba(255, 255, 255, 0.08)',
    borderRadius: 2,
    marginTop: 3,
  },
  sliderFill: {
    height: '100%',
    borderRadius: 2,
    transition: 'width 0.3s ease',
  },
  sliderThumb: {
    position: 'absolute',
    top: -3,
    width: 10,
    height: 10,
    borderRadius: '50%',
    background: '#e3e3e3',
    boxShadow: '0 0 6px rgba(138, 180, 248, 0.8)',
    pointerEvents: 'none',
    transition: 'left 0.3s ease',
  },
  kwWrap: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    flexWrap: 'wrap' as const,
    paddingTop: 6,
    borderTop: '1px solid rgba(255, 255, 255, 0.04)',
  },
  kwLabel: {
    fontSize: 10,
    color: '#5f6368',
  },
  kwTags: {
    display: 'flex',
    flexWrap: 'wrap' as const,
    gap: 4,
  },
  kwTag: {
    fontSize: 10,
    color: '#8ab4f8',
    background: 'rgba(138, 180, 248, 0.1)',
    padding: '1px 6px',
    borderRadius: 4,
  },
  modelsSection: {
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
  },
  sectionLabel: {
    fontSize: 10,
    fontWeight: 600,
    color: '#9aa0a6',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.05em',
  },
  modelsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  modelCard: {
    border: '1px solid',
    borderRadius: 8,
    padding: '9px 11px',
    display: 'flex',
    flexDirection: 'column',
    gap: 7,
  },
  cardTop: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: 7,
  },
  statusIcon: {
    display: 'flex',
    alignItems: 'center',
  },
  cardName: {
    fontSize: 12,
    color: '#e3e3e3',
    fontWeight: 500,
  },
  pill: {
    fontSize: 10,
    fontWeight: 600,
    padding: '2px 7px',
    borderRadius: 16,
  },
  metricRow: {
    display: 'flex',
    gap: 14,
  },
  rejectionBox: {
    fontSize: 11,
    color: '#f87171',
    background: 'rgba(248,113,113,0.07)',
    padding: '5px 8px',
    borderRadius: 6,
    border: '1px solid rgba(248,113,113,0.15)',
    lineHeight: 1.4,
    display: 'flex',
    alignItems: 'flex-start',
    gap: 6,
  },
};
