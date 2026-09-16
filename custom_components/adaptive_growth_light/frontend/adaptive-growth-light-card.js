/**
 * Adaptive Growth Light Card for Home Assistant Lovelace
 * Author: @kujbol
 * Version: 1.1.7
 */

const CARD_VERSION = "1.1.7";

console.info(
  `%c ADAPTIVE-GROWTH-LIGHT-CARD %c v${CARD_VERSION} `,
  "color: white; background: #059669; font-weight: 700; border-radius: 3px 0 0 3px;",
  "color: #10b981; background: #1f2937; font-weight: 700; border-radius: 0 3px 3px 0;"
);

// ---------------------------------------------------------------------------
// 1. STYLES
// ---------------------------------------------------------------------------
const CARD_STYLES = `
  :host {
    display: block;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    color: #f3f4f6;
  }

  /* Compact Tile View */
  .compact-tile {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    min-height: 74px;
    box-sizing: border-box;
    border-radius: 16px;
    background: linear-gradient(135deg, rgba(20, 29, 25, 0.95) 0%, rgba(13, 20, 18, 0.98) 100%);
    border: 1px solid rgba(52, 211, 153, 0.2);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35);
    cursor: pointer;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    user-select: none;
    gap: 14px;
  }
  .compact-tile:hover {
    border-color: rgba(52, 211, 153, 0.45);
    box-shadow: 0 8px 28px rgba(0, 0, 0, 0.45), 0 0 16px rgba(16, 185, 129, 0.12);
    transform: translateY(-1px);
  }

  .tile-left {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;
    min-width: 0;
  }
  .tile-icon-wrap {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(52, 211, 153, 0.25);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    color: #34d399;
    transition: all 0.3s ease;
  }
  .tile-icon-wrap.active {
    box-shadow: 0 0 14px rgba(52, 211, 153, 0.5);
    border-color: rgba(52, 211, 153, 0.6);
    color: #10b981;
  }
  .tile-icon-wrap svg {
    width: 24px;
    height: 24px;
    fill: currentColor;
  }
  .tile-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
  }
  .tile-title {
    font-size: 15px;
    font-weight: 600;
    color: #f8fafc;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .tile-status-row {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .tile-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;
  }
  .tile-next {
    color: #9ca3af;
    font-size: 11px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .tile-stats-row {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    font-weight: 500;
    color: #94a3b8;
    margin-top: 1px;
  }
  .stat-sun { color: #f59e0b; }
  .stat-supp { color: #10b981; }
  .stat-target { color: #f1f5f9; font-weight: 600; }

  .tile-right {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
  }
  .tile-chevron {
    color: #64748b;
    display: flex;
    align-items: center;
    transition: all 0.2s;
  }
  .compact-tile:hover .tile-chevron {
    color: #34d399;
    transform: translateX(2px);
  }

  /* Toggle Switch */
  .toggle-switch {
    position: relative;
    display: inline-block;
    width: 44px;
    height: 24px;
    cursor: pointer;
  }
  .toggle-switch input {
    opacity: 0;
    width: 0;
    height: 0;
  }
  .slider {
    position: absolute;
    cursor: pointer;
    top: 0; left: 0; right: 0; bottom: 0;
    background-color: #374151;
    border: 1px solid rgba(255,255,255,0.1);
    transition: .3s cubic-bezier(0.4, 0, 0.2, 1);
    border-radius: 24px;
  }
  .slider:before {
    position: absolute;
    content: "";
    height: 18px;
    width: 18px;
    left: 2px;
    bottom: 2px;
    background-color: white;
    transition: .3s cubic-bezier(0.4, 0, 0.2, 1);
    border-radius: 50%;
    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
  }
  input:checked + .slider {
    background-color: #059669;
    box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
  }
  input:checked + .slider:before {
    transform: translateX(20px);
  }

  /* Modal Popup Dialog */
  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.78);
    backdrop-filter: blur(10px);
    z-index: 99999;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 16px;
    box-sizing: border-box;
    animation: fadeIn 0.2s ease-out;
  }
  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
  .modal-dialog {
    background: linear-gradient(135deg, rgba(20, 29, 25, 0.98) 0%, rgba(13, 20, 18, 0.99) 100%);
    border: 1px solid rgba(52, 211, 153, 0.3);
    border-radius: 20px;
    box-shadow: 0 25px 60px rgba(0, 0, 0, 0.75), 0 0 30px rgba(16, 185, 129, 0.15);
    width: 100%;
    max-width: 520px;
    max-height: 90vh;
    overflow-y: auto;
    padding: 22px;
    box-sizing: border-box;
    position: relative;
    animation: scaleUp 0.22s cubic-bezier(0.16, 1, 0.3, 1);
  }
  @keyframes scaleUp {
    from { opacity: 0; transform: scale(0.95); }
    to { opacity: 1; transform: scale(1); }
  }
  .modal-close-btn {
    position: absolute;
    top: 16px;
    right: 16px;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: #94a3b8;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-size: 16px;
    transition: all 0.2s;
  }
  .modal-close-btn:hover {
    background: rgba(239, 68, 68, 0.2);
    color: #f87171;
    border-color: rgba(239, 68, 68, 0.4);
  }

  /* Permanently Expanded Card */
  .expanded-card {
    background: linear-gradient(135deg, rgba(20, 29, 25, 0.95) 0%, rgba(13, 20, 18, 0.98) 100%);
    backdrop-filter: blur(16px);
    border-radius: 18px;
    border: 1px solid rgba(52, 211, 153, 0.18);
    box-shadow: 0 12px 36px rgba(0, 0, 0, 0.45);
    padding: 18px;
  }

  /* Header & Details */
  .details-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
  }
  .header-title-area {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .plant-icon-wrap {
    width: 42px;
    height: 42px;
    border-radius: 12px;
    background: rgba(16, 185, 129, 0.14);
    border: 1px solid rgba(52, 211, 153, 0.25);
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .plant-icon-wrap.active {
    box-shadow: 0 0 16px rgba(52, 211, 153, 0.6);
    border-color: rgba(52, 211, 153, 0.7);
  }
  .plant-icon-wrap svg {
    width: 22px;
    height: 22px;
    fill: #34d399;
  }
  .card-title {
    font-size: 17px;
    font-weight: 700;
    color: #f9fafb;
  }
  .card-subtitle {
    font-size: 11px;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-top: 1px;
  }

  /* Status Banner */
  .status-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.04);
    margin-bottom: 14px;
  }
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 20px;
  }
  .badge-active-morn, .badge-active-eve {
    background: rgba(16, 185, 129, 0.2);
    color: #34d399;
    border: 1px solid rgba(52, 211, 153, 0.4);
  }
  .badge-daylight {
    background: rgba(245, 158, 11, 0.2);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.4);
  }
  .badge-idle {
    background: rgba(107, 114, 128, 0.2);
    color: #9ca3af;
    border: 1px solid rgba(156, 163, 175, 0.3);
  }
  .badge-disabled {
    background: rgba(239, 68, 68, 0.2);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.3);
  }
  .next-session-text {
    font-size: 12px;
    color: #9ca3af;
    display: flex;
    align-items: center;
    gap: 4px;
  }

  /* Day Timeline */
  .day-timeline-card {
    background: rgba(0, 0, 0, 0.25);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 12px;
    margin-bottom: 14px;
  }
  .timeline-title-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }
  .timeline-title {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #9ca3af;
  }
  .earliest-badge {
    font-size: 11px;
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid rgba(52, 211, 153, 0.3);
    border-radius: 6px;
    padding: 2px 8px;
  }
  .timeline-legend {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-top: 8px;
    font-size: 10px;
    color: #9ca3af;
  }
  .legend-item {
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }
  .sun-dot { background: #f59e0b; }
  .plant-dot { background: #10b981; }
  .overlap-dot {
    background: repeating-linear-gradient(45deg, #f59e0b, #f59e0b 2px, #10b981 2px, #10b981 4px);
  }
  .cutoff-dot { background: rgba(239, 68, 68, 0.8); }

  /* Metrics 3-Grid */
  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-bottom: 14px;
  }
  .metric-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 12px;
    padding: 10px 8px;
    text-align: center;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }
  .metric-card.highlight {
    border-color: rgba(52, 211, 153, 0.3);
    background: rgba(16, 185, 129, 0.05);
  }
  .metric-card.sun {
    border-color: rgba(245, 158, 11, 0.3);
    background: rgba(245, 158, 11, 0.05);
  }
  .metric-label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: #9ca3af;
  }
  .metric-value {
    font-size: 18px;
    font-weight: 700;
    color: #f3f4f6;
  }
  .metric-card.highlight .metric-value { color: #10b981; }
  .metric-card.sun .metric-value { color: #f59e0b; }

  /* Controls Panel */
  .controls-panel {
    display: flex;
    flex-direction: column;
    gap: 12px;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    padding-top: 14px;
    margin-top: 6px;
  }
  .control-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .control-label-row {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    font-weight: 500;
    color: #d1d5db;
  }
  .control-value {
    color: #34d399;
    font-weight: 600;
  }
  input[type=range] {
    -webkit-appearance: none;
    width: 100%;
    background: transparent;
  }
  input[type=range]:focus {
    outline: none;
  }
  input[type=range]::-webkit-slider-runnable-track {
    width: 100%;
    height: 6px;
    cursor: pointer;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
  }
  input[type=range]::-webkit-slider-thumb {
    height: 18px;
    width: 18px;
    border-radius: 50%;
    background: #10b981;
    cursor: pointer;
    -webkit-appearance: none;
    margin-top: -6px;
    box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
  }
  .mode-btn-group {
    display: flex;
    gap: 6px;
  }
  .mode-btn {
    flex: 1;
    padding: 7px 6px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    color: #9ca3af;
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }
  .mode-btn.active {
    background: rgba(16, 185, 129, 0.2);
    border-color: #10b981;
    color: #34d399;
  }
  .cutoff-row {
    display: flex;
    gap: 12px;
  }
  .cutoff-group {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .cutoff-group label {
    font-size: 10px;
    color: #9ca3af;
  }
  .cutoff-group input[type=time] {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    color: #f3f4f6;
    padding: 6px 8px;
    font-size: 12px;
    outline: none;
  }

  /* Seasonal Chart */
  .seasonal-chart-card {
    background: rgba(0, 0, 0, 0.25);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 10px;
  }
  .seasonal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }
  .seasonal-title {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: #9ca3af;
  }
  .seasonal-legend {
    display: flex;
    gap: 8px;
    font-size: 9px;
    color: #9ca3af;
  }
  .target-override-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 6px;
    padding-top: 10px;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
  }
  .target-override-text {
    font-size: 11px;
    color: #9ca3af;
  }
  .manual-btn {
    padding: 6px 12px;
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(52, 211, 153, 0.3);
    border-radius: 8px;
    color: #34d399;
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
  }
  .manual-btn:hover {
    background: rgba(16, 185, 129, 0.25);
  }
`;

