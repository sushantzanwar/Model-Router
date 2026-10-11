import React, { useState, useEffect, useCallback, useRef } from 'react';
import type { ModelInfo, Decision } from './types';
import { fetchModels } from './api';
import ChatPanel from './components/ChatPanel';
import InspectorPanel from './components/InspectorPanel';
import Sidebar from './components/Sidebar';
import GradientWaves from './components/GradientWaves';
import DetailedAnalysisPage from './components/DetailedAnalysisPage';
import './styles/global.css';

const POLL_INTERVAL_MS = 6000;
const DEFAULT_INSPECTOR_WIDTH = 390;
const MIN_INSPECTOR_WIDTH = 290;
const MAX_INSPECTOR_WIDTH = 680;

export default function App() {
  const [currentPage, setCurrentPage] = useState<'chat' | 'analysis'>('chat');
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [lastDecision, setLastDecision] = useState<Decision | null>(null);
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const [inspectorWidth, setInspectorWidth] = useState(DEFAULT_INSPECTOR_WIDTH);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [chatKey, setChatKey] = useState(0);

  const isDraggingRef = useRef(false);

  const loadModels = useCallback(() => {
    fetchModels()
      .then(setModels)
      .catch((err) => {
        console.warn('Backend not responding yet:', err);
      });
  }, []);

  useEffect(() => {
    loadModels();
    const id = setInterval(loadModels, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [loadModels]);

  const handleDecision = useCallback(
    (decision: Decision) => {
      setLastDecision(decision);
      loadModels();
    },
    [loadModels]
  );

  const handleNewChat = useCallback(() => {
    setChatKey((k) => k + 1);
    setLastDecision(null);
  }, []);

  // Draggable slider bar to resize analysis tab width
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    isDraggingRef.current = true;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    e.preventDefault();
  }, []);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDraggingRef.current) return;
      const newWidth = window.innerWidth - e.clientX;
      if (newWidth >= MIN_INSPECTOR_WIDTH && newWidth <= MAX_INSPECTOR_WIDTH) {
        setInspectorWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      if (isDraggingRef.current) {
        isDraggingRef.current = false;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);

  if (currentPage === 'analysis') {
    return (
      <DetailedAnalysisPage
        models={models}
        onBack={() => setCurrentPage('chat')}
      />
    );
  }

  return (
    <div style={styles.root}>
      {/* Background Gradient Waves from React Bits */}
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

      {/* Sidebar Drawer */}
      <Sidebar
        models={models}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onNewChat={handleNewChat}
        onOpenDetailedAnalysis={() => setCurrentPage('analysis')}
      />

      {/* Main Layout */}
      <div style={styles.layout}>
        {/* Chat Panel */}
        <div style={styles.chatPane}>
          <ChatPanel
            key={chatKey}
            models={models}
            onModelsChange={setModels}
            onDecision={handleDecision}
            inspectorOpen={inspectorOpen}
            onToggleInspector={() => setInspectorOpen((v) => !v)}
            onOpenSidebar={() => setSidebarOpen(true)}
            onResetChat={handleNewChat}
          />
        </div>

        {/* Draggable Slider Bar (Resizer Handle for Analysis Tab) */}
        {inspectorOpen && (
          <div
            style={styles.sliderResizer}
            onMouseDown={handleMouseDown}
            onDoubleClick={() => setInspectorWidth(DEFAULT_INSPECTOR_WIDTH)}
            title="Drag slider bar to resize analysis tab (Double-click to reset)"
          >
            <div style={styles.sliderGripLine} />
          </div>
        )}

        {/* Inspector / Analysis Panel */}
        <div
          style={{
            ...styles.inspectorPane,
            width: inspectorOpen ? `${inspectorWidth}px` : '0px',
            overflow: inspectorOpen ? 'visible' : 'hidden',
            opacity: inspectorOpen ? 1 : 0,
            transition: isDraggingRef.current ? 'none' : 'width 0.18s ease, opacity 0.15s ease',
          }}
        >
          <InspectorPanel
            models={models}
            lastDecision={lastDecision}
            onOpenDetailedAnalysis={() => setCurrentPage('analysis')}
          />
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  root: {
    display: 'flex',
    height: '100vh',
    width: '100vw',
    overflow: 'hidden',
    position: 'relative',
    background: '#0b0c10',
  },
  wavesBg: {
    position: 'absolute',
    inset: 0,
    width: '100%',
    height: '100%',
    zIndex: 0,
    pointerEvents: 'none',
  },
  layout: {
    display: 'flex',
    flex: 1,
    height: '100%',
    overflow: 'hidden',
    position: 'relative',
    zIndex: 1,
  },
  chatPane: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    minWidth: 0,
    position: 'relative',
    background: 'transparent',
  },
  sliderResizer: {
    width: '6px',
    cursor: 'col-resize',
    background: 'rgba(255, 255, 255, 0.04)',
    borderLeft: '1px solid rgba(255, 255, 255, 0.08)',
    borderRight: '1px solid rgba(255, 255, 255, 0.08)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'background 0.15s ease',
    zIndex: 20,
    flexShrink: 0,
  },
  sliderGripLine: {
    width: '2px',
    height: '28px',
    borderRadius: '1px',
    background: 'rgba(255, 255, 255, 0.25)',
  },
  inspectorPane: {
    height: '100%',
    minHeight: 0,
    flexShrink: 0,
  },
};
