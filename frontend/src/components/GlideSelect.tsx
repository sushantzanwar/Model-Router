import React, { useEffect, useId, useLayoutEffect, useRef, useState } from 'react';
import { HugeiconsIcon } from '@hugeicons/react';
import { ArrowDown01Icon, Tick02Icon } from '@hugeicons/core-free-icons';

export interface GlideSelectOptionObj {
  value: string;
  label: React.ReactNode;
  tag?: string;
}

export type GlideSelectOption = string | GlideSelectOptionObj;

export interface GlideSelectProps {
  options?: GlideSelectOption[];
  value?: string;
  defaultValue?: string;
  onChange?: (value: string, option: GlideSelectOptionObj) => void;
  placeholder?: string;
  showTags?: boolean;
  accentColor?: string;
  surfaceColor?: string;
  highlightColor?: string;
  textColor?: string;
  size?: 'sm' | 'md' | 'lg';
  radius?: number;
  menuWidth?: number;
  placement?: 'top' | 'bottom';
  align?: 'left' | 'right';
  popDuration?: number;
  glideDuration?: number;
  rememberPosition?: boolean;
  disabled?: boolean;
  ariaLabel?: string;
  className?: string;
  style?: React.CSSProperties;
  renderSidePanel?: (activeOption: GlideSelectOptionObj | null) => React.ReactNode;
}

const SIZES = {
  sm: { chip: 28, row: 26, font: 12 },
  md: { chip: 32, row: 30, font: 13 },
  lg: { chip: 44, row: 40, font: 14 },
};
const PAD = 4;
const GAP = 1;
const MENU_GAP = 6;
const DEFAULT_OPTIONS: GlideSelectOption[] = ['One', 'Two', 'Three'];

const STYLE = `
@keyframes gs-swap {
  from { opacity: 0.6; filter: blur(2px); }
  to { opacity: 1; filter: blur(0); }
}

.gs-root {
  position: relative;
  display: inline-block;
  user-select: none;
}
.gs-root[data-disabled] {
  opacity: 0.5;
  pointer-events: none;
}

.gs-trigger {
  position: relative;
  margin: 0;
  display: inline-flex;
  cursor: pointer;
  touch-action: manipulation;
  align-items: center;
  gap: 6px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 0 10px 0 12px;
  line-height: 1;
  font-weight: 500;
  outline: none;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
  font-family: inherit;
  height: var(--gs-chip);
  border-radius: var(--gs-inner-radius);
  background: var(--gs-surface);
  color: var(--gs-text);
  font-size: var(--gs-font);
  transition: background-color 100ms ease, transform 160ms cubic-bezier(0.23, 1, 0.32, 1), border-color 150ms ease;
}
.gs-trigger:hover:not(:disabled) {
  background: color-mix(in srgb, var(--gs-highlight) 60%, var(--gs-surface));
  border-color: rgba(255, 255, 255, 0.16);
}
.gs-trigger:active:not(:disabled) {
  transform: scale(0.97);
}
.gs-trigger[aria-expanded="true"] {
  background: color-mix(in srgb, var(--gs-highlight) 60%, var(--gs-surface));
  border-color: rgba(138, 180, 248, 0.35);
}

.gs-label-wrap {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.gs-label-wrap[data-empty] {
  opacity: 0.6;
}
.gs-root[data-swap] .gs-label-wrap {
  animation: gs-swap 160ms ease;
}

.gs-chevron {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: color-mix(in srgb, var(--gs-text) 55%, transparent);
  transition: transform 200ms cubic-bezier(0.23, 1, 0.32, 1);
}
.gs-trigger[aria-expanded="true"] .gs-chevron {
  transform: rotate(180deg);
}

.gs-menu {
  position: absolute;
  z-index: 50;
  min-width: 100%;
  padding: 4px;
  width: var(--gs-menu-w);
  border-radius: var(--gs-radius);
  background: var(--gs-surface);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5), 0 0 1px rgba(255, 255, 255, 0.15);
  transform-origin: var(--gs-origin);
  transition: opacity var(--gs-pop) cubic-bezier(0.23, 1, 0.32, 1), transform var(--gs-pop) cubic-bezier(0.23, 1, 0.32, 1);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
}
.gs-menu[data-state="closed"] {
  opacity: 0;
  transform: scale(0.95);
  pointer-events: none;
  transition-duration: var(--gs-pop-out);
}
.gs-menu[data-state="open"] {
  opacity: 1;
  transform: scale(1);
}
.gs-menu[data-side="bottom"] {
  top: calc(100% + 6px);
}
.gs-menu[data-side="top"] {
  bottom: calc(100% + 6px);
}
.gs-menu[data-align="left"] {
  left: 0;
}
.gs-menu[data-align="right"] {
  right: 0;
}

.gs-list {
  position: relative;
  display: grid;
  touch-action: none;
  gap: 1px;
}

.gs-pill {
  pointer-events: none;
  position: absolute;
  top: 0;
  right: 0;
  left: 0;
  opacity: 0;
  height: var(--gs-row);
  border-radius: var(--gs-inner-radius);
  background: var(--gs-highlight);
  transition: transform var(--gs-glide) cubic-bezier(0.23, 1, 0.32, 1), opacity 150ms ease;
}

.gs-row {
  position: relative;
  z-index: 1;
  display: flex;
  cursor: pointer;
  align-items: center;
  gap: 8px;
  padding: 0 8px 0 10px;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
  height: var(--gs-row);
  border-radius: var(--gs-inner-radius);
  color: var(--gs-text);
  font-size: var(--gs-font);
  transition: background-color 150ms ease;
}
.gs-row[aria-selected="true"] {
  background: color-mix(in srgb, var(--gs-highlight) 60%, transparent);
}
.gs-list[data-live] .gs-row[aria-selected="true"] {
  background: transparent;
}

.gs-row-label {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
}

.gs-row-tag {
  flex-shrink: 0;
  color: color-mix(in srgb, var(--gs-text) 55%, transparent);
  font-size: calc(var(--gs-font) - 2px);
  background: rgba(255, 255, 255, 0.05);
  padding: 2px 6px;
  border-radius: 4px;
}

.gs-row-check {
  display: inline-flex;
  flex-shrink: 0;
  visibility: hidden;
  color: var(--gs-accent);
}
.gs-row-check[data-on] {
  visibility: visible;
}
`;

