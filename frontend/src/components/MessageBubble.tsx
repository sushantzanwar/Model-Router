import React, { useState } from 'react';
import type { ChatMessage } from '../types';

interface Props {
  message: ChatMessage;
}

export default function MessageBubble({ message }: Props) {
  const { role, content, modelName, latencyMs, timestamp } = message;
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(content);
      } else {
        const textarea = document.createElement('textarea');
        textarea.value = content;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch (err) {
      console.warn('Copy failed:', err);
    }
  };

  const isUser = role === 'user';
  const isError = role === 'error';

  const timeStr = timestamp.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });

  if (isError) {
    return (
      <div style={styles.errorWrapper}>
        <div style={styles.errorCard}>
          <div style={styles.errorIcon}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          </div>
          <div>
            <p style={styles.errorTitle}>Routing Failed</p>
            <p style={styles.errorMsg}>{content}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        ...styles.row,
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        alignItems: 'center',
        animation: 'fadeSlideUp 0.3s ease',
      }}
    >
      {!isUser && (
        <div style={styles.aiAvatar}>
          <AiSparkIcon />
        </div>
      )}

      <div style={styles.bubbleGroup}>
        {/* AI model label */}
        {!isUser && modelName && (
          <p style={styles.modelLabel}>
            <span style={styles.modelLabelDot} />
            {modelName}
            {latencyMs !== undefined && (
              <span style={styles.latencyTag}>{latencyMs}ms</span>
            )}
          </p>
        )}

        <div
          style={{
            ...styles.bubble,
            ...(isUser ? styles.userBubble : styles.aiBubble),
          }}
        >
          <p style={{ ...styles.text, ...(isUser ? styles.userText : styles.aiText) }}>
            {content}
          </p>
        </div>

        {/* Footer row: copy button & timestamp */}
        <div
          style={{
            ...styles.footerRow,
            justifyContent: isUser ? 'flex-end' : 'flex-start',
            flexDirection: isUser ? 'row-reverse' : 'row',
          }}
        >
          <button
            type="button"
            className="msg-copy-btn"
            style={{
              ...styles.copyBtn,
              ...(copied ? styles.copyBtnSuccess : {}),
            }}
            onClick={handleCopy}
            title={copied ? 'Copied to clipboard!' : 'Copy to clipboard'}
            aria-label="Copy text"
          >
            {copied ? (
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            ) : (
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
              </svg>
            )}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>

          <span style={styles.time}>{timeStr}</span>
        </div>
      </div>

      {isUser && (
        <div style={styles.userAvatar}>
          <UserIcon />
        </div>
      )}
    </div>
  );
}

function AiSparkIcon() {
  return (
    <img
      src="/logo-icon.png"
      alt="Invaders 4.0"
      style={{
        width: 18,
        height: 18,
        objectFit: 'contain',
        display: 'block',
      }}
    />
  );
}

function UserIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.6)" strokeWidth="2" strokeLinecap="round">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  );
}

const styles: Record<string, React.CSSProperties> = {
  row: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    padding: '6px 28px',
    maxWidth: '100%',
  },
  aiAvatar: {
    width: 32,
    height: 32,
    borderRadius: '50%',
    background: '#18191c',
    border: '1px solid rgba(255, 255, 255, 0.15)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    alignSelf: 'center',
    boxShadow: '0 2px 10px rgba(0, 0, 0, 0.35)',
    overflow: 'hidden',
  },
  userAvatar: {
    width: 30,
    height: 30,
    borderRadius: '50%',
    background: 'rgba(96,165,250,0.15)',
    border: '1px solid rgba(96,165,250,0.25)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  bubbleGroup: {
    display: 'flex',
    flexDirection: 'column',
    maxWidth: 'min(560px, 75%)',
  },
  modelLabel: {
    fontSize: 11,
    color: '#818cf8',
    marginBottom: 5,
    paddingLeft: 4,
    fontWeight: 500,
    display: 'flex',
    alignItems: 'center',
    gap: 6,
  },
  modelLabelDot: {
    width: 5,
    height: 5,
    borderRadius: '50%',
    background: '#818cf8',
    display: 'inline-block',
  },
  latencyTag: {
    fontSize: 10,
    color: '#6b7280',
    background: 'rgba(255,255,255,0.05)',
    padding: '1px 6px',
    borderRadius: 6,
    fontFamily: 'monospace',
  },
  bubble: {
    borderRadius: 20,
    padding: '12px 18px',
    wordBreak: 'break-word',
    lineHeight: 1.65,
    maxWidth: '100%',
  },
  userBubble: {
    background: 'rgba(30,58,95,0.8)',
    border: '1px solid rgba(96,165,250,0.2)',
    borderBottomRightRadius: 6,
    backdropFilter: 'blur(8px)',
    WebkitBackdropFilter: 'blur(8px)',
  },
  aiBubble: {
    background: 'rgba(40,42,44,0.7)',
    border: '1px solid rgba(255,255,255,0.07)',
    borderBottomLeftRadius: 6,
    backdropFilter: 'blur(8px)',
    WebkitBackdropFilter: 'blur(8px)',
  },
  text: {
    fontSize: 14,
    whiteSpace: 'pre-wrap',
    margin: 0,
  },
  userText: {
    color: '#e8f0fe',
  },
  aiText: {
    color: '#e3e3e3',
  },
  footerRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    marginTop: 4,
    paddingLeft: 4,
    paddingRight: 4,
  },
  copyBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 4,
    background: 'transparent',
    border: 'none',
    color: '#9aa0a6',
    cursor: 'pointer',
    fontSize: 11,
    padding: '2px 6px',
    borderRadius: 6,
    transition: 'all 0.15s ease',
    opacity: 0.75,
  },
  copyBtnSuccess: {
    color: 'var(--green)',
    opacity: 1,
  },
  time: {
    fontSize: 10,
    color: 'rgba(255,255,255,0.3)',
  },
  errorWrapper: {
    padding: '6px 28px',
  },
  errorCard: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: 12,
    background: 'rgba(248,113,113,0.08)',
    border: '1px solid rgba(248,113,113,0.2)',
    borderLeft: '3px solid #f87171',
    borderRadius: 12,
    padding: '12px 16px',
  },
  errorIcon: {
    color: '#f87171',
    flexShrink: 0,
    marginTop: 1,
    display: 'flex',
  },
  errorTitle: {
    fontSize: 12,
    fontWeight: 700,
    color: '#f87171',
    letterSpacing: '0.03em',
    marginBottom: 4,
  },
  errorMsg: {
    fontSize: 13,
    color: '#fca5a5',
    lineHeight: 1.5,
  },
};
