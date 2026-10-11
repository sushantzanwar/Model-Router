import React from 'react';
import type { AuditEntry } from '../types';

interface Props {
  logs: AuditEntry[];
}

function formatTime(timestampIso?: string, timestampSec?: number): string {
  try {
    if (timestampIso) {
      const d = new Date(timestampIso);
      return d.toLocaleTimeString([], { hour12: false });
    }
    if (timestampSec) {
      const d = new Date(timestampSec * 1000);
      return d.toLocaleTimeString([], { hour12: false });
    }
  } catch {}
  return '--:--:--';
}

export default function AuditLog({ logs }: Props) {
  if (!logs || logs.length === 0) {
    return (
      <div style={styles.empty}>
        <p style={{ margin: 0, fontSize: 12, color: '#9aa0a6' }}>No routing events recorded yet.</p>
      </div>
    );
  }

  return (
    <div style={styles.list}>
      {logs.slice(0, 30).map((log, index) => {
        const timeStr = formatTime(log.timestamp_iso, log.timestamp);
        const reqId = log.request_id || log.log_id || `#${index + 1}`;
        const modelTarget = log.model_used || log.model || 'Unknown';
        const isOk = log.success !== false;

        return (
          <div key={log.log_id || index} style={styles.entry}>
            <div style={styles.topLine}>
              <span style={styles.time}>[{timeStr}]</span>
              <span style={styles.reqId}>{reqId}</span>
              <span
                style={{
                  ...styles.statusBadge,
                  background: isOk ? 'rgba(52,211,153,0.12)' : 'rgba(248,113,113,0.12)',
                  color: isOk ? '#34d399' : '#f87171',
                }}
              >
                {isOk ? 'OK' : 'FAIL'}
              </span>
            </div>

            <div style={styles.bottomLine}>
              <span style={styles.modelTag}>→ {modelTarget}</span>
              {log.response_time_ms !== undefined && (
                <span style={styles.ms}>{log.response_time_ms}ms</span>
              )}
              {log.simulated && (
                <span style={styles.simBadge}>SIMULATED</span>
              )}
            </div>

            {log.prompt_preview && (
              <div style={styles.preview}>"{log.prompt_preview}"</div>
            )}
          </div>
        );
      })}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  list: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
    maxHeight: 280,
    overflowY: 'auto',
    fontFamily: 'monospace',
  },
  empty: {
    padding: '16px 0',
    textAlign: 'center',
  },
  entry: {
    padding: '8px 10px',
    borderRadius: 8,
    background: 'rgba(255, 255, 255, 0.02)',
    border: '1px solid rgba(255, 255, 255, 0.06)',
    fontSize: 11,
    lineHeight: 1.4,
  },
  topLine: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
  },
  time: {
    color: '#9aa0a6',
  },
  reqId: {
    color: '#e3e3e3',
    fontWeight: 600,
  },
  statusBadge: {
    fontSize: 9,
    fontWeight: 700,
    padding: '1px 5px',
    borderRadius: 4,
    marginLeft: 'auto',
  },
  bottomLine: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    marginTop: 4,
  },
  modelTag: {
    color: '#8ab4f8',
    fontWeight: 600,
  },
  ms: {
    color: '#9aa0a6',
  },
  simBadge: {
    fontSize: 9,
    background: 'rgba(255, 255, 255, 0.06)',
    color: '#9aa0a6',
    padding: '1px 4px',
    borderRadius: 3,
  },
  preview: {
    color: '#9aa0a6',
    fontSize: 10,
    marginTop: 4,
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
};