const norm = (o: GlideSelectOption): GlideSelectOptionObj =>
  typeof o === 'string' ? { value: o, label: o } : o;

const textOf = (it: GlideSelectOptionObj): string =>
  typeof it.label === 'string' ? it.label : it.value;

const typeaheadIndex = (
  items: GlideSelectOptionObj[],
  from: number,
  ch: string
): number => {
  const c = ch.toLowerCase();
  const n = items.length;
  for (let k = 1; k <= n; k++) {
    const i = (from + k) % n;
    if (textOf(items[i]).toLowerCase().startsWith(c)) return i;
  }
  return from;
};

export default function GlideSelect({
  options = DEFAULT_OPTIONS,
  value,
  defaultValue,
  onChange,
  placeholder = 'Select…',
  showTags = true,
  accentColor = '#8ab4f8',
  surfaceColor = '#1e1f20',
  highlightColor = '#2f3134',
  textColor = '#f5f5f5',
  size = 'md',
  radius = 12,
  menuWidth = 190,
  placement = 'top',
  align = 'left',
  popDuration = 180,
  glideDuration = 220,
  rememberPosition = true,
  disabled = false,
  ariaLabel = 'Select model',
  className = '',
  style,
  renderSidePanel,
}: GlideSelectProps) {
  const items = options.map(norm);
  const [inner, setInner] = useState(defaultValue ?? '');
  const current = value ?? inner;
  const selected = items.findIndex((it) => it.value === current);
  const [phase, setPhase] = useState<'closed' | 'open' | 'closing'>('closed');
  const [active, setActive] = useState<number | null>(null);
  const [side, setSide] = useState<'top' | 'bottom'>(placement);

  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const pillRef = useRef<HTMLSpanElement>(null);
  const instant = useRef(false);
  const closeTimer = useRef<any>(undefined);
  const scrub = useRef<{ id: number; top: number } | null>(null);
  const id = useId();

  const S = SIZES[size] ?? SIZES.md;
  const step = S.row + GAP;
  const popOut = Math.round((popDuration * 2) / 3);

  useLayoutEffect(() => {
    if (phase !== 'open') return;
    const el = menuRef.current;
    const root = rootRef.current;
    if (!el || !root) return;
    const r = root.getBoundingClientRect();
    const need = el.offsetHeight + MENU_GAP;
    if (placement === 'bottom') {
      // Stay bottom unless viewport has virtually no room below and plenty above
      setSide(
        r.bottom + need > window.innerHeight && r.top > need ? 'top' : 'bottom'
      );
    } else {
      setSide(r.top - need < 0 && window.innerHeight - r.bottom > need ? 'bottom' : 'top');
    }
    el.style.transitionDuration = instant.current ? '0ms' : '';
    el.dataset.state = 'closed';
    void el.offsetHeight;
    el.dataset.state = 'open';
    const p = pillRef.current;
    if (p) {
      p.style.transition = 'none';
      p.style.transform = `translateY(${Math.max(0, selected) * step}px)`;
      p.style.opacity = '0';
      void p.offsetHeight;
      p.style.transition = '';
    }
  }, [phase, placement, selected, step]);

  useLayoutEffect(() => {
    const p = pillRef.current;
    if (!p || phase !== 'open') return;
    if (active === null) {
      p.style.opacity = '0';
      return;
    }
    const jump = instant.current || p.style.opacity !== '1';
    p.style.transitionDuration = jump ? '0ms, 150ms' : '';
    p.style.transform = `translateY(${active * step}px)`;
    p.style.opacity = '1';
    instant.current = false;
  }, [active, phase, step]);

  const open = (viaKey: boolean) => {
    if (disabled) return;
    clearTimeout(closeTimer.current);
    instant.current = true;
    setActive(selected >= 0 ? selected : viaKey ? 0 : null);
    setPhase('open');
  };

  const close = (mode: 'instant' | 'pop') => {
    setActive(null);
    clearTimeout(closeTimer.current);
    const el = menuRef.current;
    if (mode === 'instant' || !el) {
      setPhase('closed');
      return;
    }
    el.style.transitionDuration = '';
    el.dataset.state = 'closed';
    setPhase('closing');
    closeTimer.current = setTimeout(() => setPhase('closed'), popOut + 20);
  };

  const pick = (i: number, viaKey: boolean) => {
    const it = items[i];
    if (!it) {
      close('instant');
      return;
    }
    if (it.value !== current) {
      if (value === undefined) setInner(it.value);
      onChange?.(it.value, it);
      if (!viaKey && rootRef.current) rootRef.current.dataset.swap = '';
    }
    close('instant');
    triggerRef.current?.focus({ preventScroll: true });
  };

  const onTriggerKey = (e: React.KeyboardEvent<HTMLButtonElement>) => {
    const k = e.key;
    const n = items.length;
    const cur = active ?? Math.max(0, selected);
    if (phase !== 'open') {
      if (k === 'Enter' || k === ' ' || k === 'ArrowDown' || k === 'ArrowUp') {
        e.preventDefault();
        open(true);
      }
      return;
    }
    const go = (i: number) => {
      e.preventDefault();
      instant.current = true;
      setActive(Math.min(n - 1, Math.max(0, i)));
    };
    if (k === 'ArrowDown' || k === 'ArrowUp')
      go(active === null ? cur : cur + (k === 'ArrowDown' ? 1 : -1));
    else if (k === 'Home' || k === 'End') go(k === 'Home' ? 0 : n - 1);
    else if (k === 'Enter' || k === ' ') {
      e.preventDefault();
      pick(cur, true);
    } else if (k === 'Escape' || k === 'Tab') {
      if (k === 'Escape') e.preventDefault();
      close('instant');
    } else if (k.length === 1 && !e.metaKey && !e.ctrlKey && !e.altKey)
      go(typeaheadIndex(items, cur, k));
  };

  useEffect(() => {
    if (phase === 'closed') return undefined;
    const onDown = (e: PointerEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node))
        close('pop');
    };
    document.addEventListener('pointerdown', onDown, true);
    return () => document.removeEventListener('pointerdown', onDown, true);
  }, [phase]);

  useEffect(() => {
    if (disabled && phase !== 'closed') close('instant');
  }, [disabled, phase]);

  useEffect(() => () => clearTimeout(closeTimer.current), []);

  const rowAt = (y: number) => {
    const s = scrub.current;
    if (!s) return null;
    const i = Math.floor((y - s.top - PAD) / step);
    return i >= 0 && i < items.length ? i : null;
  };

  const onListDown = (e: React.PointerEvent<HTMLDivElement>) => {
    if (scrub.current) return;
    try {
      e.currentTarget.setPointerCapture(e.pointerId);
    } catch {}
    scrub.current = {
      id: e.pointerId,
      top: e.currentTarget.getBoundingClientRect().top,
    };
    instant.current = true;
    setActive(rowAt(e.clientY));
  };

  const onListMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!scrub.current || scrub.current.id !== e.pointerId) return;
    const i = rowAt(e.clientY);
    if (i !== active) setActive(i);
  };

  const onListUp = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!scrub.current || scrub.current.id !== e.pointerId) return;
    const i = e.type === 'pointerup' ? rowAt(e.clientY) : null;
    scrub.current = null;
    if (i !== null) pick(i, false);
    else if (!rememberPosition) setActive(null);
  };

  const onListOver = (e: React.PointerEvent<HTMLDivElement>) => {
    if (e.pointerType === 'touch' || scrub.current) return;
    const row = (e.target as HTMLElement).closest('[data-index]');
    if (!row) return;
    const i = Number((row as HTMLElement).dataset.index);
    if (i !== active) setActive(i);
  };

  const origin = `${side === 'bottom' ? 'top' : 'bottom'} ${align}`;

  return (
    <div
      ref={rootRef}
      className={`gs-root${className ? ` ${className}` : ''}`}
      data-size={size}
      data-disabled={disabled ? '' : undefined}
      style={
        {
          '--gs-accent': accentColor,
          '--gs-surface': surfaceColor,
          '--gs-highlight': highlightColor,
          '--gs-text': textColor,
          '--gs-radius': `${radius}px`,
          '--gs-inner-radius': `${Math.max(3, radius - 4)}px`,
          '--gs-chip': `${S.chip}px`,
          '--gs-row': `${S.row}px`,
          '--gs-font': `${S.font}px`,
          '--gs-menu-w': `${menuWidth}px`,
          '--gs-pop': `${popDuration}ms`,
          '--gs-pop-out': `${popOut}ms`,
          '--gs-glide': `${glideDuration}ms`,
          '--gs-origin': origin,
          ...style,
        } as React.CSSProperties
      }
      onAnimationEnd={(e) => {
        if (e.animationName === 'gs-swap' && rootRef.current)
          delete rootRef.current.dataset.swap;
      }}
    >
      <style>{STYLE}</style>
      <button
        ref={triggerRef}
        type="button"
        role="combobox"
        aria-haspopup="listbox"
        aria-expanded={phase === 'open'}
        aria-controls={`${id}-list`}
        aria-activedescendant={active !== null ? `${id}-${active}` : undefined}
        aria-label={ariaLabel}
        disabled={disabled}
        className="gs-trigger"
        onPointerDown={(e) => {
          if (e.button !== 0 || disabled) return;
          e.currentTarget.focus({ preventScroll: true });
          if (phase === 'open') close('pop');
          else open(false);
        }}
        onKeyDown={onTriggerKey}
      >
        <span
          className="gs-label-wrap"
          key={current}
          data-empty={selected < 0 ? '' : undefined}
        >
          {selected >= 0 ? items[selected].label : placeholder}
        </span>
        <span className="gs-chevron" aria-hidden="true">
          <HugeiconsIcon icon={ArrowDown01Icon} size={12} strokeWidth={2.5} />
        </span>
      </button>

      {phase !== 'closed' ? (
        <div
          style={{
            position: 'absolute',
            zIndex: 60,
            display: 'flex',
            alignItems: 'flex-start',
            gap: 10,
            bottom: side === 'top' ? 'calc(100% + 6px)' : 'auto',
            top: side === 'bottom' ? 'calc(100% + 6px)' : 'auto',
            left: align === 'left' ? 0 : 'auto',
            right: align === 'right' ? 0 : 'auto',
          }}
        >
          <div
            ref={menuRef}
            className="gs-menu"
            data-state="open"
            data-side={side}
            data-align={align}
            style={{
              position: 'relative',
              top: 'auto',
              bottom: 'auto',
              left: 'auto',
              right: 'auto',
            }}
          >
            <div
              id={`${id}-list`}
              role="listbox"
              aria-label={ariaLabel}
              className="gs-list"
              data-live={active !== null ? '' : undefined}
              onPointerOver={onListOver}
              onPointerLeave={() => {
                if (!scrub.current && !rememberPosition) setActive(null);
              }}
              onPointerDown={onListDown}
              onPointerMove={onListMove}
              onPointerUp={onListUp}
              onPointerCancel={onListUp}
            >
              <span ref={pillRef} className="gs-pill" aria-hidden="true" />
              {items.map((it, i) => (
                <div
                  key={it.value}
                  id={`${id}-${i}`}
                  role="option"
                  aria-selected={i === selected}
                  data-index={i}
                  className="gs-row"
                >
                  <span className="gs-row-label">{it.label}</span>
                  {showTags && it.tag ? (
                    <span className="gs-row-tag">{it.tag}</span>
                  ) : null}
                  <span
                    className="gs-row-check"
                    data-on={i === selected ? '' : undefined}
                    aria-hidden="true"
                  >
                    <HugeiconsIcon icon={Tick02Icon} size={13} strokeWidth={2.5} />
                  </span>
                </div>
              ))}
            </div>
          </div>

          {renderSidePanel?.(
            active !== null ? items[active] : selected >= 0 ? items[selected] : items[0]
          )}
        </div>
      ) : null}
    </div>
  );
}