// ---------------------------------------------------------------------------
// 2. HELPER FUNCTIONS
// ---------------------------------------------------------------------------
function parseTimeStr(tStr) {
  if (!tStr) return null;
  const parts = tStr.split(":");
  if (parts.length < 2) return null;
  return parseInt(parts[0], 10) + parseInt(parts[1], 10) / 60.0;
}

function parseIsoHour(iso) {
  if (!iso) return null;
  const d = new Date(iso);
  if (isNaN(d.getTime())) return null;
  return d.getHours() + d.getMinutes() / 60.0;
}

function getStatusBadge(status, isEnabled) {
  if (!isEnabled) {
    return {
      label: "Disabled",
      class: "badge-disabled",
      icon: "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z",
    };
  }
  switch (status) {
    case "supplementing_morning":
      return {
        label: "Active: Morning Supplement",
        class: "badge-active-morn",
        icon: "M12 7c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5-2.24-5-5-5zm0 8c-1.65 0-3-1.35-3-3s1.35-3 3-3 3 1.35 3 3-1.35 3-3 3z",
      };
    case "supplementing_evening":
      return {
        label: "Active: Evening Supplement",
        class: "badge-active-eve",
        icon: "M12 3a9 9 0 109 9c0-.46-.04-.92-.1-1.36a5.389 5.389 0 01-4.4 2.26 5.403 5.403 0 01-3.14-9.8c-.44-.06-.9-.1-1.36-.1z",
      };
    case "daylight_active":
      return {
        label: "Daylight Active",
        class: "badge-daylight",
        icon: "M12 7c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5-2.24-5-5-5zM2 13h2c.55 0 1-.45 1-1s-.45-1-1-1H2c-.55 0-1 .45-1 1s.45 1 1 1zm18 0h2c.55 0 1-.45 1-1s-.45-1-1-1h-2c-.55 0-1 .45-1 1s.45 1 1 1zM11 2v2c0 .55.45 1 1 1s1-.45 1-1V2c0-.55-.45-1-1-1s-1 .45-1 1zm0 18v2c0 .55.45 1 1 1s1-.45 1-1v-2c0-.55-.45-1-1-1s-1 .45-1 1z",
      };
    case "night_idle":
    default:
      return {
        label: "Idle (Night)",
        class: "badge-idle",
        icon: "M12 2a10 10 0 1010 10A10 10 0 0012 2zm1 17.93V18c0-.55-.45-1-1-1s-1 .45-1 1v1.93A8.001 8.001 0 014.07 13H6c.55 0 1-.45 1-1s-.45-1-1-1H4.07A8.001 8.001 0 0111 4.07V6c0 .55.45 1 1 1s1-.45 1-1V4.07A8.001 8.001 0 0119.93 11H18c-.55 0-1 .45-1 1s.45 1 1 1h1.93A8.001 8.001 0 0113 19.93z",
      };
  }
}

