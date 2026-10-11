import React, { useState } from 'react';
import type { ModelInfo } from '../types';

interface Props {
  models: ModelInfo[];
  isOpen: boolean;
  onClose: () => void;
  onNewChat: () => void;
  onOpenDetailedAnalysis?: () => void;
}

export default function Sidebar({ models, isOpen, onClose, onNewChat, onOpenDetailedAnalysis }: Props) {
  const [expandedModel, setExpandedModel] = useState<string | null>(null);

  if (!isOpen) return null;

  const toggleModel = (key: string) => {
    setExpandedModel((prev) => (prev === key ? null : key));
  };

  return (
    <>
      {/* Backdrop */}
      <div style={styles.backdrop} onClick={onClose} />

      {/* Sidebar Drawer */}
      <aside style={styles.sidebar}>
        {/* Top Header: Logo + "Model Router" + Collapse icon */}
        <div style={styles.sidebarHeader}>
          <div style={styles.brandRow}>
            <div style={styles.logoWrap}>
              <img src="/logo-icon.png" alt="Model Router Logo" style={styles.logoImg} />
            </div>
            <span style={styles.brandTitle}>Model Router</span>
          </div>

          <button
            style={styles.collapseBtn}
            onClick={onClose}
            title="Collapse menu"
            aria-label="Collapse menu"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <rect x="3" y="3" width="18" height="18" rx="3" />
              <line x1="9" y1="3" x2="9" y2="21" />
            </svg>
          </button>
        </div>

        {/* New Chat Button (Gemini Style) */}
        <div style={styles.newChatWrap}>
          <button
            style={styles.newChatBtn}
            onClick={() => {
              onNewChat();
              onClose();
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            <span>New chat</span>
          </button>
        </div>

        {/* Section title */}
        <div style={styles.sectionHeader}>
          <span>Available Models ({models.length})</span>
        </div>

        {/* Models list */}
        <div style={styles.modelList}>
          {models.length === 0 && (
            <div style={styles.emptyWrap}>
              <span style={styles.emptyText}>Loading models from gateway…</span>
            </div>
          )}

          {models.map((model) => {
            const isOnline = model.availability && model.enabled;
            const isExpanded = expandedModel === model.model_key;

            return (
              <div key={model.model_key} style={styles.modelItem}>
                <div style={styles.modelRow}>
                  <div style={styles.modelLeft}>
                    <span
                      style={{
                        ...styles.statusDot,
                        background: isOnline ? 'var(--green)' : 'var(--red)',
                        boxShadow: isOnline ? '0 0 6px rgba(52,211,153,0.45)' : 'none',
                      }}
                    />
                    <div style={styles.nameBlock}>
                      <span style={styles.modelName}>{model.name}</span>
                      <span style={styles.modelRole}>{model.role}</span>
                    </div>
                  </div>

                  {/* Downward facing arrow */}
                  <button
                    style={styles.chevronBtn}
                    onClick={() => toggleModel(model.model_key)}
                    title={isExpanded ? 'Hide model summary' : 'Show model summary'}
                    aria-label="Toggle model summary"
                  >
                    <svg
                      width="14"
                      height="14"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2.5"
                      strokeLinecap="round"
                      style={{
                        transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                        transition: 'transform 0.2s ease',
                      }}
                    >
                      <polyline points="6 9 12 15 18 9" />
                    </svg>
                  </button>
                </div>

                {/* Small summary of the model */}
                {isExpanded && (
                  <div style={styles.summaryCard}>
                    <p style={styles.summaryText}>{model.description}</p>
                    <div style={styles.statsGrid}>
                      <div style={styles.statBox}>
                        <span style={styles.statLabel}>Avg Latency</span>
                        <span style={styles.statVal}>{model.avg_latency_ms}ms</span>
                      </div>
                      <div style={styles.statBox}>
                        <span style={styles.statLabel}>Context</span>
                        <span style={styles.statVal}>{Math.round(model.context_length / 1024)}K tokens</span>
                      </div>
                      <div style={styles.statBox}>
                        <span style={styles.statLabel}>Capability</span>
                        <span style={styles.statVal}>{model.capability_score}/10</span>
                      </div>
                      <div style={styles.statBox}>
                        <span style={styles.statLabel}>Reliability</span>
                        <span style={styles.statVal}>{(model.reliability * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Footer with Detailed Analysis Navigation */}
        <div style={styles.sidebarFooter}>
          {onOpenDetailedAnalysis && (
            <button
              type="button"
              style={styles.detailedAnalysisNavBtn}
              onClick={() => {
                onClose();
                onOpenDetailedAnalysis();
              }}
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
                <rect x="3" y="3" width="18" height="18" rx="2" />
                <line x1="9" y1="9" x2="9" y2="15" />
                <line x1="12" y1="6" x2="12" y2="15" />
                <line x1="15" y1="11" x2="15" y2="15" />
              </svg>
              <span>Detailed Routing Analysis</span>
            </button>
          )}
          <div style={styles.footerBrandRow}>
            <span style={styles.footerBrand}>Invaders 4.0 · Model Router</span>
            <span style={styles.footerVersion}>v4.0</span>
          </div>
        </div>
      </aside>
    </>
  );
}

const styles: Record<string, React.CSSProperties> = {
  backdrop: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(0, 0, 0, 0.45)',
    backdropFilter: 'blur(4px)',
    WebkitBackdropFilter: 'blur(4px)',
    zIndex: 90,
  },
  sidebar: {
    position: 'fixed',
    top: 0,
    left: 0,
    height: '100vh',
    width: '280px',
    background: '#1e1f20',
    borderRight: '1px solid rgba(255, 255, 255, 0.08)',
    zIndex: 100,
    display: 'flex',
    flexDirection: 'column',
    animation: 'sidebarSlideIn 0.22s ease-out',
    boxShadow: '4px 0 24px rgba(0, 0, 0, 0.5)',
  },
  sidebarHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '16px 16px 12px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
  },
  brandRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
  },
  logoWrap: {
    width: 52,
    height: 52,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoImg: {
    maxHeight: '100%',
    maxWidth: '100%',
    objectFit: 'contain',
  },
  brandTitle: {
    fontSize: 20,
    fontWeight: 600,
    color: '#e3e3e3',
    letterSpacing: '-0.01em',
  },
  collapseBtn: {
    background: 'none',
    border: 'none',
    color: '#9aa0a6',
    cursor: 'pointer',
    padding: 6,
    borderRadius: 8,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'color 0.15s ease',
  },
  newChatWrap: {
    padding: '12px 14px 6px',
  },
  newChatBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    width: '100%',
    padding: '10px 14px',
    borderRadius: 24,
    border: '1px solid rgba(255, 255, 255, 0.08)',
    background: 'rgba(255, 255, 255, 0.04)',
    color: '#e3e3e3',
    fontSize: 13,
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'background 0.15s ease',
  },
  sectionHeader: {
    padding: '14px 16px 6px',
    fontSize: 11,
    fontWeight: 600,
    color: '#9aa0a6',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.05em',
  },
  modelList: {
    flex: 1,
    overflowY: 'auto',
    padding: '6px 12px',
    display: 'flex',
    flexDirection: 'column',
    gap: 4,
  },
  emptyWrap: {
    padding: '24px 12px',
    textAlign: 'center' as const,
  },
  emptyText: {
    fontSize: 12,
    color: '#5f6368',
  },
  modelItem: {
    borderRadius: 12,
    overflow: 'hidden',
    background: 'rgba(255, 255, 255, 0.02)',
    border: '1px solid rgba(255, 255, 255, 0.05)',
  },
  modelRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '9px 12px',
  },
  modelLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: 9,
    flex: 1,
    minWidth: 0,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: '50%',
    flexShrink: 0,
  },
  nameBlock: {
    display: 'flex',
    flexDirection: 'column',
    gap: 1,
    minWidth: 0,
  },
  modelName: {
    fontSize: 13,
    fontWeight: 500,
    color: '#e3e3e3',
    whiteSpace: 'nowrap' as const,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  modelRole: {
    fontSize: 10,
    color: '#9aa0a6',
  },
  chevronBtn: {
    background: 'none',
    border: 'none',
    color: '#9aa0a6',
    cursor: 'pointer',
    padding: 6,
    borderRadius: 6,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  summaryCard: {
    padding: '10px 12px 12px',
    borderTop: '1px solid rgba(255, 255, 255, 0.05)',
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
    background: 'rgba(0, 0, 0, 0.15)',
  },
  summaryText: {
    fontSize: 11,
    color: '#9aa0a6',
    lineHeight: 1.5,
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 6,
  },
  statBox: {
    display: 'flex',
    flexDirection: 'column',
    gap: 2,
    background: 'rgba(255, 255, 255, 0.03)',
    padding: '6px 8px',
    borderRadius: 6,
  },
  statLabel: {
    fontSize: 9,
    color: '#5f6368',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.04em',
  },
  statVal: {
    fontSize: 11,
    fontWeight: 600,
    color: '#e3e3e3',
  },
  sidebarFooter: {
    padding: '12px 14px',
    borderTop: '1px solid rgba(255, 255, 255, 0.08)',
    display: 'flex',
    flexDirection: 'column',
    gap: 10,
    background: 'rgba(0, 0, 0, 0.2)',
  },
  detailedAnalysisNavBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    width: '100%',
    padding: '9px 12px',
    borderRadius: 10,
    border: '1px solid rgba(138, 180, 248, 0.25)',
    background: 'rgba(138, 180, 248, 0.08)',
    color: '#8ab4f8',
    fontSize: 12,
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'all 0.15s ease',
  },
  footerBrandRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 4px',
  },
  footerBrand: {
    fontSize: 11,
    color: '#9aa0a6',
    fontWeight: 500,
  },
  footerVersion: {
    fontSize: 10,
    color: '#8ab4f8',
    background: 'rgba(138, 180, 248, 0.1)',
    padding: '2px 6px',
    borderRadius: 4,
  },
};
