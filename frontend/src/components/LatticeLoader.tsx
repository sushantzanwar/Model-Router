import React, { useEffect, useLayoutEffect, useRef, useState } from 'react';

type GridSize = 3 | 4;
type LoaderStatus = 'working' | 'done' | 'error';
type LoaderShape = 'square' | 'round';

interface PatternDef {
  cells: (number | null)[];
  loop?: number;
  scale?: number;
  lit?: number;
}

export interface LatticeLoaderProps {
  label?: string;
  doneLabel?: string;
  errorLabel?: string;
  status?: LoaderStatus;
  pattern?: string | PatternDef;
  grid?: GridSize;
  shape?: LoaderShape;
  color?: string;
  doneColor?: string;
  errorColor?: string;
  cellSize?: number;
  gap?: number;
  fontSize?: number;
  step?: number;
  idleOpacity?: number;
  glow?: boolean;
  glowColor?: string;
  showTimer?: boolean;
  elapsed?: number;
  className?: string;
  style?: React.CSSProperties;
}

const PATTERNS: Record<string, Partial<Record<GridSize, PatternDef>>> = {
  arrow: { 3: { cells: [1, 2, 3, 0, 1, 2, 1, 2, 3], loop: 7.2, scale: 1 } },
  dots: { 3: { cells: [0, 1, 2, 0, 1, 2, 0, 1, 2], loop: 3, scale: 2.4 } },
  ripple: { 3: { cells: [2, 1, 2, 1, 0, 1, 2, 1, 2], loop: 4.8, scale: 1.5 } },
  spiral: { 3: { cells: [0, 1, 2, 7, 8, 3, 6, 5, 4], loop: 9, scale: 1.2, lit: 0.35 } },
  orbit: {
    3: { cells: [0, 1, 2, 7, null, 3, 6, 5, 4], loop: 8, scale: 1.2 },
    4: {
      cells: [0, 1, 2, 3, 11, null, null, 4, 10, null, null, 5, 9, 8, 7, 6],
      loop: 6,
      scale: 1.2,
      lit: 0.45,
    },
  },
  snake: {
    3: { cells: [0, 1, 2, 5, 4, 3, 6, 7, 8], loop: 9, scale: 1, lit: 0.35 },
    4: {
      cells: [0, 1, 2, 3, 7, 6, 5, 4, 8, 9, 10, 11, 15, 14, 13, 12],
      loop: 16,
      scale: 1,
      lit: 0.25,
    },
  },
  sweep: {
    4: {
      cells: [0, 1, 2, 3, 1, 2, 3, 4, 2, 3, 4, 5, 3, 4, 5, 6],
      loop: 5,
      scale: 1,
      lit: 0.45,
    },
  },
  spin: {
    4: {
      cells: [0, 0, 1, 1, 0, 0, 1, 1, 3, 3, 2, 2, 3, 3, 2, 2],
      loop: 4,
      scale: 1.6,
      lit: 0.35,
    },
  },
  rain: {
    4: {
      cells: [0, 2, 1, 3, 1, 3, 2, 4, 2, 4, 3, 5, 3, 5, 4, 6],
      loop: 4,
      scale: 1.2,
      lit: 0.35,
    },
  },
  pulse: {
    4: {
      cells: [2, 1, 1, 2, 1, 0, 0, 1, 1, 0, 0, 1, 2, 1, 1, 2],
      loop: 2.4,
      scale: 2.5,
      lit: 0.45,
    },
  },
};

const DEFAULT_PATTERN: Record<GridSize, string> = { 3: 'orbit', 4: 'sweep' };

const MARKS: Record<GridSize, { done: number[]; error: number[] }> = {
  3: { done: [2, 3, 5, 7], error: [0, 2, 4, 6, 8] },
  4: { done: [7, 8, 10, 13], error: [0, 3, 5, 6, 9, 10, 12, 15] },
};

const resolvePattern = (pattern: string | PatternDef, grid: GridSize): PatternDef => {
  if (typeof pattern === 'string') {
    const named = PATTERNS[pattern];
    return (
      (named && named[grid]) ||
      PATTERNS[DEFAULT_PATTERN[grid]][grid] || {
        cells: [],
        loop: 8,
        scale: 1.2,
      }
    );
  }
  const cells = Array.from(
    { length: grid * grid },
    (_, i) => pattern.cells[i] ?? null
  );
  const validNumbers = cells.filter((v): v is number => v != null);
  const max = validNumbers.length > 0 ? Math.max(...validNumbers) : 0;
  return {
    cells,
    loop: pattern.loop ?? max + 4.2,
    scale: pattern.scale ?? 1,
    lit: pattern.lit ?? 0.62,
  };
};

