import React, { useState } from 'react';
import type { Decision, ModelInfo } from '../types';
import ExplainabilityBox from './ExplainabilityBox';
import TokenCapacityChart from './TokenCapacityChart';
import DetailedAnalysisModal from './DetailedAnalysisModal';

interface Props {
  models: ModelInfo[];
  lastDecision: Decision | null;
  onOpenDetailedAnalysis?: () => void;
}

type Section = 'decision' | 'tokens' | 'models';

const SECTIONS: { id: Section; title: string; icon: React.ReactNode }[] = [
  {
    id: 'decision',
    title: 'Routing Decision',
    icon: (
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
        <circle cx="12" cy="12" r="3" />
        <path d="M12 2v2M12 20v2M2 12h2M20 12h2" />
      </svg>
    ),
  },
  {
    id: 'tokens',
    title: 'Context Capacity',
    icon: (
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
        <rect x="3" y="3" width="18" height="18" rx="2" />
        <line x1="9" y1="9" x2="9" y2="15" />
        <line x1="12" y1="6" x2="12" y2="15" />
        <line x1="15" y1="11" x2="15" y2="15" />
      </svg>
    ),
  },
  {
    id: 'models',
    title: 'Model Status',
    icon: (
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
        <path d="M12 2L2 7l10 5 10-5-10-5z" />
        <path d="M2 17l10 5 10-5" />
        <path d="M2 12l10 5 10-5" />
      </svg>
    ),
  },
];

