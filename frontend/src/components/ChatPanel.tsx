import React, { useState, useRef, useEffect } from 'react';
import type { ChatMessage, Decision, ModelInfo } from '../types';
import { postInfer, patchModel } from '../api';
import MessageBubble from './MessageBubble';
import CrystalizedBall from './CrystalizedBall';
import LatticeLoader from './LatticeLoader';
import GlideSelect from './GlideSelect';
import ModelConfigModal from './ModelConfigModal';

interface ChatPanelProps {
  models: ModelInfo[];
  onModelsChange?: (models: ModelInfo[]) => void;
  onDecision: (decision: Decision) => void;
  inspectorOpen: boolean;
  onToggleInspector: () => void;
  onOpenSidebar: () => void;
  onResetChat?: () => void;
}

let msgCounter = 0;
function uid() {
  return `msg-${++msgCounter}-${Date.now()}`;
}

export default function ChatPanel({
  models,
  onModelsChange,
  onDecision,
  inspectorOpen,
  onToggleInspector,
  onOpenSidebar,
}: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [lastUsedModel, setLastUsedModel] = useState<string | undefined>();
  const [selectedModelKey, setSelectedModelKey] = useState<string>('auto');
  const [editingModel, setEditingModel] = useState<ModelInfo | null>(null);
  const [localSaving, setLocalSaving] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const handleQuickParamChange = async (
    model: ModelInfo,
    field: string,
    val: number
  ) => {
    const updated = { ...model, [field]: val };
    onModelsChange?.(
      models.map((m) => (m.model_key === updated.model_key ? updated : m))
    );
    try {
      setLocalSaving(true);
      await patchModel(model.model_key, { [field]: val });
    } catch (err) {
      console.warn('Quick patch failed:', err);
    } finally {
      setLocalSaving(false);
    }
  };

  const handleModelSaved = (updated: ModelInfo) => {
    onModelsChange?.(
      models.map((m) => (m.model_key === updated.model_key ? updated : m))
    );
  };
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
  }, [input]);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: ChatMessage = {
      id: uid(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const constraints = selectedModelKey !== 'auto' ? { preferred_model: selectedModelKey } : {};
      const data = await postInfer(text, constraints as any);

      if (data.decision) {
        onDecision(data.decision);
      }

      if (data.status === 'NO_VALID_MODEL' || !data.success) {
        const errorMsg: ChatMessage = {
          id: uid(),
          role: 'error',
          content: `No Valid Model: ${data.message || data.error || 'No available model satisfies the prompt constraints.'}`,
          decision: data.decision,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorMsg]);
      } else {
        const modelLabel = data.model_name || data.model_used;
        setLastUsedModel(modelLabel);

        const aiMsg: ChatMessage = {
          id: uid(),
          role: 'ai',
          content: data.response || '',
          modelName: modelLabel,
          modelKey: data.model_used,
          executionMode: data.execution_mode || (data.simulated ? 'SIMULATED' : 'REAL_OLLAMA_INFERENCE'),
          latencyMs: data.latency_ms,
          decision: data.decision,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, aiMsg]);
      }
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: uid(),
        role: 'error',
        content: `Error connecting to gateway: ${err.message}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const hasMessages = messages.length > 0;

  // The Gemini-style prompt input capsule
  const renderInputCapsule = () => (
    <div style={styles.inputCapsule}>
      {/* File Upload Button (+) */}
      <button
        style={styles.plusBtn}
        onClick={() => fileInputRef.current?.click()}
        title="Upload file or context"
        aria-label="Upload file"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
          <line x1="12" y1="5" x2="12" y2="19" />
          <line x1="5" y1="12" x2="19" y2="12" />
        </svg>
      </button>

      <input
        ref={fileInputRef}
        type="file"
        style={{ display: 'none' }}
        multiple
        onChange={(e) => {
          if (e.target.files && e.target.files.length > 0) {
            const names = Array.from(e.target.files).map((f) => f.name).join(', ');
            setInput((prev) => prev + (prev ? '\n' : '') + `[Attached: ${names}]`);
          }
          e.target.value = '';
        }}
      />

      {/* Model Selector in Chat Box using GlideSelect */}
      <div style={styles.modelPillContainer}>
        <GlideSelect
          options={[
            {
              value: 'auto',
              label: lastUsedModel ? `Auto (${lastUsedModel})` : 'Auto Router',
              tag: 'Smart',
            },
            ...models.map((m) => ({
              value: m.model_key,
              label: m.name,
              tag: `${m.avg_latency_ms}ms`,
            })),
          ]}
          value={selectedModelKey}
          onChange={(val) => setSelectedModelKey(val)}
          ariaLabel="Model Selector"
          showTags
          accentColor="#8ab4f8"
          surfaceColor="#27272a"
          highlightColor="#3f3f46"
          textColor="#f5f5f5"
          size="sm"
          radius={10}
          menuWidth={210}
          placement="bottom"
          align="left"
          popDuration={180}
          glideDuration={220}
          rememberPosition
          renderSidePanel={(activeOpt) => {
            if (!activeOpt) return null;
            if (activeOpt.value === 'auto') {
              return (
                <div style={styles.sliderFlyout}>
                  <div style={styles.flyoutHeader}>
                    <span style={styles.flyoutTitle}>⚡ Auto Router</span>
                  </div>
                  <div style={{ fontSize: 11, color: '#9aa0a6', lineHeight: 1.5 }}>
                    Autonomous engine dynamically chooses the optimal model by evaluating prompt complexity, context window, latency, and token cost.
                  </div>
                </div>
              );
            }
            const targetModel = models.find((m) => m.model_key === activeOpt.value);
            if (!targetModel) return null;
            return (
              <div style={styles.sliderFlyout}>
                <div style={styles.flyoutHeader}>
                  <div style={styles.flyoutHeaderLeft}>
                    <span style={styles.flyoutTitle}>{targetModel.name}</span>
                    <span style={styles.flyoutSubtitle}>Parameters</span>
                  </div>
                  <button
                    type="button"
                    style={styles.fullEditBtn}
                    onClick={() => setEditingModel(targetModel)}
                  >
                    Full Config ↗
                  </button>
                </div>

                <div style={styles.slidersList}>
                  {/* Slider 1: Max Latency */}
                  <div style={styles.sliderGroup}>
                    <div style={styles.sliderLabelRow}>
                      <span style={styles.paramLabel}>Max Latency</span>
                      <span style={styles.paramVal}>{targetModel.max_latency_ms}ms</span>
                    </div>
                    <input
                      type="range"
                      min={200}
                      max={12000}
                      step={100}
                      value={targetModel.max_latency_ms}
                      onChange={(e) =>
                        handleQuickParamChange(
                          targetModel,
                          'max_latency_ms',
                          Number(e.target.value)
                        )
                      }
                    />
                  </div>

                  {/* Slider 2: Max Cost / Token */}
                  <div style={styles.sliderGroup}>
                    <div style={styles.sliderLabelRow}>
                      <span style={styles.paramLabel}>Max Cost / Token</span>
                      <span style={styles.paramVal}>${(targetModel.cost_per_1k_tokens / 1000).toFixed(5)}</span>
                    </div>
                    <input
                      type="range"
                      min={0}
                      max={0.001}
                      step={0.00005}
                      value={targetModel.cost_per_1k_tokens / 1000}
                      onChange={(e) =>
                        handleQuickParamChange(
                          targetModel,
                          'cost_per_1k_tokens',
                          Number(e.target.value) * 1000
                        )
                      }
                    />
                  </div>

                  {/* Slider 3: Min Capability */}
                  <div style={styles.sliderGroup}>
                    <div style={styles.sliderLabelRow}>
                      <span style={styles.paramLabel}>Min Capability</span>
                      <span style={styles.paramVal}>{targetModel.capability_score}/10</span>
                    </div>
                    <input
                      type="range"
                      min={1}
                      max={10}
                      step={0.1}
                      value={targetModel.capability_score}
                      onChange={(e) =>
                        handleQuickParamChange(
                          targetModel,
                          'capability_score',
                          Number(e.target.value)
                        )
                      }
                    />
                  </div>

                  {/* Slider 4: Min Context */}
                  <div style={styles.sliderGroup}>
                    <div style={styles.sliderLabelRow}>
                      <span style={styles.paramLabel}>Min Context</span>
                      <span style={styles.paramVal}>{Math.round(targetModel.context_length / 1024)}K</span>
                    </div>
                    <input
                      type="range"
                      min={4096}
                      max={131072}
                      step={4096}
                      value={targetModel.context_length}
                      onChange={(e) =>
                        handleQuickParamChange(
                          targetModel,
                          'context_length',
                          Number(e.target.value)
                        )
                      }
                    />
                  </div>
                </div>

                <div style={styles.flyoutFooter}>
                  <span style={styles.saveStatus}>
                    {localSaving ? 'Saving…' : '● Changes synced live'}
                  </span>
                </div>
              </div>
            );
          }}
        />
      </div>

      {/* Textarea Input */}
      <textarea
        ref={textareaRef}
        style={styles.textarea}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask Model Router…"
        rows={1}
        disabled={loading}
        aria-label="Message input"
      />

      {/* Send Arrow Button */}
      <button
        type="button"
        style={{
          ...styles.sendBtn,
          ...(loading || !input.trim() ? styles.sendBtnDisabled : styles.sendBtnActive),
        }}
        onClick={send}
        disabled={loading || !input.trim()}
        title="Send prompt"
        aria-label="Send prompt"
      >
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <line x1="12" y1="19" x2="12" y2="5" />
          <polyline points="5 12 12 5 19 12" />
        </svg>
      </button>
    </div>
  );

  return (
    <div style={styles.wrapper}>
      {/* ── Ambient Background Dimming Animation (when ball is active) ── */}
      <div
        style={{
          ...styles.ambientDimOverlay,
          opacity: loading ? 1 : 0,
          pointerEvents: loading ? 'none' : 'none',
        }}
      />

      {/* ── Top Navigation Bar ── */}
      <header style={styles.navbar}>
        {/* Left: ONLY the clickable Logo (no text "Model Router") */}
        <button
          style={styles.logoBtn}
          onClick={onOpenSidebar}
          title="Open menu"
          aria-label="Open menu"
        >
          <img src="/logo-icon.png" alt="Model Router" style={styles.navLogoImg} />
        </button>

        <div style={styles.navCenterSpacer} />

        {/* Right: ONLY the Analytics Window Icon Button */}
        <button
          style={{
            ...styles.analyticsIconBtn,
            background: inspectorOpen ? 'rgba(255,255,255,0.08)' : 'transparent',
            color: inspectorOpen ? '#8ab4f8' : '#9aa0a6',
          }}
          onClick={onToggleInspector}
          title={inspectorOpen ? 'Hide analysis panel' : 'Show analysis panel'}
          aria-label="Toggle analysis window"
        >
          {/* Split window / Analysis panel toggle icon */}
          <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <rect x="3" y="3" width="18" height="18" rx="3" />
            <line x1="15" y1="3" x2="15" y2="21" />
          </svg>
        </button>
      </header>

      {/* ── Main Chat / Welcome Body ── */}
      <div style={styles.bodyArea}>
        {!hasMessages ? (
          /* Gemini Home Screen (Clean & Centered) */
          <div style={styles.homeCenterWrapper}>
            <div style={styles.homeGreeting}>
              <h1 style={styles.homeTitle}>Welcome to Model Router</h1>
              <p style={styles.homeSubtitle}>
                Autonomous prompt-to-model inference routing gateway
              </p>
            </div>

            {/* Input bar centered on home screen (Gemini style) */}
            <div style={styles.homeInputContainer}>
              {renderInputCapsule()}
            </div>
          </div>
        ) : (
          /* Chat Stream when messages exist */
          <div style={styles.messagesStream}>
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}

            {loading && (
              <div style={styles.loadingArea}>
                <div style={styles.ballContainer}>
                  <CrystalizedBall
                    preset="plasma"
                    color="#5b91f2"
                    size={0.7}
                    crackle={0.85}
                    fill={0.5}
                    interactive
                    hoverStrength={0.7}
                  />
                </div>
                <div style={styles.loaderContainer}>
                  <LatticeLoader
                    status="working"
                    label="Thinking"
                    doneLabel="Done in"
                    errorLabel="Failed after"
                    pattern="orbit"
                    grid={3}
                    shape="round"
                    color="#8ab4f8"
                    doneColor="#22c55e"
                    errorColor="#ef4444"
                    cellSize={6}
                    gap={2}
                    fontSize={14}
                    step={90}
                    idleOpacity={0.15}
                    glow={false}
                    glowColor=""
                    showTimer
                  />
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* ── Bottom Input Bar (when messages exist) ── */}
      {hasMessages && (
        <div style={styles.bottomInputWrap}>
          {renderInputCapsule()}
        </div>
      )}

      {/* Full Modal if opened */}
      {editingModel && (
        <ModelConfigModal
          model={editingModel}
          onClose={() => setEditingModel(null)}
          onSaveSuccess={handleModelSaved}
        />
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrapper: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    position: 'relative',
    overflow: 'hidden',
  },
  ambientDimOverlay: {
    position: 'absolute',
    inset: 0,
    background:
      'radial-gradient(ellipse at 50% 50%, rgba(91, 145, 242, 0.16) 0%, rgba(10, 12, 16, 0.78) 55%, rgba(5, 5, 8, 0.92) 100%)',
    zIndex: 1,
    pointerEvents: 'none',
    transition: 'opacity 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
  },

  // ── Navbar ──
  navbar: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '12px 20px',
    flexShrink: 0,
    zIndex: 10,
  },
  logoBtn: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    padding: '4px',
    borderRadius: 8,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'opacity 0.15s ease',
  },
  navLogoImg: {
    height: 48,
    width: 'auto',
    objectFit: 'contain',
    display: 'block',
  },
  navCenterSpacer: {
    flex: 1,
  },
  analyticsIconBtn: {
    border: 'none',
    cursor: 'pointer',
    padding: '7px',
    borderRadius: 8,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'background 0.15s ease, color 0.15s ease',
  },

  // ── Body Area ──
  bodyArea: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    position: 'relative',
    zIndex: 2,
  },

  // ── Home Center (Empty State) ──
  homeCenterWrapper: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '0 24px 60px',
    animation: 'fadeIn 0.3s ease',
  },
  homeGreeting: {
    textAlign: 'center' as const,
    marginBottom: 32,
  },
  homeTitle: {
    fontSize: 34,
    fontWeight: 600,
    color: '#e3e3e3',
    letterSpacing: '-0.02em',
    marginBottom: 8,
  },
  homeSubtitle: {
    fontSize: 15,
    color: '#9aa0a6',
    fontWeight: 400,
    letterSpacing: '-0.01em',
  },
  homeInputContainer: {
    width: '100%',
    maxWidth: 680,
  },

  // ── Messages Stream ──
  messagesStream: {
    flex: 1,
    overflowY: 'auto',
    padding: '20px 0',
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
  },
  loadingArea: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    width: '100%',
    padding: '8px 0',
  },
  ballContainer: {
    width: '100%',
    height: '420px',
    position: 'relative' as const,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  loaderContainer: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '8px 20px',
    borderRadius: 24,
    background: 'rgba(255, 255, 255, 0.05)',
    backdropFilter: 'blur(8px)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    marginTop: 8,
  },

  // ── Input Capsule ──
  bottomInputWrap: {
    padding: '12px 24px 18px',
    display: 'flex',
    justifyContent: 'center',
    flexShrink: 0,
    position: 'relative' as const,
    zIndex: 2,
  },
  inputCapsule: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    width: '100%',
    maxWidth: 720,
    background: '#1e1f20',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: 28,
    padding: '8px 12px 8px 14px',
    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.28)',
    transition: 'border-color 0.15s ease',
  },
  plusBtn: {
    background: 'none',
    border: 'none',
    color: '#9aa0a6',
    cursor: 'pointer',
    padding: 4,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    transition: 'color 0.15s ease',
  },
  modelPillContainer: {
    flexShrink: 0,
  },
  textarea: {
    flex: 1,
    border: 'none',
    outline: 'none',
    fontSize: 14,
    color: '#e3e3e3',
    background: 'transparent',
    resize: 'none',
    maxHeight: 140,
    fontFamily: 'inherit',
    lineHeight: 1.45,
    padding: '4px 0',
  },
  sendBtn: {
    border: 'none',
    borderRadius: '50%',
    width: 32,
    height: 32,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    flexShrink: 0,
    transition: 'all 0.15s ease',
  },
  sendBtnActive: {
    background: '#e3e3e3',
    color: '#131314',
  },
  sendBtnDisabled: {
    background: 'rgba(255, 255, 255, 0.08)',
    color: 'rgba(255, 255, 255, 0.2)',
    cursor: 'not-allowed',
  },
  sliderFlyout: {
    width: 290,
    background: '#1e1f20',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: 14,
    boxShadow: '0 12px 36px rgba(0, 0, 0, 0.55), 0 0 1px rgba(255, 255, 255, 0.12)',
    padding: '14px 16px',
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
  },
  flyoutHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
    paddingBottom: 10,
    gap: 8,
  },
  flyoutHeaderLeft: {
    display: 'flex',
    flexDirection: 'column',
    gap: 2,
    minWidth: 0,
  },
  flyoutTitle: {
    fontSize: 13,
    fontWeight: 600,
    color: '#f0f0f0',
    whiteSpace: 'nowrap' as const,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  flyoutSubtitle: {
    fontSize: 10,
    color: '#9aa0a6',
    fontWeight: 400,
    textTransform: 'uppercase' as const,
    letterSpacing: '0.04em',
  },
  fullEditBtn: {
    background: 'rgba(138, 180, 248, 0.1)',
    border: '1px solid rgba(138, 180, 248, 0.3)',
    color: '#8ab4f8',
    borderRadius: 7,
    fontSize: 11,
    fontWeight: 500,
    padding: '4px 9px',
    cursor: 'pointer',
    whiteSpace: 'nowrap' as const,
    flexShrink: 0,
    transition: 'all 0.15s ease',
  },
  slidersList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
  },
  sliderGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  sliderLabelRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  paramLabel: {
    fontSize: 11,
    color: '#9aa0a6',
    fontWeight: 500,
  },
  paramVal: {
    fontSize: 11,
    fontWeight: 600,
    color: '#8ab4f8',
    fontVariantNumeric: 'tabular-nums',
  },
  flyoutFooter: {
    borderTop: '1px solid rgba(255, 255, 255, 0.08)',
    paddingTop: 8,
    display: 'flex',
    justifyContent: 'flex-end',
    alignItems: 'center',
  },
  saveStatus: {
    fontSize: 10,
    color: '#34a853',
    fontWeight: 500,
  },
};