// ---------------------------------------------------------------------------
// 3. SVG RENDERERS (Timeline & Seasonal Matrix)
// ---------------------------------------------------------------------------
function renderDayTimeline(options) {
  const {
    sunriseStr,
    sunsetStr,
    mornStartStr,
    mornEndStr,
    eveStartStr,
    eveEndStr,
    lightingMode = "both",
    earliestCutoffStr,
    latestCutoffStr,
    earliestEff = "--:--",
  } = options;

  const sunriseH = parseIsoHour(sunriseStr) ?? 6.2;
  const sunsetH = parseIsoHour(sunsetStr) ?? 18.8;

  const mornStartH = parseTimeStr(mornStartStr);
  const mornEndH = parseTimeStr(mornEndStr);

  const eveStartH = parseTimeStr(eveStartStr);
  const eveEndH = parseTimeStr(eveEndStr);

  const earliestCutoffH = parseTimeStr(earliestCutoffStr);
  const latestCutoffH = parseTimeStr(latestCutoffStr);

  const now = new Date();
  const nowH = now.getHours() + now.getMinutes() / 60.0;

  const width = 460;
  const height = 48;
  const barY = 16;
  const barH = 14;
  const scaleX = (h) => Math.max(0, Math.min(width, (h / 24.0) * width));

  // Time markers
  let markersSvg = "";
  [0, 3, 6, 9, 12, 15, 18, 21, 24].forEach((h) => {
    const x = scaleX(h);
    markersSvg += `
      <line x1="${x}" y1="2" x2="${x}" y2="12" stroke="rgba(255,255,255,0.12)" stroke-width="1" />
      <text x="${x}" y="10" font-size="8" fill="#9ca3af" text-anchor="${h === 0 ? "start" : h === 24 ? "end" : "middle"}">${String(h).padStart(2, "0")}:00</text>
    `;
  });

  let rectsSvg = "";
  // 1. Dark night background (24h)
  rectsSvg += `<rect x="0" y="${barY}" width="${width}" height="${barH}" rx="4" fill="rgba(255,255,255,0.06)" />`;

  // 2. Suppressed morning cut-off zone (red overlay)
  if (earliestCutoffH && earliestCutoffH > 0) {
    const cutX = scaleX(earliestCutoffH);
    rectsSvg += `<rect x="0" y="${barY}" width="${cutX}" height="${barH}" rx="4" fill="rgba(239, 68, 68, 0.18)" stroke="rgba(239, 68, 68, 0.35)" stroke-dasharray="2,2" stroke-width="1" />`;
  }

  // 3. Suppressed evening cut-off zone (red overlay)
  if (latestCutoffH && latestCutoffH < 24) {
    const cutX = scaleX(latestCutoffH);
    rectsSvg += `<rect x="${cutX}" y="${barY}" width="${width - cutX}" height="${barH}" rx="4" fill="rgba(239, 68, 68, 0.18)" stroke="rgba(239, 68, 68, 0.35)" stroke-dasharray="2,2" stroke-width="1" />`;
  }

  // 4. Pure Natural Daylight Bar (Amber)
  const sunStartX = scaleX(sunriseH);
  const sunEndX = scaleX(sunsetH);
  rectsSvg += `<rect x="${sunStartX}" y="${barY}" width="${Math.max(2, sunEndX - sunStartX)}" height="${barH}" fill="#f59e0b" rx="2" opacity="0.95" />`;

  // 5. Morning Session (Green pre-sunrise + Striped overlap)
  if (mornStartH !== null && mornEndH !== null && mornEndH > mornStartH) {
    const sX = scaleX(mornStartH);
    const sunX = scaleX(sunriseH);
    const eX = scaleX(mornEndH);

    // Dark pre-sunrise portion (Emerald Green)
    if (mornStartH < sunriseH) {
      const darkEndX = Math.min(eX, sunX);
      rectsSvg += `<rect x="${sX}" y="${barY}" width="${Math.max(2, darkEndX - sX)}" height="${barH}" fill="#10b981" rx="2" opacity="0.95" />`;
    }

    // Daylight Overlap portion (Striped Amber + Emerald)
    if (mornEndH > sunriseH) {
      const overlapStartX = Math.max(sX, sunX);
      const overlapEndX = eX;
      if (overlapEndX > overlapStartX) {
        rectsSvg += `<rect x="${overlapStartX}" y="${barY}" width="${Math.max(2, overlapEndX - overlapStartX)}" height="${barH}" fill="url(#overlap-hatch)" rx="2" opacity="0.95" />`;
      }
    }
  }

  // 6. Evening Session (Striped overlap + Green post-sunset)
  if (eveStartH !== null && eveEndH !== null && eveEndH > eveStartH) {
    const sX = scaleX(eveStartH);
    const setX = scaleX(sunsetH);
    const maxLimit = latestCutoffH && latestCutoffH < eveEndH ? latestCutoffH : eveEndH;
    const eX = scaleX(maxLimit);

    // Daylight Overlap portion (Striped Amber + Emerald)
    if (eveStartH < sunsetH) {
      const overlapStartX = sX;
      const overlapEndX = Math.min(eX, setX);
      if (overlapEndX > overlapStartX) {
        rectsSvg += `<rect x="${overlapStartX}" y="${barY}" width="${Math.max(2, overlapEndX - overlapStartX)}" height="${barH}" fill="url(#overlap-hatch)" rx="2" opacity="0.95" />`;
      }
    }

    // Dark post-sunset portion (Emerald Green)
    if (maxLimit > sunsetH) {
      const darkStartX = Math.max(sX, setX);
      if (eX > darkStartX) {
        rectsSvg += `<rect x="${darkStartX}" y="${barY}" width="${Math.max(2, eX - darkStartX)}" height="${barH}" fill="#10b981" rx="2" opacity="0.95" />`;
      }
    }
  }

  // 7. Realtime "Now" Pointer (Cyan Needle)
  const nowX = scaleX(nowH);
  const nowSvg = `
    <line x1="${nowX}" y1="${barY - 3}" x2="${nowX}" y2="${barY + barH + 3}" stroke="#38bdf8" stroke-width="2" />
    <polygon points="${nowX - 3},${barY - 4} ${nowX + 3},${barY - 4} ${nowX},${barY}" fill="#38bdf8" />
  `;

  const sunriseLabel = sunriseStr
    ? new Date(sunriseStr).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : "06:12";
  const sunsetLabel = sunsetStr
    ? new Date(sunsetStr).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : "18:48";

  return `
    <div class="day-timeline-card">
      <div class="timeline-title-row">
        <span class="timeline-title">24h Schedule Timeline</span>
        <span class="earliest-badge">Earliest Turn-On: <strong>${earliestEff}</strong></span>
      </div>
      <svg viewBox="0 0 ${width} ${height}" class="timeline-svg" style="width: 100%; height: auto; display: block;">
        <defs>
          <pattern id="overlap-hatch" width="8" height="8" patternTransform="rotate(45)" patternUnits="userSpaceOnUse">
            <rect width="8" height="8" fill="#f59e0b" />
            <line x1="0" y1="0" x2="0" y2="8" stroke="#10b981" stroke-width="4" />
          </pattern>
        </defs>
        ${markersSvg}
        ${rectsSvg}
        ${nowSvg}
      </svg>
      <div class="timeline-legend">
        <span class="legend-item"><span class="dot sun-dot"></span>Sunlight (${sunriseLabel} - ${sunsetLabel})</span>
        <span class="legend-item"><span class="dot plant-dot"></span>Grow Light</span>
        <span class="legend-item"><span class="dot overlap-dot"></span>Daylight Overlap</span>
        <span class="legend-item"><span class="dot cutoff-dot"></span>Cut-Off Restricted</span>
      </div>
    </div>
  `;
}

