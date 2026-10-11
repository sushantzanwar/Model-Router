import React, { useState } from 'react';
import type { ModelInfo } from '../types';
import { patchModel } from '../api';

interface Props {
  model: ModelInfo;
  onClose: () => void;
  onSaveSuccess: (updated: ModelInfo) => void;
}

export default function ModelConfigModal({ model, onClose, onSaveSuccess }: Props) {
  const [avgLatency, setAvgLatency] = useState(model.avg_latency_ms);
  const [maxLatency, setMaxLatency] = useState(model.max_latency_ms);
  const [capability, setCapability] = useState(model.capability_score);
  const [contextLength, setContextLength] = useState(model.context_length);
  const [reliability, setReliability] = useState(model.reliability);
  const [availability, setAvailability] = useState(model.availability);
  const [enabled, setEnabled] = useState(model.enabled);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const updated = await patchModel(model.model_key, {
        avg_latency_ms: Number(avgLatency),
        max_latency_ms: Number(maxLatency),
        capability_score: Number(capability),
        context_length: Number(contextLength),
        reliability: Number(reliability),
        availability: Boolean(availability),
        enabled: Boolean(enabled),
      });
      onSaveSuccess(updated);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to update model configuration');
    } finally {
      setSaving(false);
    }
  };

  const isActive = availability && enabled;

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div style={styles.header}>
          <div style={styles.headerContent}>
            <div style={styles.titleRow}>
              <span style={styles.title}>{model.name}</span>
              <span
                style={{
                  ...styles.statusBadge,
                  background: isActive ? 'rgba(52,211,153,0.12)' : 'rgba(248,113,113,0.12)',
                  color: isActive ? '#34d399' : '#f87171',
                  borderColor: isActive ? 'rgba(52,211,153,0.3)' : 'rgba(248,113,113,0.3)',
                }}
              >
                {isActive ? '● ACTIVE' : '● OFFLINE'}
              </span>
            </div>
            <div style={styles.roleText}>{model.role}</div>
          </div>
          <button style={styles.closeBtn} onClick={onClose} aria-label="Close">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Error */}
        {error && (
          <div style={styles.errorBox}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            {error}
          </div>
        )}

        {/* Body */}
        <div style={styles.body}>
          {/* Measured latency info */}
          <div style={styles.infoBox}>
            <div style={styles.infoRow}>
              <span style={styles.infoLabel}>Measured Latency</span>
              <span style={styles.infoValue}>{model.measured_latency_ms}ms</span>
            </div>
            <p style={styles.infoHint}>
              Actual measured from latest inference. Parameters below are judge-configurable estimates.
            </p>
          </div>

          {/* Form Fields */}
          <div style={styles.formGrid}>
            <SliderField
              label="Avg Latency (avg_latency_ms)"
              hint="Used to rank candidates"
              value={avgLatency}
              min={50}
              max={20000}
              step={50}
              unit="ms"
              color="#60a5fa"
              onChange={setAvgLatency}
            />

            <SliderField
              label="Max Latency Deadline (max_latency_ms)"
              hint="Rejects if budget exceeded"
              value={maxLatency}
              min={100}
              max={30000}
              step={100}
              unit="ms"
              color="#f87171"
              onChange={setMaxLatency}
            />

            <SliderField
              label="Capability Rating"
              hint="Score for quality and reasoning"
              value={capability}
              min={1}
              max={10}
              step={0.1}
              unit="/10"
              color="#a78bfa"
              onChange={setCapability}
            />

            <SliderField
              label="Context Length Capacity"
              hint="Total context window tokens"
              value={contextLength}
              min={1024}
              max={262144}
              step={1024}
              unit=" tokens"
              color="#34d399"
              onChange={setContextLength}
            />

            <SliderField
              label="Reliability Score"
              hint="Historical stability factor (0–1)"
              value={reliability}
              min={0}
              max={1}
              step={0.01}
              unit=""
              color="#fbbf24"
              onChange={setReliability}
            />

            {/* Toggles */}
            <div style={styles.togglesRow}>
              <ToggleField
                label="Online Availability"
                hint="Mark model as available/offline"
                checked={availability}
                onChange={setAvailability}
              />
              <ToggleField
                label="Routing Enabled"
                hint="Include model in routing candidates"
                checked={enabled}
                onChange={setEnabled}
              />
            </div>
          </div>
        </div>

        {/* Footer */}
        <div style={styles.footer}>
          <button style={styles.cancelBtn} onClick={onClose} disabled={saving}>
            Cancel
          </button>
          <button
            style={{
              ...styles.saveBtn,
              opacity: saving ? 0.7 : 1,
            }}
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? (
              <>
                <span style={styles.savingDot} />
                Persisting…
              </>
            ) : (
              'Save Changes'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

function SliderField({
  label,
  hint,
  value,
  min,
  max,
  step,
  unit,
  color,
  onChange,
}: {
  label: string;
  hint: string;
  value: number;
  min: number;
  max: number;
  step: number;
  unit: string;
  color: string;
  onChange: (v: number) => void;
}) {
  const pct = ((value - min) / (max - min)) * 100;

  return (
    <div style={sliderStyles.field}>
      <div style={sliderStyles.labelRow}>
        <label style={sliderStyles.label}>{label}</label>
        <span style={{ ...sliderStyles.valueDisplay, color }}>{value}{unit}</span>
      </div>
      <p style={sliderStyles.hint}>{hint}</p>
      <div style={sliderStyles.sliderWrap}>
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          style={{
            background: `linear-gradient(90deg, ${color} ${pct}%, rgba(255,255,255,0.1) ${pct}%)`,
          }}
        />
      </div>
    </div>
  );
}

function ToggleField({
  label,
  hint,
  checked,
  onChange,
}: {
  label: string;
  hint: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div style={toggleStyles.row}>
      <div style={toggleStyles.info}>
        <span style={toggleStyles.label}>{label}</span>
        <span style={toggleStyles.hint}>{hint}</span>
      </div>
      <label className="toggle-switch">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
        />
        <span className="toggle-slider" />
      </label>
    </div>
  );
}

const sliderStyles: Record<string, React.CSSProperties> = {
  field: {
    display: 'flex',
    flexDirection: 'column',
    gap: 5,
  },
  labelRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  label: {
    fontSize: 12,
    fontWeight: 600,
    color: '#e3e3e3',
  },
  valueDisplay: {
    fontSize: 13,
    fontWeight: 700,
    fontFamily: 'monospace',
  },
  hint: {
    fontSize: 11,
    color: '#6b7280',
    marginTop: -2,
  },
  sliderWrap: {
    marginTop: 2,
  },
};

const toggleStyles: Record<string, React.CSSProperties> = {
  row: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '10px 14px',
    background: 'rgba(255,255,255,0.03)',
    borderRadius: 10,
    border: '1px solid rgba(255,255,255,0.07)',
  },
  info: {
    display: 'flex',
    flexDirection: 'column',
    gap: 2,
  },
  label: {
    fontSize: 13,
    fontWeight: 600,
    color: '#e3e3e3',
  },
  hint: {
    fontSize: 11,
    color: '#6b7280',
  },
};

