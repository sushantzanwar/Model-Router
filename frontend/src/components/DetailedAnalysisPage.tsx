import React, { useState, useEffect } from 'react';
import type { AuditEntry, ModelInfo } from '../types';
import { fetchLogs, fetchModels } from '../api';
import GradientWaves from './GradientWaves';
import { WobbleCard } from './ui/wobble-card';

interface Props {
  models: ModelInfo[];
  onBack: () => void;
}

export default function DetailedAnalysisPage({ models: initialModels, onBack }: Props) {
  const [models, setModels] = useState<ModelInfo[]>(initialModels);
  const [logs, setLogs] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);

  // Fetch real-time telemetry logs and models from backend
  const loadData = () => {
    Promise.all([fetchLogs(), fetchModels()])
      .then(([logsData, modelsData]) => {
        setLogs(logsData || []);
        if (modelsData && modelsData.length > 0) {
          setModels(modelsData);
        }
      })
      .catch((err) => console.warn('Failed to load telemetry:', err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    setLoading(true);
    loadData();
    const interval = setInterval(loadData, 4000);
    return () => clearInterval(interval);
  }, []);

  const totalReqs = logs.length;
  const successfulReqs = logs.filter((l) => l.success !== false).length;
  const successRate = totalReqs > 0 ? Math.round((successfulReqs / totalReqs) * 100) : 100;
  const avgLatency =
    totalReqs > 0
      ? Math.round(
          logs.reduce((acc, l) => acc + (l.response_time_ms || 0), 0) / totalReqs
        )
      : 0;

  // Real model usage frequencies from backend audit logs
  const modelUsageCounts: Record<string, number> = {};
  logs.forEach((l) => {
    const m = l.model_used || l.model || 'Unknown';
    modelUsageCounts[m] = (modelUsageCounts[m] || 0) + 1;
  });
  const modelUsageList = Object.entries(modelUsageCounts).sort((a, b) => b[1] - a[1]);

  // Model-specific actual latency from backend
  const modelLatencyMap: Record<string, { total: number; count: number }> = {};
  logs.forEach((l) => {
    const m = l.model_used || l.model || 'Unknown';
    if (!modelLatencyMap[m]) modelLatencyMap[m] = { total: 0, count: 0 };
    modelLatencyMap[m].total += l.response_time_ms || 0;
    modelLatencyMap[m].count += 1;
  });

  // Spider / Radar Graph Dimensions & Axes
  // Attributes: Capability (0-10), Speed (Inverse Latency), Context Window, Cost Efficiency, Reliability
  const radarDimensions = [
    { key: 'capability', label: 'Capability (IQ)', max: 10 },
    { key: 'speed', label: 'Speed Score', max: 10 },
    { key: 'context', label: 'Context Size', max: 128 },
    { key: 'costEff', label: 'Cost Efficiency', max: 10 },
    { key: 'reliability', label: 'Reliability', max: 100 },
  ];

  // Distinct theme colors for model polygon overlays
  const modelColors = ['#f43f5e', '#38bdf8', '#a855f7', '#34d399', '#fbbf24', '#f97316'];

  // Radar chart calculation: Center (160, 160), Radius 110
  const cx = 160;
  const cy = 160;
  const r = 105;
  const numAxes = radarDimensions.length;

  const getAxisPoint = (index: number, factor: number) => {
    const angle = (Math.PI * 2 * index) / numAxes - Math.PI / 2;
    return {
      x: cx + r * factor * Math.cos(angle),
      y: cy + r * factor * Math.sin(angle),
    };
  };

  return (
    <div style={styles.page}>
      {/* Background Gradient Waves - Exactly matching main page */}
      <div style={styles.wavesBg}>
        <GradientWaves
          horizonColor="#5227FF"
          waveColor="#FF9FFC"
          crestColor="#FFFFFF"
          speed={0.4}
          amplitude={2.5}
          waveScale={0.6}
          waveRatio={0.9}
          swell={35}
          turbulence={15.5}
          tilt={1.11}
          zoom={1.0}
          height={5.5}
          fogDepth={15}
          detail="medium"
          brightness={1.0}
          opacity={0.5}
          mouseInteraction={true}
          parallaxStrength={0.5}
          grain={true}
          grainIntensity={0.05}
        />
      </div>

      {/* Main Content Container */}
      <div style={styles.contentWrap}>
        {/* Navigation / Top Header */}
        <header style={styles.header}>
          <div style={styles.headerLeft}>
            <button
              type="button"
              style={styles.backBtn}
              onClick={onBack}
              title="Return to Model Router"
              aria-label="Back to chat"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="19" y1="12" x2="5" y2="12" />
                <polyline points="12 19 5 12 12 5" />
              </svg>
              <span>Back to Chat</span>
            </button>

            <div style={styles.dividerV} />

            <div style={styles.brandRow}>
              <img src="/logo-icon.png" alt="Invaders 4.0 Logo" style={styles.logoImg} />
              <div>
                <h1 style={styles.title}>Detailed Routing Analysis</h1>
                <p style={styles.subtitle}>Dynamic multi-model spider radar analysis & real-time backend telemetry</p>
              </div>
            </div>
          </div>

          <div style={styles.headerRight}>
            <span style={styles.livePill}>
              <span style={styles.pulseDot} />
              Backend Syncing Live
            </span>
          </div>
        </header>

        {/* Scrollable Dashboard Body */}
        <main style={styles.scrollArea}>
          {/* Top Metric Cards with distinct opaque styling */}
          <div style={styles.statsGrid}>
            <div style={{ ...styles.statCard, borderTop: '3px solid #8ab4f8' }}>
              <span style={styles.statLabel}>Total Inferences</span>
              <span style={styles.statVal}>{totalReqs}</span>
              <span style={styles.statSub}>Audit queries routed</span>
            </div>
            <div style={{ ...styles.statCard, borderTop: '3px solid #34d399' }}>
              <span style={styles.statLabel}>Success Rate</span>
              <span style={{ ...styles.statVal, color: '#34d399' }}>{successRate}%</span>
              <span style={styles.statSub}>{successfulReqs} of {totalReqs} completed</span>
            </div>
            <div style={{ ...styles.statCard, borderTop: '3px solid #a855f7' }}>
              <span style={styles.statLabel}>Average Latency</span>
              <span style={{ ...styles.statVal, color: '#c084fc' }}>{avgLatency}ms</span>
              <span style={styles.statSub}>End-to-end execution</span>
            </div>
            <div style={{ ...styles.statCard, borderTop: '3px solid #f43f5e' }}>
              <span style={styles.statLabel}>Registered Engines</span>
              <span style={styles.statVal}>{models.length}</span>
              <span style={styles.statSub}>{models.filter((m) => m.availability && m.enabled).length} online & active</span>
            </div>
          </div>

          {/* Wobble Cards Grid: Solid & Gradient Colors Matching Provided Example */}
          <div style={styles.wobbleGrid}>
            {/* Card 1: Spider / Radar Graph Multi-Model Benchmark (Solid Deep Fuchsia/Crimson Card) */}
            <WobbleCard
              containerClassName="col-span-1 lg:col-span-2 min-h-[380px]"
              style={{
                background: 'linear-gradient(135deg, #881337 0%, #9f1239 50%, #4c0519 100%)',
                border: '1px solid rgba(251, 113, 133, 0.3)',
                boxShadow: '0 20px 40px rgba(136, 19, 55, 0.45)',
              }}
            >
              <div style={styles.cardInner}>
                <div style={styles.cardHeader}>
                  <div>
                    <h2 style={styles.cardTitle}>Multi-Model Spider Radar Benchmark</h2>
                    <p style={styles.cardDesc}>Geometric multi-axis performance & capability profile computed from backend parameters</p>
                  </div>
                  <span style={{ ...styles.tagBadge, background: 'rgba(255, 255, 255, 0.15)', borderColor: 'rgba(255, 255, 255, 0.3)', color: '#fff' }}>
                    Spider Graph
                  </span>
                </div>

                <div style={styles.radarLayout}>
                  {/* SVG Spider / Radar Plot */}
                  <div style={styles.radarSvgWrap}>
                    <svg width="320" height="320" viewBox="0 0 320 320" style={{ overflow: 'visible' }}>
                      {/* Concentric Web Polygons (20%, 40%, 60%, 80%, 100%) */}
                      {[0.2, 0.4, 0.6, 0.8, 1.0].map((level, lvlIdx) => {
                        const pts = Array.from({ length: numAxes })
                          .map((_, i) => {
                            const p = getAxisPoint(i, level);
                            return `${p.x},${p.y}`;
                          })
                          .join(' ');
                        return (
                          <polygon
                            key={lvlIdx}
                            points={pts}
                            fill="none"
                            stroke="rgba(255, 255, 255, 0.18)"
                            strokeWidth="1"
                            strokeDasharray={level === 1.0 ? 'none' : '3 3'}
                          />
                        );
                      })}

                      {/* Radial Axis Spokes */}
                      {Array.from({ length: numAxes }).map((_, i) => {
                        const p = getAxisPoint(i, 1.0);
                        return (
                          <line
                            key={i}
                            x1={cx}
                            y1={cy}
                            x2={p.x}
                            y2={p.y}
                            stroke="rgba(255, 255, 255, 0.28)"
                            strokeWidth="1.2"
                          />
                        );
                      })}

                      {/* Dimension Labels */}
                      {radarDimensions.map((dim, i) => {
                        const p = getAxisPoint(i, 1.18);
                        return (
                          <text
                            key={dim.key}
                            x={p.x}
                            y={p.y}
                            textAnchor="middle"
                            dominantBaseline="central"
                            fill="#fef08a"
                            fontSize="10"
                            fontWeight="600"
                            letterSpacing="0.02em"
                          >
                            {dim.label}
                          </text>
                        );
                      })}

                      {/* Model Data Polygons from Backend Models */}
                      {models.map((m, mIdx) => {
                        const col = modelColors[mIdx % modelColors.length];
                        const capFactor = Math.min(1, Math.max(0.1, m.capability_score / 10));
                        // Speed factor: 12000ms is slow (0.1), 300ms is fast (1.0)
                        const speedFactor = Math.min(1, Math.max(0.15, (12000 - Math.min(m.avg_latency_ms, 11000)) / 11500));
                        // Context factor: 4K is 0.2, 128K is 1.0
                        const ctxFactor = Math.min(1, Math.max(0.2, (m.context_length / 1024) / 128));
                        // Cost efficiency: cheaper is higher score
                        const costFactor = Math.min(1, Math.max(0.2, (0.001 - Math.min(m.cost_per_1k_tokens / 1000, 0.0009)) / 0.001));
                        // Reliability
                        const relFactor = Math.min(1, Math.max(0.2, m.reliability || 0.9));

                        const factors = [capFactor, speedFactor, ctxFactor, costFactor, relFactor];
                        const polygonPts = factors
                          .map((f, fIdx) => {
                            const p = getAxisPoint(fIdx, f);
                            return `${p.x},${p.y}`;
                          })
                          .join(' ');

                        return (
                          <g key={m.model_key}>
                            <polygon
                              points={polygonPts}
                              fill={col}
                              fillOpacity="0.22"
                              stroke={col}
                              strokeWidth="2.2"
                            />
                            {/* Vertices */}
                            {factors.map((f, fIdx) => {
                              const p = getAxisPoint(fIdx, f);
                              return <circle key={fIdx} cx={p.x} cy={p.y} r="3.5" fill={col} stroke="#fff" strokeWidth="1" />;
                            })}
                          </g>
                        );
                      })}
                    </svg>
                  </div>

                  {/* Legend of Models */}
                  <div style={styles.radarLegend}>
                    <span style={styles.legendTitle}>Models Benchmark</span>
                    <div style={styles.legendItems}>
                      {models.map((m, mIdx) => {
                        const col = modelColors[mIdx % modelColors.length];
                        return (
                          <div key={m.model_key} style={styles.legendRow}>
                            <span style={{ ...styles.legendDot, background: col, boxShadow: `0 0 8px ${col}` }} />
                            <div style={{ display: 'flex', flexDirection: 'column' }}>
                              <span style={styles.legendName}>{m.name}</span>
                              <span style={styles.legendSub}>
                                Cap {m.capability_score}/10 · {m.avg_latency_ms}ms · {Math.round(m.context_length / 1024)}K ctx
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>
            </WobbleCard>

            {/* Card 2: Engine Allocation & Traffic Share (Solid Deep Royal Blue Card) */}
            <WobbleCard
              containerClassName="col-span-1 min-h-[380px]"
              style={{
                background: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 60%, #1e1b4b 100%)',
                border: '1px solid rgba(129, 140, 248, 0.3)',
                boxShadow: '0 20px 40px rgba(30, 27, 75, 0.45)',
              }}
            >
              <div style={styles.cardInner}>
                <div style={styles.cardHeader}>
                  <div>
                    <h2 style={styles.cardTitle}>Engine Allocation</h2>
                    <p style={styles.cardDesc}>Share of queries chosen by router from backend</p>
                  </div>
                </div>

                <div style={styles.allocationList}>
                  {modelUsageList.length === 0 ? (
                    <div style={styles.emptyGraph}>Awaiting prompt telemetry from gateway…</div>
                  ) : (
                    modelUsageList.map(([name, count], i) => {
                      const share = Math.round((count / (totalReqs || 1)) * 100);
                      const col = modelColors[i % modelColors.length];
                      return (
                        <div key={name} style={styles.allocationRow}>
                          <div style={styles.allocHeader}>
                            <span style={styles.allocName}>{name}</span>
                            <span style={{ ...styles.allocCount, color: col }}>{count} ({share}%)</span>
                          </div>
                          <div style={styles.progressTrack}>
                            <div
                              style={{
                                ...styles.progressFill,
                                width: `${share}%`,
                                background: `linear-gradient(90deg, ${col} 0%, #ffffff 100%)`,
                              }}
                            />
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            </WobbleCard>

            {/* Card 3: Dynamic Model Capabilities Matrix (Solid Vibrant Blue / Navy Card) */}
            <WobbleCard
              containerClassName="col-span-1 lg:col-span-3 min-h-[320px]"
              style={{
                background: 'linear-gradient(135deg, #172554 0%, #1e3a8a 50%, #172554 100%)',
                border: '1px solid rgba(96, 165, 250, 0.3)',
                boxShadow: '0 20px 40px rgba(23, 37, 84, 0.45)',
              }}
            >
              <div style={styles.cardInner}>
                <div style={styles.cardHeader}>
                  <div>
                    <h2 style={styles.cardTitle}>Registered Engines: Live Benchmark Matrix</h2>
                    <p style={styles.cardDesc}>All specifications and measured performance synchronizing live from backend</p>
                  </div>
                  <span style={{ ...styles.tagBadge, background: 'rgba(255, 255, 255, 0.15)', borderColor: 'rgba(255, 255, 255, 0.3)', color: '#fff' }}>
                    Backend Synced
                  </span>
                </div>

                <div style={styles.matrixGrid}>
                  {models.map((m, idx) => {
                    const avgLat = modelLatencyMap[m.model_key]?.count
                      ? Math.round(modelLatencyMap[m.model_key].total / modelLatencyMap[m.model_key].count)
                      : m.avg_latency_ms;
                    const capPct = (m.capability_score / 10) * 100;
                    const contextK = Math.round(m.context_length / 1024);
                    const col = modelColors[idx % modelColors.length];

                    return (
                      <div key={m.model_key} style={styles.matrixCard}>
                        <div style={styles.matrixTop}>
                          <span style={{ ...styles.matrixName, color: col }}>{m.name}</span>
                          <span style={styles.matrixRole}>{m.role}</span>
                        </div>

                        {/* Capability Bar */}
                        <div style={styles.matrixStatGroup}>
                          <div style={styles.matrixStatRow}>
                            <span style={styles.matrixStatKey}>Intelligence</span>
                            <span style={styles.matrixStatVal}>{m.capability_score}/10</span>
                          </div>
                          <div style={styles.progressTrack}>
                            <div style={{ ...styles.progressFill, width: `${capPct}%`, background: col }} />
                          </div>
                        </div>

                        {/* Benchmark Speed */}
                        <div style={styles.matrixStatGroup}>
                          <div style={styles.matrixStatRow}>
                            <span style={styles.matrixStatKey}>Speed Profile</span>
                            <span style={{ ...styles.matrixStatVal, color: '#34d399' }}>{avgLat}ms</span>
                          </div>
                          <div style={styles.progressTrack}>
                            <div
                              style={{
                                ...styles.progressFill,
                                width: `${Math.max(10, Math.min(100, 100 - (avgLat / 5000) * 100))}%`,
                                background: '#34d399',
                              }}
                            />
                          </div>
                        </div>

                        <div style={styles.matrixFooterRow}>
                          <span style={styles.matrixPill}>Context: {contextK}K</span>
                          <span style={styles.matrixPill}>Cost: ${(m.cost_per_1k_tokens / 1000).toFixed(5)}/tok</span>
                          <span style={{ ...styles.matrixPill, color: m.availability && m.enabled ? '#34d399' : '#f87171' }}>
                            {m.availability && m.enabled ? 'Online' : 'Offline'}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </WobbleCard>
          </div>

          {/* Historical Audit Trail Table with solid card theme */}
          <div style={styles.tableCard}>
            <div style={styles.tableTop}>
              <div>
                <h3 style={styles.tableTitle}>Inference Logs & Execution Audit</h3>
                <p style={styles.tableSub}>Complete chronological trace of prompt routing decisions from gateway backend</p>
              </div>
            </div>

            <div style={styles.tableScroll}>
              <div style={styles.tableHeader}>
                <span style={{ width: 100 }}>Time</span>
                <span style={{ width: 140 }}>Request ID</span>
                <span style={{ flex: 1, minWidth: 200 }}>Prompt Snapshot</span>
                <span style={{ width: 150 }}>Model Used</span>
                <span style={{ width: 100 }}>Latency</span>
                <span style={{ width: 100, textAlign: 'right' }}>Status</span>
              </div>

              {loading ? (
                <div style={styles.tableEmpty}>Loading historical audit records from backend…</div>
              ) : logs.length === 0 ? (
                <div style={styles.tableEmpty}>No audit events yet. Try sending a prompt from the main chat.</div>
              ) : (
                <div style={styles.tableRows}>
                  {logs.map((log, idx) => {
                    const isOk = log.success !== false;
                    const timeStr = log.timestamp_iso
                      ? new Date(log.timestamp_iso).toLocaleTimeString()
                      : '--:--:--';
                    const reqId = log.request_id || log.log_id || `#${idx + 1}`;

                    return (
                      <div key={log.log_id || idx} style={styles.tableRow}>
                        <span style={{ width: 100, color: '#9aa0a6', fontSize: 12 }}>{timeStr}</span>
                        <span style={{ width: 140, color: '#8ab4f8', fontSize: 12, fontFamily: 'monospace' }}>
                          {reqId}
                        </span>
                        <span style={{ flex: 1, minWidth: 200, color: '#e3e3e3', fontSize: 13 }} title={log.prompt_preview}>
                          {log.prompt_preview ? `"${log.prompt_preview}"` : '—'}
                        </span>
                        <div style={{ width: 150, display: 'flex', alignItems: 'center', gap: 6 }}>
                          <span style={{ color: '#f0f0f0', fontWeight: 500, fontSize: 12 }}>
                            {log.model_used || log.model || 'Auto'}
                          </span>
                          {log.simulated && <span style={styles.simBadge}>SIM</span>}
                        </div>
                        <span style={{ width: 100, color: '#e3e3e3', fontSize: 12, fontFamily: 'monospace' }}>
                          {log.response_time_ms ?? 0}ms
                        </span>
                        <div style={{ width: 100, textAlign: 'right' }}>
                          <span
                            style={{
                              ...styles.statusTag,
                              background: isOk ? 'rgba(52,211,153,0.18)' : 'rgba(248,113,113,0.18)',
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
          </div>
        </main>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    width: '100vw',
    height: '100vh',
    position: 'relative',
    overflow: 'hidden',
    background: '#0b0c10',
    display: 'flex',
    flexDirection: 'column',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
  wavesBg: {
    position: 'absolute',
    inset: 0,
    width: '100%',
    height: '100%',
    zIndex: 0,
    pointerEvents: 'none',
  },
  contentWrap: {
    position: 'relative',
    zIndex: 1,
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    backdropFilter: 'blur(8px)',
    WebkitBackdropFilter: 'blur(8px)',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '16px 28px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
    background: '#121316',
    flexShrink: 0,
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: 16,
  },
  backBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 8,
    background: 'rgba(255, 255, 255, 0.08)',
    border: '1px solid rgba(255, 255, 255, 0.15)',
    color: '#e3e3e3',
    padding: '8px 14px',
    borderRadius: 10,
    cursor: 'pointer',
    fontSize: 13,
    fontWeight: 500,
    transition: 'all 0.15s ease',
  },
  dividerV: {
    width: 1,
    height: 32,
    background: 'rgba(255, 255, 255, 0.12)',
  },
  brandRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
  },
  logoImg: {
    width: 40,
    height: 40,
    objectFit: 'contain',
  },
  title: {
    fontSize: 18,
    fontWeight: 600,
    color: '#f5f5f5',
    margin: 0,
    letterSpacing: '-0.01em',
  },
  subtitle: {
    fontSize: 12,
    color: '#9aa0a6',
    margin: '2px 0 0',
  },
  headerRight: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
  },
  livePill: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 7,
    background: 'rgba(52, 211, 153, 0.14)',
    border: '1px solid rgba(52, 211, 153, 0.3)',
    color: '#34d399',
    fontSize: 11,
    fontWeight: 500,
    padding: '5px 12px',
    borderRadius: 20,
  },
  pulseDot: {
    width: 7,
    height: 7,
    borderRadius: '50%',
    background: '#34d399',
    boxShadow: '0 0 8px #34d399',
  },
  scrollArea: {
    flex: 1,
    overflowY: 'auto',
    padding: '24px 32px 48px',
    display: 'flex',
    flexDirection: 'column',
    gap: 24,
    maxWidth: 1380,
    width: '100%',
    margin: '0 auto',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
    gap: 16,
  },
  statCard: {
    background: '#18191d',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: 16,
    padding: '18px 20px',
    display: 'flex',
    flexDirection: 'column',
    gap: 4,
    boxShadow: '0 6px 24px rgba(0, 0, 0, 0.4)',
  },
  statLabel: {
    fontSize: 11,
    color: '#9aa0a6',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    fontWeight: 500,
  },
  statVal: {
    fontSize: 28,
    fontWeight: 700,
    color: '#f5f5f5',
    letterSpacing: '-0.02em',
  },
  statSub: {
    fontSize: 11,
    color: '#71767b',
  },
  wobbleGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
    gap: 20,
  },
  cardInner: {
    padding: '26px',
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    gap: 18,
  },
  cardHeader: {
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: 12,
  },
  cardTitle: {
    fontSize: 17,
    fontWeight: 700,
    color: '#ffffff',
    margin: 0,
    letterSpacing: '-0.01em',
  },
  cardDesc: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.75)',
    margin: '4px 0 0',
  },
  tagBadge: {
    fontSize: 10,
    fontWeight: 600,
    padding: '4px 9px',
    borderRadius: 6,
    textTransform: 'uppercase',
  },
  emptyGraph: {
    flex: 1,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'rgba(255, 255, 255, 0.6)',
    fontSize: 13,
    padding: '30px 0',
  },
  radarLayout: {
    display: 'flex',
    flexWrap: 'wrap',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 24,
    minHeight: 280,
  },
  radarSvgWrap: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '10px',
  },
  radarLegend: {
    flex: 1,
    minWidth: 220,
    display: 'flex',
    flexDirection: 'column',
    gap: 10,
    background: 'rgba(0, 0, 0, 0.25)',
    padding: '14px 16px',
    borderRadius: 14,
    border: '1px solid rgba(255, 255, 255, 0.1)',
  },
  legendTitle: {
    fontSize: 11,
    fontWeight: 700,
    color: '#fef08a',
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
  },
  legendItems: {
    display: 'flex',
    flexDirection: 'column',
    gap: 10,
  },
  legendRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
  },
  legendDot: {
    width: 10,
    height: 10,
    borderRadius: '50%',
    flexShrink: 0,
  },
  legendName: {
    fontSize: 13,
    fontWeight: 600,
    color: '#ffffff',
  },
  legendSub: {
    fontSize: 11,
    color: 'rgba(255, 255, 255, 0.7)',
  },
  allocationList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 16,
    flex: 1,
    justifyContent: 'center',
  },
  allocationRow: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  allocHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  allocName: {
    fontSize: 14,
    fontWeight: 600,
    color: '#ffffff',
  },
  allocCount: {
    fontSize: 13,
    fontWeight: 700,
  },
  progressTrack: {
    width: '100%',
    height: 7,
    background: 'rgba(0, 0, 0, 0.35)',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 4,
    transition: 'width 0.4s ease',
  },
  matrixGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
    gap: 16,
  },
  matrixCard: {
    background: 'rgba(0, 0, 0, 0.25)',
    border: '1px solid rgba(255, 255, 255, 0.12)',
    borderRadius: 14,
    padding: '16px',
    display: 'flex',
    flexDirection: 'column',
    gap: 14,
  },
  matrixTop: {
    display: 'flex',
    flexDirection: 'column',
    gap: 2,
  },
  matrixName: {
    fontSize: 15,
    fontWeight: 700,
  },
  matrixRole: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.7)',
  },
  matrixStatGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  matrixStatRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  matrixStatKey: {
    fontSize: 11,
    color: 'rgba(255, 255, 255, 0.75)',
  },
  matrixStatVal: {
    fontSize: 12,
    fontWeight: 700,
    color: '#ffffff',
  },
  matrixFooterRow: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: 6,
    borderTop: '1px solid rgba(255, 255, 255, 0.1)',
    paddingTop: 10,
  },
  matrixPill: {
    fontSize: 10,
    background: 'rgba(0, 0, 0, 0.35)',
    color: '#ffffff',
    padding: '3px 7px',
    borderRadius: 4,
    fontWeight: 500,
  },
  tableCard: {
    background: '#18191d',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: 16,
    overflow: 'hidden',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.45)',
  },
  tableTop: {
    padding: '18px 24px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
  },
  tableTitle: {
    fontSize: 16,
    fontWeight: 600,
    color: '#f5f5f5',
    margin: 0,
  },
  tableSub: {
    fontSize: 12,
    color: '#9aa0a6',
    margin: '3px 0 0',
  },
  tableScroll: {
    overflowX: 'auto',
  },
  tableHeader: {
    display: 'flex',
    alignItems: 'center',
    padding: '12px 24px',
    background: 'rgba(0, 0, 0, 0.3)',
    borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
    fontSize: 11,
    fontWeight: 600,
    color: '#9aa0a6',
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
  },
  tableRows: {
    maxHeight: 400,
    overflowY: 'auto',
  },
  tableRow: {
    display: 'flex',
    alignItems: 'center',
    padding: '12px 24px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
    gap: 8,
  },
  tableEmpty: {
    padding: '36px',
    textAlign: 'center',
    color: '#71767b',
    fontSize: 13,
  },
  simBadge: {
    fontSize: 9,
    color: '#9aa0a6',
    background: 'rgba(255, 255, 255, 0.06)',
    padding: '1px 5px',
    borderRadius: 4,
  },
  statusTag: {
    fontSize: 10,
    fontWeight: 700,
    padding: '3px 8px',
    borderRadius: 4,
    display: 'inline-block',
  },
};
