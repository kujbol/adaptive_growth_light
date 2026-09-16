/**
 * Adaptive Growth Light Card for Home Assistant Lovelace
 * Author: @kujbol
 * Version: 1.0.0
 */

const CARD_VERSION = "1.1.3";

console.info(
  `%c ADAPTIVE-GROWTH-LIGHT-CARD %c v${CARD_VERSION} `,
  "color: white; background: #059669; font-weight: 700;",
  "color: #059669; background: #ecfdf5; font-weight: 700;"
);

class AdaptiveGrowthLightCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._isExpanded = false;
    this._tooltipData = null;
  }

  setConfig(config) {
    if (!config.entity && !config.automation_switch) {
      throw new Error("Please define an 'entity' (the automation switch or status sensor)");
    }
    this._config = {
      name: config.name,
      entity: config.entity || config.automation_switch,
      expanded_by_default: config.expanded_by_default || false,
      ...config,
    };
    if (this._config.expanded_by_default) {
      this._isExpanded = true;
    }
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  _findCompanionEntities() {
    if (!this._hass || !this._config.entity) return {};

    const baseEntityId = this._config.entity;
    // Extract base prefix, e.g. switch.bathroom_plant_light_automation -> bathroom_plant_light
    let baseName = baseEntityId.split(".")[1] || "";
    baseName = baseName.replace(/_(automation|status|automation_switch|target_photoperiod)$/, "");

    const domainPrefix = (d) => `${d}.${baseName}`;

    const resolveEntity = (domain, suffix) => {
      const direct = `${domain}.${baseName}_${suffix}`;
      if (this._hass.states[direct]) return this._hass.states[direct];
      // Try fuzzy search
      for (const eid in this._hass.states) {
        if (eid.startsWith(`${domain}.`) && eid.includes(baseName) && eid.endsWith(suffix)) {
          return this._hass.states[eid];
        }
      }
      return null;
    };

    const automationSwitch =
      this._hass.states[baseEntityId]?.attributes?.target_entity !== undefined
        ? this._hass.states[baseEntityId]
        : resolveEntity("switch", "automation") || this._hass.states[baseEntityId];

    const statusSensor = resolveEntity("sensor", "status");
    const nextSessionSensor = resolveEntity("sensor", "next_session");
    const suppHoursSensor = resolveEntity("sensor", "supplementary_hours");
    const naturalDaylightSensor = resolveEntity("sensor", "natural_daylight");
    const seasonalProfileSensor = resolveEntity("sensor", "seasonal_profile");
    const earliestTurnOnSensor = resolveEntity("sensor", "earliest_turn_on");
    const targetPhotoperiodNumber = resolveEntity("number", "target_photoperiod");
    const morningSplitNumber = resolveEntity("number", "morning_split");
    const daylightOverlapNumber = resolveEntity("number", "daylight_overlap");
    const earliestStartEntity = resolveEntity("time", "earliest_start");
    const latestEndEntity = resolveEntity("time", "latest_end");
    const lightingModeSelect = resolveEntity("select", "lighting_mode");

    return {
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
    };
  }

  _toggleAutomation(e) {
    e.stopPropagation();
    const { automationSwitch } = this._findCompanionEntities();
    if (!automationSwitch) return;

    const isCurrentlyOn = automationSwitch.state === "on";
    this._hass.callService("switch", isCurrentlyOn ? "turn_off" : "turn_on", {
      entity_id: automationSwitch.entity_id,
    });
  }

  _toggleTargetLight(e) {
    e.stopPropagation();
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

  _toggleExpand() {
    this._isExpanded = !this._isExpanded;
    this.render();
  }

  _getStatusBadge(status, isEnabled) {
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
          label: "Idle (Rest)",
          class: "badge-idle",
          icon: "M12 2a10 10 0 1010 10A10 10 0 0012 2zm1 17.93V18c0-.55-.45-1-1-1s-1 .45-1 1v1.93A8.001 8.001 0 014.07 13H6c.55 0 1-.45 1-1s-.45-1-1-1H4.07A8.001 8.001 0 0111 4.07V6c0 .55.45 1 1 1s1-.45 1-1V4.07A8.001 8.001 0 0119.93 11H18c-.55 0-1 .45-1 1s.45 1 1 1h1.93A8.001 8.001 0 0113 19.93z",
        };
    }
  }

  _renderSeasonalChart(seasonalMonths, currentTarget) {
    if (!seasonalMonths || !seasonalMonths.length) {
      return `<div class="chart-empty">No seasonal profile data available</div>`;
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

      const natHeight = (natH / maxHourScale) * (chartHeight - 20);
      const suppHeight = (suppH / maxHourScale) * (chartHeight - 20);

      const natY = chartHeight - 20 - natHeight;
      const suppY = natY - suppHeight;

      const isCurrentMonth = m.month === currentMonthIdx;
      const highlightStroke = isCurrentMonth ? `stroke="#34d399" stroke-width="2"` : "";

      barsSvg += `
        <g class="month-col" data-month="${m.name}" data-nat="${m.natural_hours}" data-supp="${m.supplementary_hours}" data-target="${m.target_hours}">
          <!-- Natural daylight bar (amber/gold) -->
          <rect x="${x}" y="${natY}" width="${barWidth}" height="${natHeight}" rx="3" fill="url(#sun-grad)" opacity="${isCurrentMonth ? '1.0' : '0.8'}" />
          <!-- Supplementary light bar (emerald/growth) -->
          ${suppHeight > 0 ? `
            <rect x="${x}" y="${suppY}" width="${barWidth}" height="${suppHeight}" rx="3" fill="url(#plant-grad)" opacity="${isCurrentMonth ? '1.0' : '0.85'}" ${highlightStroke} />
          ` : ""}
          <!-- Month label -->
          <text x="${x + barWidth / 2}" y="${chartHeight - 5}" text-anchor="middle" font-size="9" fill="${isCurrentMonth ? '#34d399' : '#9ca3af'}" font-weight="${isCurrentMonth ? '700' : '500'}">
            ${m.name}
          </text>
        </g>
      `;
    });

    // Target photoperiod line
    const targetY = chartHeight - 20 - (Math.min(maxHourScale, currentTarget) / maxHourScale) * (chartHeight - 20);

    return `
      <div class="seasonal-chart-container">
        <div class="chart-header">
          <span class="chart-title">Year-Round Photoperiod Matrix</span>
          <span class="chart-legend">
            <span class="legend-item"><span class="dot sun-dot"></span>Natural Daylight</span>
            <span class="legend-item"><span class="dot plant-dot"></span>Supplement</span>
          </span>
        </div>
        <svg viewBox="0 0 ${chartWidth} ${chartHeight}" class="seasonal-svg">
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

          <!-- Grid horizontal lines at 8h, 12h, 16h -->
          <line x1="0" y1="${chartHeight - 20 - (8 / maxHourScale) * (chartHeight - 20)}" x2="${chartWidth}" y2="${chartHeight - 20 - (8 / maxHourScale) * (chartHeight - 20)}" stroke="rgba(255,255,255,0.06)" stroke-dasharray="3,3" />
          <line x1="0" y1="${chartHeight - 20 - (12 / maxHourScale) * (chartHeight - 20)}" x2="${chartWidth}" y2="${chartHeight - 20 - (12 / maxHourScale) * (chartHeight - 20)}" stroke="rgba(255,255,255,0.06)" stroke-dasharray="3,3" />
          <line x1="0" y1="${chartHeight - 20 - (16 / maxHourScale) * (chartHeight - 20)}" x2="${chartWidth}" y2="${chartHeight - 20 - (16 / maxHourScale) * (chartHeight - 20)}" stroke="rgba(255,255,255,0.06)" stroke-dasharray="3,3" />

          ${barsSvg}

          <!-- Target Line -->
          <line x1="0" y1="${targetY}" x2="${chartWidth}" y2="${targetY}" stroke="#38bdf8" stroke-width="1.5" stroke-dasharray="4,3" opacity="0.8" />
          <text x="${chartWidth - 2}" y="${targetY - 3}" text-anchor="end" font-size="8" fill="#38bdf8" font-weight="600">Target ${currentTarget}h</text>
        </svg>
      </div>
    `;
  }

  _renderDayTimeline(statusSensor, earliestTurnOnSensor, earliestStartEntity, latestEndEntity) {
    const sunriseStr = statusSensor?.attributes?.sunrise;
    const sunsetStr = statusSensor?.attributes?.sunset;
    const earliestStats = earliestTurnOnSensor?.attributes || {};
    const earliestEff = earliestTurnOnSensor?.state || "--:--";

    const parseIsoHour = (iso) => {
      if (!iso) return null;
      const d = new Date(iso);
      return d.getHours() + d.getMinutes() / 60.0;
    };
    const parseTimeStr = (tStr) => {
      if (!tStr) return null;
      const parts = tStr.split(":");
      return parseInt(parts[0], 10) + parseInt(parts[1], 10) / 60.0;
    };

    const sunriseH = parseIsoHour(sunriseStr) ?? 6.5;
    const sunsetH = parseIsoHour(sunsetStr) ?? 18.5;

    const mornStartStr = earliestStats.today_morning_start;
    const eveStartStr = earliestStats.today_evening_start;
    const mornStartH = parseTimeStr(mornStartStr);
    const eveStartH = parseTimeStr(eveStartStr);

    const hasValidEarliest = earliestStartEntity && earliestStartEntity.state && earliestStartEntity.state !== "unknown" && earliestStartEntity.state !== "unavailable";
    const hasValidLatest = latestEndEntity && latestEndEntity.state && latestEndEntity.state !== "unknown" && latestEndEntity.state !== "unavailable";
    const earliestCutoffH = hasValidEarliest ? parseTimeStr(earliestStartEntity.state) : null;
    const latestCutoffH = hasValidLatest ? parseTimeStr(latestEndEntity.state) : null;

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
        <text x="${x}" y="10" font-size="8" fill="#9ca3af" text-anchor="${h === 0 ? 'start' : (h === 24 ? 'end' : 'middle')}">${String(h).padStart(2, '0')}:00</text>
      `;
    });

    let rectsSvg = "";
    // Background bar (Night)
    rectsSvg += `<rect x="0" y="${barY}" width="${width}" height="${barH}" rx="4" fill="rgba(255,255,255,0.06)" />`;

    // Suppressed morning cut-off zone
    if (earliestCutoffH && earliestCutoffH > 0) {
      const cutX = scaleX(earliestCutoffH);
      rectsSvg += `<rect x="0" y="${barY}" width="${cutX}" height="${barH}" rx="4" fill="rgba(239, 68, 68, 0.18)" stroke="rgba(239, 68, 68, 0.35)" stroke-dasharray="2,2" stroke-width="1" />`;
    }

    // Suppressed evening cut-off zone
    if (latestCutoffH && latestCutoffH < 24) {
      const cutX = scaleX(latestCutoffH);
      rectsSvg += `<rect x="${cutX}" y="${barY}" width="${width - cutX}" height="${barH}" rx="4" fill="rgba(239, 68, 68, 0.18)" stroke="rgba(239, 68, 68, 0.35)" stroke-dasharray="2,2" stroke-width="1" />`;
    }

    // Morning grow light session
    if (mornStartH !== null && mornStartH < sunriseH) {
      const startX = scaleX(mornStartH);
      const endX = scaleX(sunriseH);
      rectsSvg += `<rect x="${startX}" y="${barY}" width="${Math.max(2, endX - startX)}" height="${barH}" fill="#10b981" rx="2" opacity="0.95" />`;
    }

    // Natural daylight
    const sunStartX = scaleX(sunriseH);
    const sunEndX = scaleX(sunsetH);
    rectsSvg += `<rect x="${sunStartX}" y="${barY}" width="${Math.max(2, sunEndX - sunStartX)}" height="${barH}" fill="#f59e0b" rx="2" opacity="0.95" />`;

    // Evening grow light session
    if (eveStartH !== null) {
      const eveLimit = latestCutoffH && latestCutoffH < 24 ? latestCutoffH : 24;
      const eveEndX = scaleX(eveLimit);
      const startX = scaleX(eveStartH);
      if (eveEndX > startX) {
        rectsSvg += `<rect x="${startX}" y="${barY}" width="${Math.max(2, eveEndX - startX)}" height="${barH}" fill="#10b981" rx="2" opacity="0.95" />`;
      }
    }

    // Now indicator
    const nowX = scaleX(nowH);
    const nowSvg = `
      <line x1="${nowX}" y1="${barY - 3}" x2="${nowX}" y2="${barY + barH + 3}" stroke="#38bdf8" stroke-width="2" />
      <polygon points="${nowX-3},${barY-4} ${nowX+3},${barY-4} ${nowX},${barY}" fill="#38bdf8" />
    `;

    return `
      <div class="day-timeline-card">
        <div class="timeline-title-row">
          <span class="timeline-title">24h Schedule Timeline</span>
          <span class="earliest-badge">Earliest Turn-On: <strong>${earliestEff}</strong></span>
        </div>
        <svg viewBox="0 0 ${width} ${height}" class="timeline-svg" style="width: 100%; height: auto; display: block;">
          ${markersSvg}
          ${rectsSvg}
          ${nowSvg}
        </svg>
        <div class="timeline-legend">
          <span class="legend-item"><span class="dot sun-dot"></span>Sunlight (${sunriseStr ? new Date(sunriseStr).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : '06:30'} - ${sunsetStr ? new Date(sunsetStr).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : '18:30'})</span>
          <span class="legend-item"><span class="dot plant-dot"></span>Grow Light</span>
          <span class="legend-item"><span class="dot cutoff-dot"></span>Cut-Off Restricted</span>
        </div>
      </div>
    `;
  }

  render() {
    if (!this._hass || !this._config) return;

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
    } = this._findCompanionEntities();

    const isEnabled = automationSwitch ? automationSwitch.state === "on" : true;
    const currentStatus = statusSensor ? statusSensor.state : "idle";
    const nextSessionText = nextSessionSensor ? nextSessionSensor.state : "Scheduled dynamically";
    const suppHours = suppHoursSensor ? parseFloat(suppHoursSensor.state) || 0 : 0;
    const daylightHours = naturalDaylightSensor ? parseFloat(naturalDaylightSensor.state) || 0 : 0;
    const targetHours = targetPhotoperiodNumber ? parseFloat(targetPhotoperiodNumber.state) || 14.0 : 14.0;
    const morningSplit = morningSplitNumber ? parseFloat(morningSplitNumber.state) || 50.0 : 50.0;
    const daylightOverlap = daylightOverlapNumber ? parseFloat(daylightOverlapNumber.state) || 1.0 : 1.0;
    const lightingMode = lightingModeSelect ? lightingModeSelect.state : "both";
    const hasEarliestStart = earliestStartEntity && earliestStartEntity.state && earliestStartEntity.state !== "unknown" && earliestStartEntity.state !== "unavailable";
    const earliestStartVal = hasEarliestStart ? earliestStartEntity.state.substring(0, 5) : "";
    const hasLatestEnd = latestEndEntity && latestEndEntity.state && latestEndEntity.state !== "unknown" && latestEndEntity.state !== "unavailable";
    const latestEndVal = hasLatestEnd ? latestEndEntity.state.substring(0, 5) : "";

    const seasonalMonths = seasonalProfileSensor?.attributes?.months || [];
    const targetEntityId = automationSwitch?.attributes?.target_entity || "";
    const targetState = targetEntityId && this._hass.states[targetEntityId] ? this._hass.states[targetEntityId].state : null;

    const friendlyName = this._config.name || automationSwitch?.attributes?.friendly_name?.replace(/ Automation$/, "") || "Adaptive Plant Light";
    const badge = this._getStatusBadge(currentStatus, isEnabled);

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
          color: #f3f4f6;
        }
        ha-card {
          background: linear-gradient(135deg, rgba(20, 29, 25, 0.95) 0%, rgba(13, 20, 18, 0.98) 100%);
          backdrop-filter: blur(16px);
          border-radius: 18px;
          border: 1px solid rgba(52, 211, 153, 0.18);
          box-shadow: 0 12px 36px rgba(0, 0, 0, 0.45), 0 0 24px rgba(16, 185, 129, 0.08);
          overflow: hidden;
          padding: 18px;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        ha-card:hover {
          border-color: rgba(52, 211, 153, 0.3);
          box-shadow: 0 14px 40px rgba(0, 0, 0, 0.5), 0 0 30px rgba(16, 185, 129, 0.12);
        }
        /* Header */
        .card-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 14px;
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
          position: relative;
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
        .name-area {
          display: flex;
          flex-direction: column;
        }
        .card-title {
          font-size: 17px;
          font-weight: 700;
          letter-spacing: -0.2px;
          color: #f9fafb;
        }
        .card-subtitle {
          font-size: 11px;
          color: #9ca3af;
          text-transform: uppercase;
          letter-spacing: 0.8px;
          margin-top: 1px;
        }
        /* Toggle Switch */
        .switch-wrap {
          display: flex;
          align-items: center;
        }
        .toggle-switch {
          position: relative;
          display: inline-block;
          width: 46px;
          height: 26px;
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
          border-radius: 26px;
        }
        .slider:before {
          position: absolute;
          content: "";
          height: 20px;
          width: 20px;
          left: 2px;
          bottom: 2px;
          background-color: white;
          transition: .3s cubic-bezier(0.4, 0, 0.2, 1);
          border-radius: 50%;
          box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        input:checked + .slider {
          background-color: #059669;
          box-shadow: 0 0 12px rgba(16, 185, 129, 0.5);
        }
        input:checked + .slider:before {
          transform: translateX(20px);
        }
        /* Status Badge */
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
          padding: 4px 9px;
          border-radius: 6px;
        }
        .badge svg {
          width: 14px;
          height: 14px;
        }
        .badge-active-morn, .badge-active-eve {
          background: rgba(16, 185, 129, 0.2);
          color: #34d399;
          border: 1px solid rgba(52, 211, 153, 0.35);
          animation: pulse-glow 2s infinite ease-in-out;
        }
        .badge-daylight {
          background: rgba(245, 158, 11, 0.2);
          color: #fbbf24;
          border: 1px solid rgba(245, 158, 11, 0.35);
        }
        .badge-idle {
          background: rgba(156, 163, 175, 0.15);
          color: #d1d5db;
        }
        .badge-disabled {
          background: rgba(239, 68, 68, 0.2);
          color: #f87171;
        }
        @keyframes pulse-glow {
          0%, 100% { box-shadow: 0 0 6px rgba(52, 211, 153, 0.2); }
          50% { box-shadow: 0 0 14px rgba(52, 211, 153, 0.6); }
        }
        .next-session-text {
          font-size: 12px;
          color: #9ca3af;
          display: flex;
          align-items: center;
          gap: 4px;
        }
        /* Metrics Grid */
        .metrics-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 10px;
          margin-bottom: 14px;
        }
        .metric-card {
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.06);
          border-radius: 12px;
          padding: 10px;
          display: flex;
          flex-direction: column;
          align-items: center;
          text-align: center;
        }
        .metric-value {
          font-size: 18px;
          font-weight: 700;
          color: #f9fafb;
          margin-top: 2px;
        }
        .metric-label {
          font-size: 10px;
          color: #9ca3af;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }
        .metric-card.highlight {
          border-color: rgba(52, 211, 153, 0.3);
          background: rgba(16, 185, 129, 0.06);
        }
        .metric-card.highlight .metric-value {
          color: #34d399;
        }
        .metric-card.sun .metric-value {
          color: #fbbf24;
        }
        /* Expand Toggle */
        .expand-btn {
          width: 100%;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 8px;
          padding: 7px;
          color: #d1d5db;
          font-size: 11px;
          font-weight: 600;
          letter-spacing: 0.5px;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          transition: all 0.2s ease;
        }
        .expand-btn:hover {
          background: rgba(255, 255, 255, 0.09);
          color: #fff;
        }
        .expand-btn svg {
          width: 14px;
          height: 14px;
          transition: transform 0.3s ease;
        }
        .expand-btn.expanded svg {
          transform: rotate(180deg);
        }
        /* Advanced Panel */
        .advanced-panel {
          margin-top: 14px;
          padding-top: 14px;
          border-top: 1px solid rgba(255, 255, 255, 0.08);
          animation: fadeIn 0.3s ease-in-out;
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-6px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .control-group {
          margin-bottom: 14px;
        }
        .control-label-row {
          display: flex;
          justify-content: space-between;
          font-size: 12px;
          font-weight: 600;
          color: #e5e7eb;
          margin-bottom: 6px;
        }
        .control-value {
          color: #34d399;
          font-weight: 700;
        }
        /* Mode Select Buttons */
        .mode-btn-group {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 6px;
        }
        .mode-btn {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 8px;
          color: #9ca3af;
          padding: 8px 4px;
          font-size: 11px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
        }
        .mode-btn:hover {
          background: rgba(255, 255, 255, 0.1);
          color: #fff;
        }
        .mode-btn.active {
          background: rgba(16, 185, 129, 0.2);
          border-color: rgba(52, 211, 153, 0.5);
          color: #34d399;
        }
        /* Sliders */
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
          background: #374151;
          border-radius: 4px;
        }
        input[type=range]::-webkit-slider-thumb {
          height: 18px;
          width: 18px;
          border-radius: 50%;
          background: #34d399;
          cursor: pointer;
          -webkit-appearance: none;
          margin-top: -6px;
          box-shadow: 0 0 8px rgba(52, 211, 153, 0.6);
        }
        /* Seasonal Chart */
        .seasonal-chart-container {
          background: rgba(0, 0, 0, 0.2);
          border: 1px solid rgba(255, 255, 255, 0.05);
          border-radius: 12px;
          padding: 12px;
          margin-top: 14px;
        }
        .chart-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;
        }
        .chart-title {
          font-size: 11px;
          font-weight: 700;
          color: #d1d5db;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }
        .chart-legend {
          display: flex;
          gap: 10px;
          font-size: 10px;
          color: #9ca3af;
        }
        .legend-item {
          display: flex;
          align-items: center;
          gap: 4px;
        }
        .dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }
        .sun-dot { background: #fbbf24; }
        .plant-dot { background: #34d399; }
        .seasonal-svg {
          width: 100%;
          height: auto;
          overflow: visible;
        }
        .month-col rect {
          transition: opacity 0.2s ease, transform 0.2s ease;
          cursor: pointer;
        }
        .month-col:hover rect {
          opacity: 1 !important;
          filter: brightness(1.2);
        }
        /* Manual Override Row */
        .target-override-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          background: rgba(255, 255, 255, 0.03);
          border-radius: 10px;
          padding: 8px 12px;
          margin-top: 14px;
        }
        .target-override-text {
          font-size: 12px;
          color: #9ca3af;
        }
        .manual-btn {
          background: rgba(52, 211, 153, 0.15);
          border: 1px solid rgba(52, 211, 153, 0.3);
          color: #34d399;
          font-size: 11px;
          font-weight: 600;
          border-radius: 6px;
          padding: 5px 10px;
          cursor: pointer;
        }
        .manual-btn:hover {
          background: rgba(52, 211, 153, 0.25);
        }
        /* 24h Timeline Card */
        .day-timeline-card {
          background: rgba(0, 0, 0, 0.25);
          border: 1px solid rgba(255, 255, 255, 0.06);
          border-radius: 12px;
          padding: 10px 12px;
          margin-bottom: 14px;
        }
        .timeline-title-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 6px;
        }
        .timeline-title {
          font-size: 11px;
          font-weight: 700;
          color: #d1d5db;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }
        .earliest-badge {
          font-size: 11px;
          color: #a7f3d0;
          background: rgba(16, 185, 129, 0.15);
          border: 1px solid rgba(52, 211, 153, 0.3);
          border-radius: 6px;
          padding: 2px 8px;
        }
        .timeline-legend {
          display: flex;
          gap: 12px;
          font-size: 10px;
          color: #9ca3af;
          margin-top: 8px;
          flex-wrap: wrap;
        }
        .cutoff-dot { background: rgba(239, 68, 68, 0.85); }
        /* Cutoff Row */
        .cutoff-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 10px;
          margin-top: 6px;
        }
        .cutoff-group {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .cutoff-group label {
          font-size: 11px;
          color: #9ca3af;
          font-weight: 600;
        }
        .cutoff-group input[type=time] {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.12);
          border-radius: 8px;
          color: #34d399;
          font-weight: 700;
          font-size: 13px;
          padding: 6px 10px;
          outline: none;
          color-scheme: dark;
        }
      </style>

      <ha-card>
        <!-- Minimal Header -->
        <div class="card-header">
          <div class="header-title-area">
            <div class="plant-icon-wrap ${badge.class.includes('active') ? 'active' : ''}">
              <svg viewBox="0 0 24 24">
                <path d="M12 2C6.48 2 2 6.48 2 12c0 3.84 2.16 7.18 5.34 8.87.16-.95.53-2.67 1.66-4.87 1.4-2.73 3.55-4.49 6.27-5.18.35 2.15-.35 4.93-2.02 7.21-.99 1.35-2.28 2.37-3.6 2.94 1.35.65 2.87 1.03 4.35 1.03 5.52 0 10-4.48 10-10S17.52 2 12 2z"/>
              </svg>
            </div>
            <div class="name-area">
              <span class="card-title">${friendlyName}</span>
              <span class="card-subtitle">${lightingMode.toUpperCase()} ROUTINE</span>
            </div>
          </div>
          <!-- Master Switch Toggle -->
          <div class="switch-wrap">
            <label class="toggle-switch">
              <input type="checkbox" id="master-toggle" ${isEnabled ? "checked" : ""}>
              <span class="slider"></span>
            </label>
          </div>
        </div>

        <!-- Status & Next Session -->
        <div class="status-bar">
          <div class="badge ${badge.class}">
            <svg viewBox="0 0 24 24"><path d="${badge.icon}"/></svg>
            <span>${badge.label}</span>
          </div>
          <div class="next-session-text">
            <span>⏰</span>
            <span>${nextSessionText}</span>
          </div>
        </div>

        <!-- 24h Photoperiod Timeline -->
        ${this._renderDayTimeline(statusSensor, earliestTurnOnSensor, earliestStartEntity, latestEndEntity)}

        <!-- Minimal Metrics Grid -->
        <div class="metrics-grid">
          <div class="metric-card highlight">
            <span class="metric-label">Supplement</span>
            <span class="metric-value">${suppHours}h</span>
          </div>
          <div class="metric-card sun">
            <span class="metric-label">Natural Sun</span>
            <span class="metric-value">${daylightHours}h</span>
          </div>
          <div class="metric-card">
            <span class="metric-label">Target</span>
            <span class="metric-value">${targetHours}h</span>
          </div>
        </div>

        <!-- Expand / Advanced Button -->
        <button class="expand-btn ${this._isExpanded ? 'expanded' : ''}" id="expand-btn">
          <span>${this._isExpanded ? "Hide Advanced Settings" : "Configure Photoperiod & Seasonal Chart"}</span>
          <svg viewBox="0 0 24 24"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z" fill="currentColor"/></svg>
        </button>

        <!-- Advanced Expanded Panel -->
        ${this._isExpanded ? `
          <div class="advanced-panel">
            <!-- Target Photoperiod Slider -->
            <div class="control-group">
              <div class="control-label-row">
                <span>Target Photoperiod</span>
                <span class="control-value">${targetHours} hours / day</span>
              </div>
              <input type="range" id="target-slider" min="6" max="18" step="0.5" value="${targetHours}">
            </div>

            <!-- Lighting Mode Selector -->
            <div class="control-group">
              <div class="control-label-row">
                <span>Lighting Routine</span>
                <span class="control-value">${lightingMode.toUpperCase()}</span>
              </div>
              <div class="mode-btn-group">
                <button class="mode-btn ${lightingMode === 'morning' ? 'active' : ''}" data-mode="morning">Morning</button>
                <button class="mode-btn ${lightingMode === 'evening' ? 'active' : ''}" data-mode="evening">Evening</button>
                <button class="mode-btn ${lightingMode === 'both' ? 'active' : ''}" data-mode="both">Both (Split)</button>
              </div>
            </div>

            <!-- Morning Split (if both) -->
            ${lightingMode === 'both' ? `
              <div class="control-group">
                <div class="control-label-row">
                  <span>Morning / Evening Ratio</span>
                  <span class="control-value">${morningSplit}% Morning / ${100 - morningSplit}% Evening</span>
                </div>
                <input type="range" id="split-slider" min="0" max="100" step="5" value="${morningSplit}">
              </div>
            ` : ""}

            <!-- Daylight Overlap Knob -->
            <div class="control-group">
              <div class="control-label-row">
                <span>Daylight Overlap Buffer</span>
                <span class="control-value">${daylightOverlap} hours</span>
              </div>
              <input type="range" id="overlap-slider" min="0" max="3" step="0.25" value="${daylightOverlap}">
            </div>

            <!-- Sleep Protection Cut-Off Controls -->
            <div class="control-group">
              <div class="control-label-row">
                <span>Sleep Protection Cut-Offs</span>
                <span class="control-value">${(earliestStartVal || latestEndVal) ? `${earliestStartVal || "No limit"} - ${latestEndVal || "No limit"}` : "None"}</span>
              </div>
              <div class="cutoff-row">
                <div class="cutoff-group">
                  <label>Earliest Morning Start</label>
                  <input type="time" id="earliest-start-input" value="${earliestStartVal}">
                </div>
                <div class="cutoff-group">
                  <label>Latest Evening End</label>
                  <input type="time" id="latest-end-input" value="${latestEndVal}">
                </div>
              </div>
            </div>

            <!-- Seasonal Chart -->
            ${this._renderSeasonalChart(seasonalMonths, targetHours)}

            <!-- Manual light test override -->
            ${targetEntityId ? `
              <div class="target-override-row">
                <span class="target-override-text">Controlled Light: <strong>${targetEntityId}</strong> ${targetState ? `(${targetState})` : ''}</span>
                <button class="manual-btn" id="manual-light-btn">Toggle Light</button>
              </div>
            ` : ""}
          </div>
        ` : ""}
      </ha-card>
    `;

    this._bindEvents();
  }

  _bindEvents() {
    const root = this.shadowRoot;

    // Toggle automation
    const toggle = root.getElementById("master-toggle");
    if (toggle) {
      toggle.addEventListener("change", (e) => this._toggleAutomation(e));
    }

    // Expand button
    const expandBtn = root.getElementById("expand-btn");
    if (expandBtn) {
      expandBtn.addEventListener("click", () => this._toggleExpand());
    }

    // Advanced controls
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
    return this._isExpanded ? 6 : 3;
  }
}

customElements.define("adaptive-growth-light-card", AdaptiveGrowthLightCard);

// Register card with Home Assistant card picker
window.customCards = window.customCards || [];
window.customCards.push({
  type: "adaptive-growth-light-card",
  name: "Adaptive Growth Light Card",
  description: "Intelligent supplementary plant lighting controller with seasonal daylight visualization.",
  preview: true,
  documentationURL: "https://github.com/kujbol/adaptive_growth_light",
});