function renderSeasonalChart(seasonalMonths, currentTarget) {
  if (!seasonalMonths || !seasonalMonths.length) {
    return `<div style="text-align: center; color: #9ca3af; font-size: 11px; padding: 12px;">No seasonal profile data available</div>`;
  }

  const currentMonthIdx = new Date().getMonth() + 1;
  const maxHourScale = 20.0;
  const chartHeight = 120;
  const chartWidth = 340;
  const barWidth = 18;
  const gap = (chartWidth - barWidth * 12) / 13;

  let barsSvg = "";
  seasonalMonths.forEach((m, idx) => {
    const x = gap + idx * (barWidth + gap);
    const natH = Math.min(maxHourScale, m.natural_hours || 0);
    const suppH = Math.min(maxHourScale - natH, m.supplementary_hours || 0);

    const natPixelH = (natH / maxHourScale) * (chartHeight - 20);
    const suppPixelH = (suppH / maxHourScale) * (chartHeight - 20);

    const natY = chartHeight - 20 - natPixelH;
    const suppY = natY - suppPixelH;
    const isCurrent = m.month === currentMonthIdx;

    barsSvg += `
      <rect x="${x}" y="${natY}" width="${barWidth}" height="${natPixelH}" fill="url(#sun-grad)" rx="2" opacity="${isCurrent ? "1.0" : "0.8"}" />
      ${suppPixelH > 0 ? `<rect x="${x}" y="${suppY}" width="${barWidth}" height="${suppPixelH}" fill="url(#plant-grad)" rx="2" opacity="${isCurrent ? "1.0" : "0.85"}" />` : ""}
      ${isCurrent ? `<rect x="${x - 1}" y="${suppPixelH > 0 ? suppY - 1 : natY - 1}" width="${barWidth + 2}" height="${natPixelH + suppPixelH + 2}" fill="none" stroke="#34d399" stroke-width="1.5" rx="3" />` : ""}
      <text x="${x + barWidth / 2}" y="${chartHeight - 6}" text-anchor="middle" font-size="8" fill="${isCurrent ? "#34d399" : "#9ca3af"}" font-weight="${isCurrent ? "700" : "500"}">
        ${m.month_name ? m.month_name.substring(0, 1) : m.month}
      </text>
    `;
  });

  const targetY = chartHeight - 20 - (currentTarget / maxHourScale) * (chartHeight - 20);

  return `
    <div class="seasonal-chart-card">
      <div class="seasonal-header">
        <span class="seasonal-title">Seasonal Daylight vs. Supplementary Matrix</span>
        <div class="seasonal-legend">
          <span class="legend-item"><span class="dot sun-dot"></span>Sun</span>
          <span class="legend-item"><span class="dot plant-dot"></span>Grow Light</span>
        </div>
      </div>
      <svg viewBox="0 0 ${chartWidth} ${chartHeight}" style="width: 100%; height: auto; display: block;">
        <defs>
          <linearGradient id="sun-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#fbbf24" />
            <stop offset="100%" stop-color="#d97706" />
          </linearGradient>
          <linearGradient id="plant-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#34d399" />
            <stop offset="100%" stop-color="#059669" />
          </linearGradient>
        </defs>
        <line x1="0" y1="${chartHeight - 20 - (8 / maxHourScale) * (chartHeight - 20)}" x2="${chartWidth}" y2="${chartHeight - 20 - (8 / maxHourScale) * (chartHeight - 20)}" stroke="rgba(255,255,255,0.06)" stroke-dasharray="3,3" />
        <line x1="0" y1="${chartHeight - 20 - (12 / maxHourScale) * (chartHeight - 20)}" x2="${chartWidth}" y2="${chartHeight - 20 - (12 / maxHourScale) * (chartHeight - 20)}" stroke="rgba(255,255,255,0.06)" stroke-dasharray="3,3" />
        <line x1="0" y1="${chartHeight - 20 - (16 / maxHourScale) * (chartHeight - 20)}" x2="${chartWidth}" y2="${chartHeight - 20 - (16 / maxHourScale) * (chartHeight - 20)}" stroke="rgba(255,255,255,0.06)" stroke-dasharray="3,3" />
        ${barsSvg}
        <line x1="0" y1="${targetY}" x2="${chartWidth}" y2="${targetY}" stroke="#38bdf8" stroke-width="1.5" stroke-dasharray="4,3" opacity="0.8" />
        <text x="${chartWidth - 2}" y="${targetY - 3}" text-anchor="end" font-size="8" fill="#38bdf8" font-weight="600">Target ${currentTarget}h</text>
      </svg>
    </div>
  `;
}