const styles: Record<string, React.CSSProperties> = {
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(0, 0, 0, 0.7)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
    backdropFilter: 'blur(8px)',
    WebkitBackdropFilter: 'blur(8px)',
    animation: 'fadeSlideUp 0.2s ease',
  },
  modal: {
    background: 'rgba(25,26,28,0.97)',
    backdropFilter: 'blur(20px)',
    WebkitBackdropFilter: 'blur(20px)',
    width: '90%',
    maxWidth: 560,
    borderRadius: 18,
    boxShadow: '0 20px 60px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.08)',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    border: '1px solid rgba(255,255,255,0.1)',
  },
  header: {
    padding: '20px 24px',
    borderBottom: '1px solid rgba(255,255,255,0.07)',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  headerContent: {
    flex: 1,
  },
  titleRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    marginBottom: 4,
  },
  title: {
    fontSize: 18,
    fontWeight: 700,
    color: '#e3e3e3',
  },
  statusBadge: {
    fontSize: 10,
    fontWeight: 700,
    padding: '3px 9px',
    borderRadius: 20,
    border: '1px solid',
    letterSpacing: '0.04em',
  },
  roleText: {
    fontSize: 13,
    color: '#6b7280',
  },
  closeBtn: {
    background: 'rgba(255,255,255,0.06)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: 8,
    color: '#9aa0a6',
    cursor: 'pointer',
    width: 32,
    height: 32,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    marginLeft: 12,
  },
  errorBox: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    background: 'rgba(248,113,113,0.08)',
    color: '#f87171',
    padding: '10px 24px',
    fontSize: 13,
    borderBottom: '1px solid rgba(248,113,113,0.15)',
  },
  body: {
    padding: '20px 24px',
    maxHeight: '65vh',
    overflowY: 'auto',
    display: 'flex',
    flexDirection: 'column',
    gap: 16,
  },
  infoBox: {
    background: 'rgba(129,140,248,0.06)',
    border: '1px solid rgba(129,140,248,0.2)',
    borderRadius: 12,
    padding: '12px 16px',
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  infoRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  infoLabel: {
    fontSize: 12,
    color: '#9aa0a6',
    fontWeight: 500,
  },
  infoValue: {
    fontSize: 15,
    fontWeight: 700,
    color: '#a5b4fc',
    fontFamily: 'monospace',
  },
  infoHint: {
    fontSize: 11,
    color: '#6b7280',
    lineHeight: 1.4,
  },
  formGrid: {
    display: 'flex',
    flexDirection: 'column',
    gap: 20,
  },
  togglesRow: {
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
    paddingTop: 4,
  },
  footer: {
    padding: '16px 24px',
    borderTop: '1px solid rgba(255,255,255,0.07)',
    background: 'rgba(255,255,255,0.02)',
    display: 'flex',
    justifyContent: 'flex-end',
    gap: 12,
  },
  cancelBtn: {
    padding: '9px 18px',
    borderRadius: 10,
    border: '1px solid rgba(255,255,255,0.12)',
    background: 'rgba(255,255,255,0.05)',
    color: '#9aa0a6',
    fontSize: 13,
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'all 0.15s ease',
  },
  saveBtn: {
    padding: '9px 22px',
    borderRadius: 10,
    border: 'none',
    background: 'linear-gradient(135deg, #818cf8, #60a5fa)',
    color: '#fff',
    fontSize: 13,
    fontWeight: 700,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    boxShadow: '0 2px 12px rgba(129,140,248,0.35)',
    transition: 'all 0.15s ease',
  },
  savingDot: {
    width: 8,
    height: 8,
    borderRadius: '50%',
    border: '2px solid rgba(255,255,255,0.4)',
    borderTopColor: '#fff',
    display: 'inline-block',
    animation: 'spin 0.6s linear infinite',
  },
};
