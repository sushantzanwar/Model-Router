import React from 'react';
import type { ModelInfo } from '../types';

interface Props {
  models: ModelInfo[];
}

export default function TokenCapacityChart({ models }: Props) {
  if (!models || models.length === 0) {
    return (
      <div style={styles.empty}>
        <p style={{ margin: 0, fontSize: 12, color: '#6b7280' }}>No models available.</p>
      </div>
    );
  }

  const maxTokensRef = 131072;

  const formatTokens = (num: number) => {
    if (num >= 1000) return `${Math.round(num / 1024)}K`;
    return `${num}`;
  };

  return (
    <div style={styles.container}>
      <div style={styles.subhead}>
        <span>Context window capacity</span>
        <span style={styles.subheadMax}>Max ref: 128K</span>
      </div>

      <div style={styles.chartList}>
        {models.map((m) => {
          const tokens = m.context_length || 32768;
          const percentage = Math.min(100, Math.max(10, (tokens / maxTokensRef) * 100));
          const isOnline = m.availability && m.enabled;

          const barColor = !isOnline
            ? 'rgba(255,255,255,0.08)'
            : tokens >= 100000
            ? 'linear-gradient(90deg, #818cf8, #60a5fa)'
            : tokens >= 60000
            ? 'linear-gradient(90deg, #34d399, #0891b2)'
            : 'linear-gradient(90deg, #a78bfa, #818cf8)';

          return (
            <div key={m.model_key} style={styles.row}>
              <div style={styles.modelHeader}>
                <div style={styles.nameGroup}>
                  <span
                    style={{
                      ...styles.dot,
                      background: isOnline ? 'var(--green)' : 'var(--red)',
                      boxShadow: isOnline ? '0 0 5px rgba(52,211,153,0.4)' : 'none',
                    }}
                  />
                  <span style={styles.modelName}>{m.name}</span>
                </div>
                <div style={styles.tokenValues}>
                  <strong style={styles.tokenCount}>{formatTokens(tokens)}</strong>
                  <span style={styles.tokenRaw}>{tokens.toLocaleString()}</span>
                </div>
              </div>

              <div style={styles.barTrack}>
                <div
                  style={{
                    ...styles.barFill,
                    width: `${percentage}%`,
                    background: barColor,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <div style={styles.legend}>
        <div style={styles.legendItem}>
          <span style={{ ...styles.legendDot, background: 'linear-gradient(135deg, #a78bfa, #818cf8)' }} />
          <span>32K</span>
        </div>
        <div style={styles.legendItem}>
          <span style={{ ...styles.legendDot, background: 'linear-gradient(135deg, #34d399, #0891b2)' }} />
          <span>64K</span>
        </div>
        <div style={styles.legendItem}>
          <span style={{ ...styles.legendDot, background: 'linear-gradient(135deg, #818cf8, #60a5fa)' }} />
          <span>128K</span>
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
  },
  empty: {
    padding: '16px 0',
    textAlign: 'center',
  },
  subhead: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: 10,
    color: '#6b7280',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.04em',
  },
  subheadMax: {
    fontWeight: 600,
    color: '#9aa0a6',
  },
  chartList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 10,
  },
  row: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
    padding: '9px 11px',
    borderRadius: 8,
    background: 'rgba(255,255,255,0.03)',
    border: '1px solid rgba(255,255,255,0.06)',
  },
  modelHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  nameGroup: {
    display: 'flex',
    alignItems: 'center',
    gap: 7,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: '50%',
    flexShrink: 0,
  },
  modelName: {
    fontSize: 12,
    fontWeight: 600,
    color: 'var(--text-primary)',
  },
  tokenValues: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
  },
  tokenCount: {
    fontSize: 13,
    color: '#a5b4fc',
    fontFamily: 'monospace',
    fontWeight: 700,
  },
  tokenRaw: {
    fontSize: 10,
    color: '#6b7280',
  },
  barTrack: {
    width: '100%',
    height: 4,
    borderRadius: 2,
    background: 'rgba(255,255,255,0.07)',
    overflow: 'hidden',
  },
  barFill: {
    height: '100%',
    borderRadius: 2,
    transition: 'width 0.5s ease',
  },
  legend: {
    display: 'flex',
    gap: 12,
    fontSize: 10,
    color: '#6b7280',
    paddingTop: 4,
    borderTop: '1px solid rgba(255,255,255,0.06)',
  },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 5,
  },
  legendDot: {
    width: 8,
    height: 8,
    borderRadius: 2,
  },
};