// ---------------------------------------------------------------------------
// 4. UNIFIED DETAILS PANEL (Used by both Modal Dialog and Expanded Card)
// ---------------------------------------------------------------------------
function renderDetailsPanel(d) {
  const sproutIcon = `M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17.93V18c0-.55-.45-1-1-1s-1 .45-1 1v1.93A8.001 8.001 0 014.07 13H6c.55 0 1-.45 1-1s-.45-1-1-1H4.07A8.001 8.001 0 0111 4.07V6c0 .55.45 1 1 1s1-.45 1-1V4.07A8.001 8.001 0 0119.93 11H18c-.55 0-1 .45-1 1s.45 1 1 1h1.93A8.001 8.001 0 0113 19.93z`;

  return `
    <div class="details-header" style="${d.isModal ? "padding-right: 36px;" : ""}">
      <div class="header-title-area">
        <div class="plant-icon-wrap ${d.isEnabled ? "active" : ""}">
          <svg viewBox="0 0 24 24"><path d="${sproutIcon}"/></svg>
        </div>
        <div>
          <div class="card-title">${d.friendlyName}</div>
          <div class="card-subtitle">${d.lightingMode.toUpperCase()} ROUTINE</div>
        </div>
      </div>
      <label class="toggle-switch" id="master-toggle-wrap">
        <input type="checkbox" id="master-toggle" ${d.isEnabled ? "checked" : ""}>
        <span class="slider"></span>
      </label>
    </div>

    <div class="status-bar">
      <div class="badge ${d.badge.class}">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="${d.badge.icon}"/></svg>
        <span>${d.badge.label}</span>
      </div>
      <div class="next-session-text">
        <span>⏰</span>
        <span>${d.nextSessionText}</span>
      </div>
    </div>

    ${renderDayTimeline({
      sunriseStr: d.sunriseStr,
      sunsetStr: d.sunsetStr,
      mornStartStr: d.mornStartStr,
      mornEndStr: d.mornEndStr,
      eveStartStr: d.eveStartStr,
      eveEndStr: d.eveEndStr,
      lightingMode: d.lightingMode,
      earliestCutoffStr: d.earliestStartVal,
      latestCutoffStr: d.latestEndVal,
      earliestEff: d.earliestEff,
    })}

    <div class="metrics-grid">
      <div class="metric-card highlight">
        <span class="metric-label">Supplement</span>
        <span class="metric-value">${d.suppHours}h</span>
      </div>
      <div class="metric-card sun">
        <span class="metric-label">Natural Sun</span>
        <span class="metric-value">${d.daylightHours}h</span>
      </div>
      <div class="metric-card">
        <span class="metric-label">Target</span>
        <span class="metric-value">${d.targetHours}h</span>
      </div>
    </div>

    <div class="controls-panel">
      <div class="control-group">
        <div class="control-label-row">
          <span>Target Photoperiod</span>
          <span class="control-value">${d.targetHours} hours / day</span>
        </div>
        <input type="range" id="target-slider" min="6" max="18" step="0.5" value="${d.targetHours}">
      </div>

      <div class="control-group">
        <div class="control-label-row">
          <span>Lighting Routine</span>
          <span class="control-value">${d.lightingMode.toUpperCase()}</span>
        </div>
        <div class="mode-btn-group">
          <button class="mode-btn ${d.lightingMode === "morning" ? "active" : ""}" data-mode="morning">Morning</button>
          <button class="mode-btn ${d.lightingMode === "evening" ? "active" : ""}" data-mode="evening">Evening</button>
          <button class="mode-btn ${d.lightingMode === "both" ? "active" : ""}" data-mode="both">Both (Split)</button>
        </div>
      </div>

      ${d.lightingMode === "both" ? `
        <div class="control-group">
          <div class="control-label-row">
            <span>Morning / Evening Ratio</span>
            <span class="control-value">${d.morningSplit}% Morning / ${100 - d.morningSplit}% Evening</span>
          </div>
          <input type="range" id="split-slider" min="0" max="100" step="5" value="${d.morningSplit}">
        </div>
      ` : ""}

      <div class="control-group">
        <div class="control-label-row">
          <span>Daylight Overlap Buffer</span>
          <span class="control-value">${d.daylightOverlap} hours</span>
        </div>
        <input type="range" id="overlap-slider" min="0" max="3" step="0.25" value="${d.daylightOverlap}">
      </div>

      <div class="control-group">
        <div class="control-label-row">
          <span>Sleep Protection Cut-Offs</span>
          <span class="control-value">${(d.earliestStartVal || d.latestEndVal) ? `${d.earliestStartVal || "No limit"} - ${d.latestEndVal || "No limit"}` : "None"}</span>
        </div>
        <div class="cutoff-row">
          <div class="cutoff-group">
            <label>Earliest Morning Start</label>
            <input type="time" id="earliest-start-input" value="${d.earliestStartVal}">
          </div>
          <div class="cutoff-group">
            <label>Latest Evening End</label>
            <input type="time" id="latest-end-input" value="${d.latestEndVal}">
          </div>
        </div>
      </div>

      ${renderSeasonalChart(d.seasonalMonths, d.targetHours)}

      ${d.targetEntityId ? `
        <div class="target-override-row">
          <span class="target-override-text">Target: <strong>${d.targetEntityId}</strong> ${d.targetState ? `(${d.targetState})` : ""}</span>
          <button class="manual-btn" id="manual-light-btn">Toggle Light</button>
        </div>
      ` : ""}
    </div>
  `;
}