export default function InspectorPanel({ models, lastDecision, onOpenDetailedAnalysis }: Props) {
  const [openSections, setOpenSections] = useState<Set<Section>>(
    new Set(['decision', 'tokens', 'models'])
  );
  const [showDetailedModal, setShowDetailedModal] = useState(false);

  const toggle = (id: Section) => {
    setOpenSections((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleOpenDetailed = () => {
    if (onOpenDetailedAnalysis) {
      onOpenDetailedAnalysis();
    } else {
      setShowDetailedModal(true);
    }
  };

  const onlineCount = models.filter((m) => m.availability && m.enabled).length;
  const hasDecision = lastDecision !== null;
  const complexityScore = lastDecision?.complexity?.score ?? 0;
  const complexityPct = Math.min(100, Math.max(0, (complexityScore / 10) * 100));

  return (
    <>
      <div style={styles.wrapper}>
        {/* Header */}
        <div style={styles.header}>
          <div style={styles.headerLeft}>
            <div style={styles.headerIconWrap}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
                <rect x="3" y="3" width="18" height="18" rx="2" />
                <line x1="9" y1="9" x2="9" y2="15" />
                <line x1="12" y1="6" x2="12" y2="15" />
                <line x1="15" y1="11" x2="15" y2="15" />
              </svg>
            </div>
            <div>
              <span style={styles.headerTitle}>Analysis Window</span>
              <div style={styles.headerSub}>Model Routing Intelligence</div>
            </div>
          </div>
          <span
            style={{
              ...styles.badge,
              background: onlineCount > 0 ? 'rgba(52,211,153,0.12)' : 'rgba(248,113,113,0.12)',
              color: onlineCount > 0 ? 'var(--green)' : 'var(--red)',
              borderColor: onlineCount > 0 ? 'rgba(52,211,153,0.25)' : 'rgba(248,113,113,0.25)',
            }}
          >
            {onlineCount}/{models.length} Online
          </span>
        </div>

        {/* Selected Model Summary Banner With Complexity Slider Bar */}
        {hasDecision && lastDecision?.selected && (
          <div style={styles.decisionBanner}>
            <div style={styles.bannerLeft}>
              <div style={styles.bannerPulse}>
                <div style={styles.pulseRing} />
                <div style={styles.pulseDot} />
              </div>
              <div>
                <div style={styles.bannerLabel}>Active Model</div>
                <div style={styles.bannerModel}>
                  {lastDecision.selected_name || lastDecision.selected}
                </div>
              </div>
            </div>
            {lastDecision.complexity && (
              <div style={styles.complexityBadge}>
                <div style={styles.complexityTopRow}>
                  <span style={styles.complexityLabel}>Complexity</span>
                  <span style={styles.complexityScore}>
                    {lastDecision.complexity.score}/10
                  </span>
                </div>
                {/* Visual horizontal slider bar */}
                <div style={styles.miniSliderTrack}>
                  <div
                    style={{
                      ...styles.miniSliderFill,
                      width: `${complexityPct}%`,
                    }}
                  />
                  <div style={{ ...styles.miniSliderThumb, left: `calc(${complexityPct}% - 4px)` }} />
                </div>
              </div>
            )}
          </div>
        )}

        {/* Sections With High-Visibility Custom Scrollbar ("Slider Bar") */}
        <div className="analysis-scroll" style={styles.sections}>
          {SECTIONS.map(({ id, title, icon }) => {
            const isOpen = openSections.has(id);
            return (
              <div key={id} style={styles.section}>
                <button
                  type="button"
                  style={styles.sectionHeader}
                  onClick={() => toggle(id)}
                >
                  <div style={styles.sectionHeaderLeft}>
                    <span style={styles.sectionIcon}>{icon}</span>
                    <span style={styles.sectionTitle}>{title}</span>
                  </div>
                  <span
                    style={{
                      ...styles.chevron,
                      transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
                    }}
                  >
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <polyline points="6 9 12 15 18 9" />
                    </svg>
                  </span>
                </button>

                {isOpen && (
                  <div style={styles.sectionBody}>
                    {id === 'decision' && <ExplainabilityBox decision={lastDecision} />}



                    {id === 'tokens' && <TokenCapacityChart models={models} />}

                    {id === 'models' && (
                      <div style={styles.modelStatusList}>
                        {models.map((m) => {
                          const isOnline = m.availability && m.enabled;
                          return (
                            <div key={m.model_key} style={styles.modelStatusRow}>
                              <div style={styles.modelRowLeft}>
                                <span
                                  style={{
                                    ...styles.dot,
                                    background: isOnline ? 'var(--green)' : 'var(--red)',
                                    boxShadow: isOnline ? '0 0 5px rgba(52,211,153,0.4)' : 'none',
                                  }}
                                />
                                <div>
                                  <div style={styles.name}>{m.name}</div>
                                  <div style={styles.role}>{m.role}</div>
                                </div>
                              </div>
                              <div style={styles.modelRowRight}>
                                <div style={styles.lat}>{m.avg_latency_ms}ms</div>
                                <div style={styles.cap}>Cap: {m.capability_score}/10</div>
                              </div>
                            </div>
                          );
                        })}
                        {models.length === 0 && (
                          <p style={styles.emptyMsg}>No models loaded from backend.</p>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Footer with Button to Detailed Analysis */}
        <div style={styles.footer}>
          <button
            type="button"
            style={styles.analysisBtn}
            onClick={handleOpenDetailed}
            title="Open detailed analysis & audit logs"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
              <polyline points="15 3 21 3 21 9" />
              <line x1="10" y1="14" x2="21" y2="3" />
            </svg>
            <span>Open Detailed Analysis</span>
          </button>
          <span style={styles.footerInfo}>Local Ollama CPU</span>
        </div>
      </div>

      {/* Detailed Analysis Modal */}
      <DetailedAnalysisModal
        isOpen={showDetailedModal}
        onClose={() => setShowDetailedModal(false)}
        models={models}
      />
    </>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrapper: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    background: 'rgba(24, 25, 28, 0.88)',
    backdropFilter: 'blur(16px)',
    WebkitBackdropFilter: 'blur(16px)',
    borderLeft: '1px solid rgba(255, 255, 255, 0.08)',
    overflow: 'hidden',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '14px 16px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
    background: 'rgba(0, 0, 0, 0.1)',
    flexShrink: 0,
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
  },
  headerIconWrap: {
    width: 28,
    height: 28,
    borderRadius: 8,
    background: 'rgba(138, 180, 248, 0.12)',
    color: '#8ab4f8',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  headerTitle: {
    fontSize: 13,
    fontWeight: 600,
    color: '#e3e3e3',
    display: 'block',
  },
  headerSub: {
    fontSize: 10,
    color: '#9aa0a6',
    marginTop: 1,
  },
  badge: {
    fontSize: 10,
    fontWeight: 600,
    borderRadius: 16,
    padding: '2px 8px',
    border: '1px solid',
    flexShrink: 0,
  },
  decisionBanner: {
    margin: '10px 12px 0',
    padding: '10px 14px',
    background: 'rgba(255, 255, 255, 0.03)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: 12,
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexShrink: 0,
  },
  bannerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
  },
  bannerPulse: {
    position: 'relative',
    width: 12,
    height: 12,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  pulseRing: {
    position: 'absolute',
    width: 12,
    height: 12,
    borderRadius: '50%',
    border: '2px solid rgba(52,211,153,0.4)',
    animation: 'pulseGlow 2s ease infinite',
  },
  pulseDot: {
    width: 6,
    height: 6,
    borderRadius: '50%',
    background: 'var(--green)',
  },
  bannerLabel: {
    fontSize: 10,
    color: '#9aa0a6',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.04em',
  },
  bannerModel: {
    fontSize: 13,
    fontWeight: 600,
    color: '#e3e3e3',
    marginTop: 1,
  },
  complexityBadge: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-end',
    gap: 3,
  },
  complexityTopRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
  },
  complexityLabel: {
    fontSize: 9,
    color: '#9aa0a6',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.04em',
  },
  complexityScore: {
    fontSize: 13,
    fontWeight: 700,
    color: '#8ab4f8',
  },
  miniSliderTrack: {
    position: 'relative',
    width: 64,
    height: 3,
    borderRadius: 2,
    background: 'rgba(255, 255, 255, 0.1)',
  },
  miniSliderFill: {
    height: '100%',
    borderRadius: 2,
    background: 'linear-gradient(90deg, #34d399, #8ab4f8)',
  },
  miniSliderThumb: {
    position: 'absolute',
    top: -2.5,
    width: 8,
    height: 8,
    borderRadius: '50%',
    background: '#8ab4f8',
    boxShadow: '0 0 4px rgba(138, 180, 248, 0.8)',
  },
  sections: {
    flex: 1,
    overflowY: 'auto',
    padding: '10px 12px',
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  section: {
    background: 'rgba(255, 255, 255, 0.02)',
    borderRadius: 10,
    border: '1px solid rgba(255, 255, 255, 0.06)',
    overflow: 'hidden',
  },
  sectionHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    width: '100%',
    padding: '10px 12px',
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    textAlign: 'left' as const,
  },
  sectionHeaderLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
  },
  sectionIcon: {
    color: '#8ab4f8',
    display: 'flex',
    alignItems: 'center',
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: 600,
    color: '#e3e3e3',
  },
  chevron: {
    color: '#9aa0a6',
    transition: 'transform 0.2s ease',
    display: 'flex',
    alignItems: 'center',
  },
  sectionBody: {
    padding: '0 12px 12px',
    borderTop: '1px solid rgba(255, 255, 255, 0.04)',
    paddingTop: 10,
  },

  modelStatusList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 5,
  },
  modelStatusRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '7px 9px',
    borderRadius: 8,
    background: 'rgba(255, 255, 255, 0.02)',
    border: '1px solid rgba(255, 255, 255, 0.04)',
  },
  modelRowLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: '50%',
    flexShrink: 0,
  },
  name: {
    fontSize: 12,
    fontWeight: 500,
    color: '#e3e3e3',
  },
  role: {
    fontSize: 10,
    color: '#9aa0a6',
  },
  modelRowRight: {
    textAlign: 'right' as const,
  },
  lat: {
    fontSize: 11,
    fontWeight: 600,
    color: '#8ab4f8',
    fontFamily: 'monospace',
  },
  cap: {
    fontSize: 10,
    color: '#9aa0a6',
  },
  emptyMsg: {
    fontSize: 12,
    color: '#5f6368',
    textAlign: 'center' as const,
    padding: '8px 0',
  },
  footer: {
    padding: '12px 14px',
    borderTop: '1px solid rgba(255, 255, 255, 0.06)',
    background: 'rgba(0, 0, 0, 0.1)',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexShrink: 0,
  },
  analysisBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: 7,
    fontSize: 12,
    fontWeight: 500,
    color: '#8ab4f8',
    background: 'rgba(138, 180, 248, 0.1)',
    border: '1px solid rgba(138, 180, 248, 0.2)',
    borderRadius: 8,
    padding: '6px 12px',
    cursor: 'pointer',
    transition: 'all 0.15s ease',
  },
  footerInfo: {
    fontSize: 10,
    color: '#5f6368',
  },
};
