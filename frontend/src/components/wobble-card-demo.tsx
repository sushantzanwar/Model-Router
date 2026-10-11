"use client";

import { WobbleCard } from "@/components/ui/wobble-card";

export default function WobbleCardDemo() {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', width: '100%' }}>
      <WobbleCard containerClassName="bg-pink-800 min-h-[220px]">
        <div style={{ padding: '24px' }}>
          <h2 style={{ fontSize: '18px', fontWeight: 600, color: '#fff' }}>
            Telemetry & Intelligence
          </h2>
          <p style={{ marginTop: '8px', fontSize: '13px', color: '#e5e7eb' }}>
            Autonomous routing statistics dynamically evaluating prompt complexity and model performance.
          </p>
        </div>
      </WobbleCard>
      <WobbleCard containerClassName="bg-indigo-900 min-h-[220px]">
        <div style={{ padding: '24px' }}>
          <h2 style={{ fontSize: '18px', fontWeight: 600, color: '#fff' }}>
            Performance Metrics
          </h2>
          <p style={{ marginTop: '8px', fontSize: '13px', color: '#e5e7eb' }}>
            Live latency distribution, token throughput, and success rate analytics.
          </p>
        </div>
      </WobbleCard>
    </div>
  );
}