const STYLE = `
@keyframes lattice-on {
  0%, 100% { opacity: var(--ll-idle); }
  18%, 42% { opacity: var(--ll-peak); }
  62% { opacity: var(--ll-idle); }
}
@keyframes lattice-on-45 {
  0%, 100% { opacity: var(--ll-idle); }
  13%, 31% { opacity: var(--ll-peak); }
  45% { opacity: var(--ll-idle); }
}
@keyframes lattice-on-35 {
  0%, 100% { opacity: var(--ll-idle); }
  10%, 24% { opacity: var(--ll-peak); }
  35% { opacity: var(--ll-idle); }
}
@keyframes lattice-on-25 {
  0%, 100% { opacity: var(--ll-idle); }
  7%, 17% { opacity: var(--ll-peak); }
  25% { opacity: var(--ll-idle); }
}

.ll-root {
  position: relative;
  display: inline-flex;
  align-items: center;
  line-height: 1;
  font-family: inherit;
  gap: calc(var(--ll-font) * 0.625);
  font-size: var(--ll-font);
  color: var(--ll-color);
  user-select: none;
}
.ll-grid-wrap {
  display: grid;
  flex-shrink: 0;
}
.ll-run {
  grid-area: 1 / 1;
  display: grid;
  grid-template-columns: repeat(var(--ll-n), var(--ll-cell));
  gap: var(--ll-gap);
  transition: opacity 200ms ease;
}
.ll-root[data-status="done"] .ll-run,
.ll-root[data-status="error"] .ll-run {
  opacity: 0;
}
.ll-root[data-status="done"] .ll-run > span,
.ll-root[data-status="error"] .ll-run > span {
  animation-play-state: paused;
}
.ll-cell {
  height: var(--ll-cell);
  width: var(--ll-cell);
  border-radius: max(1px, calc(var(--ll-cell) * 0.25));
  background: var(--ll-color);
  transition: opacity 200ms ease, background-color 200ms ease;
}
.ll-root[data-shape="round"] .ll-cell {
  border-radius: 9999px;
}
.ll-lit-62 { animation: lattice-on var(--ll-cycle) infinite var(--ll-ease-in-out); }
.ll-lit-45 { animation: lattice-on-45 var(--ll-cycle) infinite var(--ll-ease-in-out); }
.ll-lit-35 { animation: lattice-on-35 var(--ll-cycle) infinite var(--ll-ease-in-out); }
.ll-lit-25 { animation: lattice-on-25 var(--ll-cycle) infinite var(--ll-ease-in-out); }

.ll-root[data-glow] .ll-run .ll-cell:not([data-hole]) {
  box-shadow: 0 0 calc(var(--ll-cell) * 1.2) calc(var(--ll-cell) * 0.12) var(--ll-glow);
}

.ll-mark {
  grid-area: 1 / 1;
  display: grid;
  grid-template-columns: repeat(var(--ll-n), var(--ll-cell));
  gap: var(--ll-gap);
  transform-origin: center;
  opacity: 0;
  transform: scale(0.9);
  transition: opacity 160ms var(--ll-ease-out), transform 160ms var(--ll-ease-out);
}
.ll-root[data-status="done"] .ll-mark,
.ll-root[data-status="error"] .ll-mark {
  opacity: 1;
  transform: none;
  transition: opacity 200ms ease, transform 200ms var(--ll-ease-out);
}
.ll-mark .ll-cell[data-on] {
  background: var(--ll-mark);
  opacity: var(--ll-peak);
}
.ll-root[data-glow] .ll-mark .ll-cell[data-on] {
  box-shadow: 0 0 calc(var(--ll-cell) * 1.2) calc(var(--ll-cell) * 0.12) var(--ll-mark-glow);
}

.ll-text-wrap {
  position: relative;
  display: inline-block;
  font-weight: 500;
}
.ll-text {
  position: absolute;
  top: 0;
  left: 0;
  white-space: nowrap;
  opacity: 0;
  filter: blur(2px);
  transition: opacity 200ms ease, filter 200ms ease;
}
.ll-text[data-active] {
  position: static;
  opacity: 1;
  filter: blur(0);
}
.ll-timer {
  font-family: monospace;
  font-variant-numeric: tabular-nums;
  opacity: 0.6;
  font-size: calc(var(--ll-font) * 0.875);
}
.ll-sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}

@media (prefers-reduced-motion: reduce) {
  .ll-run { --ll-peak: 0.7; }
  .ll-run > span { animation-delay: 0ms !important; animation-duration: 1400ms !important; }
  .ll-mark { transform: none !important; }
  .ll-text { filter: none !important; }
}
`;

const fmt = (ds: number) =>
  ds < 600
    ? `${(ds / 10).toFixed(1)}s`
    : `${Math.floor(ds / 600)}m ${((ds % 600) / 10).toFixed(1)}s`;

const spoken = (ds: number) =>
  ds < 600
    ? `${(ds / 10).toFixed(1)} seconds`
    : `${Math.floor(ds / 600)} minutes ${((ds % 600) / 10).toFixed(1)} seconds`;

