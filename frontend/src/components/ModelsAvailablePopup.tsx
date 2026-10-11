import React, { useState } from 'react';
import type { ModelInfo } from '../types';
import ModelConfigModal from './ModelConfigModal';
import { patchModel } from '../api';

interface Props {
  models: ModelInfo[];
  onModelsChange: (models: ModelInfo[]) => void;
  selectedModelName?: string;
}

export default function ModelsAvailablePopup({
  models,
  onModelsChange,
  selectedModelName,
}: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [hoveredModelKey, setHoveredModelKey] = useState<string | null>(null);
  const [editingModel, setEditingModel] = useState<ModelInfo | null>(null);
  const [localSaving, setLocalSaving] = useState(false);

  // Default display name on the pill: use selectedModelName or lowest-level model or "Auto"
  const defaultModel = models.find((m) => m.capability_score <= 5) || models[0];
  const displayName = selectedModelName || (defaultModel ? defaultModel.name : 'Auto');

  const hoveredModel = models.find((m) => m.model_key === hoveredModelKey) || null;

  const handleModelSaved = (updated: ModelInfo) => {
    onModelsChange(
      models.map((m) => (m.model_key === updated.model_key ? updated : m))
    );
  };

  const handleQuickParamChange = async (
    model: ModelInfo,
    field: string,
    val: number
  ) => {
    // Optimistic update
    const updated = { ...model, [field]: val };
    handleModelSaved(updated);
    try {
      setLocalSaving(true);
      await patchModel(model.model_key, { [field]: val });
    } catch (err) {
      console.warn('Quick patch failed:', err);
    } finally {
      setLocalSaving(false);
    }
  };

  return (
    <div style={styles.container}>
      {/* Pill Button inside the Gemini Prompt Bar */}
      <button
        type="button"
        style={{
          ...styles.triggerPill,
          background: isOpen ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.06)',
          borderColor: isOpen ? 'rgba(255,255,255,0.2)' : 'rgba(255,255,255,0.08)',
        }}
        onClick={() => setIsOpen((v) => !v)}
        title="Select & configure routing models"
        aria-label="Model selector"
      >
        <span style={styles.modelPillName}>{displayName}</span>
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" style={{ opacity: 0.7 }}>
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {/* Floating Dialog Area */}
      {isOpen && (
        <>
          <div
            style={styles.backdrop}
            onClick={() => {
              setIsOpen(false);
              setHoveredModelKey(null);
            }}
          />

          <div style={styles.dialogContainer}>
            {/* ── Dialog Box 01: List of Models ── */}
            <div style={styles.dialog01}>
              <div style={styles.dialog01Header}>
                <span>Available Models</span>
                <span style={styles.hintText}>Hover to edit parameters</span>
              </div>

              <div style={styles.modelsList}>
                {models.map((m) => {
                  const isOnline = m.availability && m.enabled;
                  const isHovered = hoveredModelKey === m.model_key;

                  return (
                    <div
                      key={m.model_key}
                      style={{
                        ...styles.modelRowItem,
                        background: isHovered
                          ? 'rgba(255, 255, 255, 0.08)'
                          : 'transparent',
                      }}
                      onMouseEnter={() => setHoveredModelKey(m.model_key)}
                      onClick={() => {
                        setEditingModel(m);
                        setIsOpen(false);
                      }}
                    >
                      <span
                        style={{
                          ...styles.statusDot,
                          background: isOnline ? 'var(--green)' : 'var(--red)',
                          boxShadow: isOnline ? '0 0 6px rgba(52,211,153,0.5)' : 'none',
                        }}
                      />
                      <div style={styles.modelNameCol}>
                        <span style={styles.modelRowName}>{m.name}</span>
                        <span style={styles.modelRowRole}>{m.role}</span>
                      </div>
                      <span style={styles.capScore}>{m.capability_score}/10</span>
                      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ opacity: 0.5 }}>
                        <polyline points="9 18 15 12 9 6" />
                      </svg>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* ── Dialog Box 02: Sliders on Hover ── */}
            {hoveredModel && (
              <div style={styles.dialog02}>
                <div style={styles.dialog02Header}>
                  <div style={styles.dialog02Title}>{hoveredModel.name} Parameters</div>
                  <button
                    style={styles.fullEditBtn}
                    onClick={() => {
                      setEditingModel(hoveredModel);
                      setIsOpen(false);
                    }}
                  >
                    Full Config ↗
                  </button>
                </div>

                <div style={styles.slidersList}>
                  {/* Slider 1: Max Latency */}
                  <div style={styles.sliderGroup}>
                    <div style={styles.sliderLabelRow}>
                      <span style={styles.paramLabel}>Max Latency</span>
                      <span style={styles.paramVal}>{hoveredModel.max_latency_ms}ms</span>
                    </div>
                    <input
                      type="range"
                      min={200}
                      max={12000}
                      step={100}
                      value={hoveredModel.max_latency_ms}
                      onChange={(e) =>
                        handleQuickParamChange(
                          hoveredModel,
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
                      <span style={styles.paramVal}>${(hoveredModel.cost_per_1k_tokens / 1000).toFixed(5)}</span>
                    </div>
                    <input
                      type="range"
                      min={0}
                      max={0.001}
                      step={0.00005}
                      value={hoveredModel.cost_per_1k_tokens / 1000}
                      onChange={(e) =>
                        handleQuickParamChange(
                          hoveredModel,
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
                      <span style={styles.paramVal}>{hoveredModel.capability_score}/10</span>
                    </div>
                    <input
                      type="range"
                      min={1}
                      max={10}
                      step={0.1}
                      value={hoveredModel.capability_score}
                      onChange={(e) =>
                        handleQuickParamChange(
                          hoveredModel,
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
                      <span style={styles.paramVal}>{Math.round(hoveredModel.context_length / 1024)}K</span>
                    </div>
                    <input
                      type="range"
                      min={4096}
                      max={131072}
                      step={4096}
                      value={hoveredModel.context_length}
                      onChange={(e) =>
                        handleQuickParamChange(
                          hoveredModel,
                          'context_length',
                          Number(e.target.value)
                        )
                      }
                    />
                  </div>
                </div>

                <div style={styles.dialog02Footer}>
                  <span style={styles.saveStatus}>
                    {localSaving ? 'Saving…' : '● Changes synced live'}
                  </span>
                </div>
              </div>
            )}
          </div>
        </>
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
  container: {
    position: 'relative',
    display: 'inline-flex',
    alignItems: 'center',
  },
  triggerPill: {
    display: 'flex',
    alignItems: 'center',
    gap: 7,
    padding: '6px 14px',
    borderRadius: 20,
    border: '1px solid rgba(255, 255, 255, 0.08)',
    fontSize: 12,
    fontWeight: 500,
    color: '#e3e3e3',
    cursor: 'pointer',
    transition: 'all 0.15s ease',
  },
  modelPillName: {
    maxWidth: 140,
    whiteSpace: 'nowrap' as const,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  backdrop: {
    position: 'fixed',
    inset: 0,
    zIndex: 800,
  },
  dialogContainer: {
    position: 'absolute',
    bottom: 'calc(100% + 12px)',
    left: 0,
    display: 'flex',
    alignItems: 'flex-start',
    gap: 8,
    zIndex: 850,
    animation: 'fadeSlideUp 0.15s ease-out',
  },
  dialog01: {
    width: 250,
    background: 'rgba(30, 31, 32, 0.95)',
    backdropFilter: 'blur(18px)',
    WebkitBackdropFilter: 'blur(18px)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: 16,
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.5)',
    padding: '10px 0',
    overflow: 'hidden',
  },
  dialog01Header: {
    display: 'flex',
    flexDirection: 'column',
    padding: '4px 14px 8px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
    fontSize: 12,
    fontWeight: 600,
    color: '#e3e3e3',
  },
  hintText: {
    fontSize: 10,
    color: '#9aa0a6',
    fontWeight: 400,
  },
  modelsList: {
    display: 'flex',
    flexDirection: 'column',
    padding: '4px 6px',
    gap: 2,
  },
  modelRowItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '8px 10px',
    borderRadius: 8,
    cursor: 'pointer',
    transition: 'background 0.1s ease',
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: '50%',
    flexShrink: 0,
  },
  modelNameCol: {
    display: 'flex',
    flexDirection: 'column',
    flex: 1,
    minWidth: 0,
  },
  modelRowName: {
    fontSize: 12,
    fontWeight: 500,
    color: '#e3e3e3',
    whiteSpace: 'nowrap' as const,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  modelRowRole: {
    fontSize: 9,
    color: '#9aa0a6',
  },
  capScore: {
    fontSize: 10,
    fontWeight: 600,
    color: '#8ab4f8',
    background: 'rgba(138, 180, 248, 0.1)',
    padding: '1px 5px',
    borderRadius: 4,
  },
  dialog02: {
    width: 280,
    background: 'rgba(30, 31, 32, 0.95)',
    backdropFilter: 'blur(18px)',
    WebkitBackdropFilter: 'blur(18px)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: 16,
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.5)',
    padding: '12px 16px',
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
    animation: 'fadeSlideUp 0.12s ease-out',
  },
  dialog02Header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
    paddingBottom: 8,
  },
  dialog02Title: {
    fontSize: 12,
    fontWeight: 600,
    color: '#e3e3e3',
  },
  fullEditBtn: {
    background: 'rgba(255, 255, 255, 0.06)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    color: '#8ab4f8',
    borderRadius: 6,
    fontSize: 10,
    fontWeight: 500,
    padding: '3px 7px',
    cursor: 'pointer',
  },
  slidersList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 10,
  },
  sliderGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: 4,
  },
  sliderLabelRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  paramLabel: {
    fontSize: 11,
    color: '#9aa0a6',
  },
  paramVal: {
    fontSize: 11,
    fontWeight: 600,
    color: '#e3e3e3',
    fontFamily: 'monospace',
  },
  dialog02Footer: {
    borderTop: '1px solid rgba(255, 255, 255, 0.06)',
    paddingTop: 8,
    display: 'flex',
    justifyContent: 'flex-end',
  },
  saveStatus: {
    fontSize: 10,
    color: '#34d399',
  },
};