// ---------------------------------------------------------------------------
// 5. MAIN CARD COMPONENT
// ---------------------------------------------------------------------------
class AdaptiveGrowthLightCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._modalOpen = false;
  }

  connectedCallback() {
    this._onKeyDown = (e) => {
      if (e.key === "Escape" && this._modalOpen) {
        this._closeModal();
      }
    };
    window.addEventListener("keydown", this._onKeyDown);
  }

  disconnectedCallback() {
    if (this._onKeyDown) {
      window.removeEventListener("keydown", this._onKeyDown);
    }
  }

  setConfig(config) {
    if (!config.entity && !config.automation_switch) {
      throw new Error("Please define an 'entity' (automation switch) in card configuration.");
    }
    this._config = {
      entity: config.entity || config.automation_switch,
      layout: config.layout || "compact",
      ...config,
    };
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  _openModal() {
    this._modalOpen = true;
    this.render();
  }

  _closeModal() {
    this._modalOpen = false;
    this.render();
  }

  _findCompanionEntities() {
    if (!this._hass) return {};
    const baseEntityId = this._config.entity;
    const baseName = baseEntityId ? baseEntityId.split(".")[1] : "";

    const resolveEntity = (domain, patterns) => {
      const patternList = Array.isArray(patterns) ? patterns : [patterns];
      for (const p of patternList) {
        const direct = `${domain}.${baseName}_${p}`;
        if (this._hass.states[direct]) return this._hass.states[direct];
      }
      for (const eid in this._hass.states) {
        if (!eid.startsWith(`${domain}.`)) continue;
        if (!eid.includes(baseName)) continue;
        for (const p of patternList) {
          if (eid.includes(p)) return this._hass.states[eid];
        }
      }
      return null;
    };

    const automationSwitch =
      baseEntityId && baseEntityId.startsWith("switch.")
        ? this._hass.states[baseEntityId]
        : resolveEntity("switch", ["automation", "automation_switch"]) || this._hass.states[baseEntityId];

    return {
      automationSwitch,
      statusSensor: resolveEntity("sensor", ["status"]),
      nextSessionSensor: resolveEntity("sensor", ["next_session"]),
      suppHoursSensor: resolveEntity("sensor", ["supplementary_hours_today", "supplementary_hours"]),
      naturalDaylightSensor: resolveEntity("sensor", ["natural_daylight_today", "natural_daylight"]),
      seasonalProfileSensor: resolveEntity("sensor", ["seasonal_profile"]),
      earliestTurnOnSensor: resolveEntity("sensor", ["earliest_turn_on_of_year", "earliest_turn_on"]),
      targetPhotoperiodNumber: resolveEntity("number", ["target_photoperiod"]),
      morningSplitNumber: resolveEntity("number", ["morning_split"]),
      daylightOverlapNumber: resolveEntity("number", ["daylight_overlap"]),
      earliestStartEntity: resolveEntity("time", ["earliest_morning_start", "earliest_start"]),
      latestEndEntity: resolveEntity("time", ["latest_evening_end", "latest_end"]),
      lightingModeSelect: resolveEntity("select", ["lighting_mode"]),
    };
  }

  _toggleAutomation(e) {
    if (e) e.stopPropagation();
    const { automationSwitch } = this._findCompanionEntities();
    if (!automationSwitch) return;
    this._hass.callService("switch", "toggle", {
      entity_id: automationSwitch.entity_id,
    });
  }

  _toggleTargetLight(e) {
    if (e) e.stopPropagation();
    const { automationSwitch } = this._findCompanionEntities();
    const targetEntityId = automationSwitch?.attributes?.target_entity;
    if (!targetEntityId || !this._hass.states[targetEntityId]) return;
    this._hass.callService("homeassistant", "toggle", {
      entity_id: targetEntityId,
    });
  }

  _setPhotoperiod(e) {
    const val = parseFloat(e.target.value);
    const { targetPhotoperiodNumber } = this._findCompanionEntities();
    if (targetPhotoperiodNumber) {
      this._hass.callService("number", "set_value", {
        entity_id: targetPhotoperiodNumber.entity_id,
        value: val,
      });
    }
  }

  _setMorningSplit(e) {
    const val = parseFloat(e.target.value);
    const { morningSplitNumber } = this._findCompanionEntities();
    if (morningSplitNumber) {
      this._hass.callService("number", "set_value", {
        entity_id: morningSplitNumber.entity_id,
        value: val,
      });
    }
  }

  _setOverlap(e) {
    const val = parseFloat(e.target.value);
    const { daylightOverlapNumber } = this._findCompanionEntities();
    if (daylightOverlapNumber) {
      this._hass.callService("number", "set_value", {
        entity_id: daylightOverlapNumber.entity_id,
        value: val,
      });
    }
  }

  _setEarliestStart(e) {
    const val = e.target.value;
    if (!val) return;
    const { earliestStartEntity } = this._findCompanionEntities();
    if (earliestStartEntity) {
      const timeStr = val.length === 5 ? `${val}:00` : val;
      this._hass.callService("time", "set_value", {
        entity_id: earliestStartEntity.entity_id,
        time: timeStr,
      });
    }
  }

  _setLatestEnd(e) {
    const val = e.target.value;
    if (!val) return;
    const { latestEndEntity } = this._findCompanionEntities();
    if (latestEndEntity) {
      const timeStr = val.length === 5 ? `${val}:00` : val;
      this._hass.callService("time", "set_value", {
        entity_id: latestEndEntity.entity_id,
        time: timeStr,
      });
    }
  }

  _setMode(mode) {
    const { lightingModeSelect } = this._findCompanionEntities();
    if (lightingModeSelect) {
      lightingModeSelect.state = mode;
      this.render();
      this._hass.callService("select", "select_option", {
        entity_id: lightingModeSelect.entity_id,
        option: mode,
      });
    }
  }

  render() {
    if (!this._hass || !this._config) return;

    const comps = this._findCompanionEntities();
    const {
      automationSwitch,
      statusSensor,
      nextSessionSensor,
      suppHoursSensor,
      naturalDaylightSensor,
      seasonalProfileSensor,
      earliestTurnOnSensor,
      targetPhotoperiodNumber,
      morningSplitNumber,
      daylightOverlapNumber,
      earliestStartEntity,
      latestEndEntity,
      lightingModeSelect,
    } = comps;

    const isEnabled = automationSwitch ? automationSwitch.state === "on" : true;
    const currentStatus = automationSwitch?.attributes?.status || (statusSensor ? statusSensor.state : "idle");
    const nextSessionText = automationSwitch?.attributes?.next_session_str || (nextSessionSensor ? nextSessionSensor.state : "Scheduled dynamically");

    const suppHours =
      automationSwitch?.attributes?.supplementary_hours !== undefined
        ? automationSwitch.attributes.supplementary_hours
        : suppHoursSensor ? parseFloat(suppHoursSensor.state) || 0 : 0;

    const daylightHours =
      automationSwitch?.attributes?.natural_daylight_hours !== undefined
        ? automationSwitch.attributes.natural_daylight_hours
        : naturalDaylightSensor ? parseFloat(naturalDaylightSensor.state) || 0 : 0;

    const targetHours = targetPhotoperiodNumber
      ? parseFloat(targetPhotoperiodNumber.state) || 14.0
      : automationSwitch?.attributes?.target_photoperiod || 14.0;

    const morningSplit = morningSplitNumber
      ? parseFloat(morningSplitNumber.state) || 50.0
      : automationSwitch?.attributes?.morning_split || 50.0;

    const daylightOverlap = daylightOverlapNumber
      ? parseFloat(daylightOverlapNumber.state) || 1.0
      : automationSwitch?.attributes?.daylight_overlap || 1.0;

    const lightingMode = lightingModeSelect
      ? lightingModeSelect.state
      : automationSwitch?.attributes?.lighting_mode || "both";

    const hasEarliestStart = earliestStartEntity && earliestStartEntity.state && earliestStartEntity.state !== "unknown" && earliestStartEntity.state !== "unavailable";
    const earliestStartVal = hasEarliestStart ? earliestStartEntity.state.substring(0, 5) : "";

    const hasLatestEnd = latestEndEntity && latestEndEntity.state && latestEndEntity.state !== "unknown" && latestEndEntity.state !== "unavailable";
    const latestEndVal = hasLatestEnd ? latestEndEntity.state.substring(0, 5) : "";

    const earliestEff = automationSwitch?.attributes?.earliest_turn_on || earliestTurnOnSensor?.state || "--:--";
    const seasonalMonths = automationSwitch?.attributes?.seasonal_months || seasonalProfileSensor?.attributes?.months || [];
    const targetEntityId = automationSwitch?.attributes?.target_entity || "";
    const targetState = targetEntityId && this._hass.states[targetEntityId] ? this._hass.states[targetEntityId].state : null;

    const friendlyName = this._config.name || automationSwitch?.attributes?.friendly_name?.replace(/ Automation$/, "") || "Adaptive Plant Light";
    const badge = getStatusBadge(currentStatus, isEnabled);

    const isExpandedLayout = this._config.layout === "expanded";

    // Assemble unified data package for details panel
    const detailsData = {
      isModal: !isExpandedLayout,
      friendlyName,
      lightingMode,
      isEnabled,
      badge,
      nextSessionText,
      suppHours,
      daylightHours,
      targetHours,
      morningSplit,
      daylightOverlap,
      earliestStartVal,
      latestEndVal,
      earliestEff,
      sunriseStr: automationSwitch?.attributes?.sunrise || statusSensor?.attributes?.sunrise,
      sunsetStr: automationSwitch?.attributes?.sunset || statusSensor?.attributes?.sunset,
      mornStartStr: automationSwitch?.attributes?.today_morning_start || earliestTurnOnSensor?.attributes?.today_morning_start,
      mornEndStr: automationSwitch?.attributes?.today_morning_end || earliestTurnOnSensor?.attributes?.today_morning_end,
      eveStartStr: automationSwitch?.attributes?.today_evening_start || earliestTurnOnSensor?.attributes?.today_evening_start,
      eveEndStr: automationSwitch?.attributes?.today_evening_end || earliestTurnOnSensor?.attributes?.today_evening_end,
      seasonalMonths,
      targetEntityId,
      targetState,
    };

    const sproutIcon = `M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17.93V18c0-.55-.45-1-1-1s-1 .45-1 1v1.93A8.001 8.001 0 014.07 13H6c.55 0 1-.45 1-1s-.45-1-1-1H4.07A8.001 8.001 0 0111 4.07V6c0 .55.45 1 1 1s1-.45 1-1V4.07A8.001 8.001 0 0119.93 11H18c-.55 0-1 .45-1 1s.45 1 1 1h1.93A8.001 8.001 0 0113 19.93z`;

    this.shadowRoot.innerHTML = `
      <style>${CARD_STYLES}</style>

      ${isExpandedLayout ? `
        <!-- Permanently Expanded Layout -->
        <ha-card class="expanded-card">
          ${renderDetailsPanel(detailsData)}
        </ha-card>
      ` : `
        <!-- Compact Tile Mode (Default) -->
        <ha-card class="compact-tile" id="card-tile">
          <div class="tile-left">
            <div class="tile-icon-wrap ${isEnabled ? "active" : ""}">
              <svg viewBox="0 0 24 24"><path d="${sproutIcon}"/></svg>
            </div>
            <div class="tile-info">
              <div class="tile-title">${friendlyName}</div>
              <div class="tile-status-row">
                <span class="tile-badge ${badge.class}">${badge.label}</span>
                <span class="tile-next">${nextSessionText}</span>
              </div>
              <div class="tile-stats-row">
                <span class="stat-sun">☀️ ${daylightHours}h</span>
                <span>•</span>
                <span class="stat-supp">🌱 ${suppHours}h</span>
                <span>/</span>
                <span class="stat-target">🎯 ${targetHours}h</span>
              </div>
            </div>
          </div>
          <div class="tile-right">
            <label class="toggle-switch" id="master-toggle-wrap">
              <input type="checkbox" id="master-toggle" ${isEnabled ? "checked" : ""}>
              <span class="slider"></span>
            </label>
            <div class="tile-chevron">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
              </svg>
            </div>
          </div>
        </ha-card>

        <!-- Interactive Modal Dialog -->
        ${this._modalOpen ? `
          <div class="modal-backdrop" id="modal-backdrop">
            <div class="modal-dialog" id="modal-dialog">
              <button class="modal-close-btn" id="modal-close-btn" title="Close">✕</button>
              ${renderDetailsPanel(detailsData)}
            </div>
          </div>
        ` : ""}
      `}
    `;

    this._bindEvents();
  }

  _bindEvents() {
    const root = this.shadowRoot;

    // Tile click to open modal
    const tile = root.getElementById("card-tile");
    if (tile) {
      tile.addEventListener("click", () => this._openModal());
    }

    // Modal close button
    const closeBtn = root.getElementById("modal-close-btn");
    if (closeBtn) {
      closeBtn.addEventListener("click", () => this._closeModal());
    }

    // Modal backdrop click
    const backdrop = root.getElementById("modal-backdrop");
    if (backdrop) {
      backdrop.addEventListener("click", (e) => {
        if (e.target.id === "modal-backdrop") {
          this._closeModal();
        }
      });
    }

    // Stop propagation on master toggle click so it doesn't open modal
    const toggleWrap = root.getElementById("master-toggle-wrap");
    if (toggleWrap) {
      toggleWrap.addEventListener("click", (e) => e.stopPropagation());
    }

    // Toggle automation switch
    const toggle = root.getElementById("master-toggle");
    if (toggle) {
      toggle.addEventListener("change", (e) => this._toggleAutomation(e));
    }

    // Controls
    const targetSlider = root.getElementById("target-slider");
    if (targetSlider) {
      targetSlider.addEventListener("change", (e) => this._setPhotoperiod(e));
    }

    const splitSlider = root.getElementById("split-slider");
    if (splitSlider) {
      splitSlider.addEventListener("change", (e) => this._setMorningSplit(e));
    }

    const overlapSlider = root.getElementById("overlap-slider");
    if (overlapSlider) {
      overlapSlider.addEventListener("change", (e) => this._setOverlap(e));
    }

    const earliestInput = root.getElementById("earliest-start-input");
    if (earliestInput) {
      earliestInput.addEventListener("change", (e) => this._setEarliestStart(e));
    }

    const latestInput = root.getElementById("latest-end-input");
    if (latestInput) {
      latestInput.addEventListener("change", (e) => this._setLatestEnd(e));
    }

    const modeBtns = root.querySelectorAll(".mode-btn");
    modeBtns.forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const mode = e.target.getAttribute("data-mode");
        if (mode) this._setMode(mode);
      });
    });

    const manualBtn = root.getElementById("manual-light-btn");
    if (manualBtn) {
      manualBtn.addEventListener("click", (e) => this._toggleTargetLight(e));
    }
  }

  getCardSize() {
    return this._config.layout === "expanded" ? 6 : 1;
  }

  static getConfigElement() {
    return document.createElement("adaptive-growth-light-card-editor");
  }

  static getStubConfig(hass) {
    if (!hass || !hass.states) return { entity: "", layout: "compact" };
    const candidates = Object.keys(hass.states).filter((eid) => {
      if (!eid.startsWith("switch.")) return false;
      const s = hass.states[eid];
      return (
        eid.endsWith("_automation") ||
        s?.attributes?.target_entity !== undefined ||
        eid.includes("adaptive_light") ||
        eid.includes("adaptive_growth_light")
      );
    });
    return {
      entity: candidates.length > 0 ? candidates[0] : "",
      layout: "compact",
    };
  }
}