export default function LatticeLoader({
  label = 'Thinking',
  doneLabel = 'Done in',
  errorLabel = 'Failed after',
  status = 'working',
  pattern = 'orbit',
  grid = 3,
  shape = 'round',
  color = 'currentColor',
  doneColor = '#22c55e',
  errorColor = '#ef4444',
  cellSize = 6,
  gap = 2,
  fontSize = 14,
  step = 90,
  idleOpacity = 0.15,
  glow = false,
  glowColor = '',
  showTimer = true,
  elapsed,
  className = '',
  style,
}: LatticeLoaderProps) {
  const n = grid === 4 ? 4 : 3;
  const pat = resolvePattern(pattern, n);
  const marks = MARKS[n];
  const d = step * (pat.scale ?? 1);
  const cycle = Math.round((pat.loop ?? 8) * d);

  const timerRef = useRef<HTMLSpanElement>(null);
  const dsRef = useRef(0);
  const markRef = useRef<'done' | 'error'>('done');
  const mark = status === 'working' ? markRef.current : status;
  markRef.current = mark === 'error' ? 'error' : 'done';
  const [announce, setAnnounce] = useState(`${label}, in progress`);

  const paint = (ds: number) => {
    dsRef.current = ds;
    if (timerRef.current) timerRef.current.textContent = fmt(ds);
  };

  useLayoutEffect(() => {
    if (elapsed != null) {
      paint(Math.round(elapsed * 10));
      return undefined;
    }
    if (status !== 'working') return undefined;
    const startedAt = performance.now();
    paint(0);
    const id = setInterval(
      () => paint(Math.floor((performance.now() - startedAt) / 100)),
      100
    );
    return () => clearInterval(id);
  }, [status, elapsed]);

  useEffect(() => {
    if (status === 'working') setAnnounce(`${label}, in progress`);
    else
      setAnnounce(
        `${status === 'done' ? doneLabel : errorLabel}${
          showTimer ? ` ${spoken(dsRef.current)}` : ''
        }`
      );
  }, [status, label, doneLabel, errorLabel, showTimer]);

  const litKey = Math.round((pat.lit ?? 0.62) * 100);
  const litClass =
    litKey === 45
      ? 'll-lit-45'
      : litKey === 35
      ? 'll-lit-35'
      : litKey === 25
      ? 'll-lit-25'
      : 'll-lit-62';

  return (
    <span
      role="status"
      className={`ll-root${className ? ` ${className}` : ''}`}
      data-status={status}
      data-shape={shape}
      data-glow={glow ? '' : undefined}
      style={
        {
          '--ll-n': n,
          '--ll-cell': `${cellSize}px`,
          '--ll-gap': `${gap}px`,
          '--ll-font': `${fontSize}px`,
          '--ll-color': color,
          '--ll-mark': status === 'error' ? errorColor : doneColor,
          '--ll-idle': idleOpacity,
          '--ll-glow': glowColor || color,
          '--ll-mark-glow':
            glowColor || (status === 'error' ? errorColor : doneColor),
          '--ll-cycle': `${cycle}ms`,
          '--ll-peak': 1,
          '--ll-ease-out': 'cubic-bezier(0.23, 1, 0.32, 1)',
          '--ll-ease-in-out': 'cubic-bezier(0.77, 0, 0.175, 1)',
          ...style,
        } as React.CSSProperties
      }
    >
      <style>{STYLE}</style>
      <span className="ll-grid-wrap" aria-hidden="true">
        <span className="ll-run">
          {pat.cells.map((unit, i) => (
            <span
              key={i}
              className={`ll-cell ${litClass}`}
              data-hole={unit == null ? '' : undefined}
              style={{
                opacity: unit == null ? idleOpacity * 0.47 : idleOpacity,
                animationDelay:
                  unit == null ? undefined : `${Math.round(unit * d)}ms`,
              }}
            />
          ))}
        </span>
        <span className="ll-mark">
          {pat.cells.map((_, i) => (
            <span
              key={i}
              className="ll-cell"
              style={{ opacity: idleOpacity }}
              data-on={marks[markRef.current].includes(i) ? '' : undefined}
            />
          ))}
        </span>
      </span>
      <span className="ll-text-wrap" aria-hidden="true">
        <span
          className="ll-text"
          data-active={status === 'working' ? '' : undefined}
        >
          {label}
        </span>
        <span
          className="ll-text"
          data-active={status === 'done' ? '' : undefined}
        >
          {doneLabel}
        </span>
        <span
          className="ll-text"
          data-active={status === 'error' ? '' : undefined}
        >
          {errorLabel}
        </span>
      </span>
      {showTimer ? (
        <span ref={timerRef} className="ll-timer" aria-hidden="true">
          0.0s
        </span>
      ) : null}
      <span className="ll-sr-only">{announce}</span>
    </span>
  );
}