// ---------------------------------------------------------------------------
// 6. CARD VISUAL EDITOR COMPONENT
// ---------------------------------------------------------------------------
class AdaptiveGrowthLightCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._initialized = false;
  }

  setConfig(config) {
    this._config = { layout: "compact", ...config };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _getDiscoveredEntities() {
    if (!this._hass || !this._hass.states) return [];
    return Object.keys(this._hass.states)
      .filter((eid) => {
        if (!eid.startsWith("switch.")) return false;
        const s = this._hass.states[eid];
        return (
          eid.endsWith("_automation") ||
          s?.attributes?.target_entity !== undefined ||
          eid.includes("adaptive_light") ||
          eid.includes("adaptive_growth_light")
        );
      })
      .map((eid) => ({
        entity_id: eid,
        name:
          this._hass.states[eid].attributes.friendly_name?.replace(/ Automation$/, "") ||
          eid.split(".")[1],
      }));
  }

  _render() {
    if (!this._hass || !this._config) return;

    if (!this._initialized) {
      this._initialized = true;
      const style = document.createElement("style");
      style.textContent = `
        :host {
          display: flex;
          flex-direction: column;
          gap: 16px;
          padding: 8px 0;
          box-sizing: border-box;
        }
        .chips-container {
          background: var(--secondary-background-color, rgba(255, 255, 255, 0.04));
          border: 1px solid var(--divider-color, rgba(255, 255, 255, 0.1));
          border-radius: 8px;
          padding: 12px;
          margin-bottom: 4px;
        }
        .chips-title {
          font-size: 11px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          color: var(--secondary-text-color, #94a3b8);
          margin-bottom: 8px;
          display: flex;
          align-items: center;
          gap: 6px;
        }
        .chips-list {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }
        .chip {
          background: var(--card-background-color, rgba(255, 255, 255, 0.06));
          border: 1px solid var(--primary-color, #10b981);
          color: var(--primary-text-color, #f8fafc);
          padding: 6px 12px;
          border-radius: 16px;
          font-size: 12px;
          font-weight: 500;
          cursor: pointer;
          display: inline-flex;
          align-items: center;
          gap: 6px;
          transition: all 0.2s ease;
        }
        .chip:hover {
          background: var(--primary-color, #10b981);
          color: white;
        }
        .chip.active {
          background: var(--primary-color, #10b981);
          color: white;
          box-shadow: 0 0 10px rgba(16, 185, 129, 0.4);
        }
      `;
      this.shadowRoot.appendChild(style);

      this._chipsRoot = document.createElement("div");
      this.shadowRoot.appendChild(this._chipsRoot);

      this._form = document.createElement("ha-form");
      this._form.addEventListener("value-changed", (ev) => this._valueChanged(ev));
      this._form.computeLabel = (schema) => {
        if (schema.name === "entity") return "Adaptive Light Entity (Automation Switch)";
        if (schema.name === "name") return "Card Title (Optional)";
        if (schema.name === "layout") return "Display Mode";
        return schema.name;
      };
      this._form.computeHelper = (schema) => {
        if (schema.name === "entity") return "Select the Adaptive Growth Light entity to monitor and control.";
        if (schema.name === "layout") return "Compact tile fits in 1-row dashboard grids and opens detailed modal on tap.";
        return "";
      };
      this.shadowRoot.appendChild(this._form);
    }

    const discovered = this._getDiscoveredEntities();
    if (discovered.length > 0) {
      this._chipsRoot.innerHTML = `
        <div class="chips-container">
          <div class="chips-title">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17.93V18c0-.55-.45-1-1-1s-1 .45-1 1v1.93A8.001 8.001 0 014.07 13H6c.55 0 1-.45 1-1s-.45-1-1-1H4.07A8.001 8.001 0 0111 4.07V6c0 .55.45 1 1 1s1-.45 1-1V4.07A8.001 8.001 0 0119.93 11H18c-.55 0-1 .45-1 1s.45 1 1 1h1.93A8.001 8.001 0 0113 19.93z"/>
            </svg>
            Discovered Adaptive Lights
          </div>
          <div class="chips-list">
            ${discovered
              .map(
                (d) => `
              <button type="button" class="chip ${this._config.entity === d.entity_id ? "active" : ""}" data-entity="${d.entity_id}">
                ${d.name}
              </button>
            `
              )
              .join("")}
          </div>
        </div>
      `;

      this._chipsRoot.querySelectorAll(".chip").forEach((btn) => {
        btn.addEventListener("click", (e) => {
          e.preventDefault();
          const eid = btn.getAttribute("data-entity");
          if (eid) {
            this._valueChanged({ detail: { value: { ...this._config, entity: eid } } });
          }
        });
      });
    } else {
      this._chipsRoot.innerHTML = "";
    }

    const schema = [
      {
        name: "entity",
        required: true,
        selector: {
          entity: {
            filter: [
              { integration: "adaptive_growth_light", domain: "switch" },
              { integration: "adaptive_growth_light" },
            ],
          },
        },
      },
      {
        name: "name",
        selector: { text: {} },
      },
      {
        name: "layout",
        selector: {
          select: {
            options: [
              { value: "compact", label: "Compact Tile (Opens Modal on Tap)" },
              { value: "expanded", label: "Permanently Expanded (Full Details)" },
            ],
          },
        },
      },
    ];

    this._form.hass = this._hass;
    this._form.data = this._config;
    this._form.schema = schema;
  }

  _valueChanged(ev) {
    if (!this._config || !this._hass) return;
    const newConfig = { ...this._config, ...ev.detail.value };
    this._config = newConfig;
    this._render();
    this.dispatchEvent(
      new CustomEvent("config-changed", {
        detail: { config: newConfig },
        bubbles: true,
        composed: true,
      })
    );
  }
}

// Register components with customElements
customElements.define("adaptive-growth-light-card", AdaptiveGrowthLightCard);
customElements.define("adaptive-growth-light-card-editor", AdaptiveGrowthLightCardEditor);

// Register card with Home Assistant Lovelace card picker
window.customCards = window.customCards || [];
window.customCards.push({
  type: "adaptive-growth-light-card",
  name: "Adaptive Growth Light Card",
  description: "Intelligent supplementary plant lighting controller with seasonal daylight visualization.",
  preview: true,
  documentationURL: "https://github.com/kujbol/adaptive_growth_light",
});
