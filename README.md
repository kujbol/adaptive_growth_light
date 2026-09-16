<p align="center">
  <img src="https://raw.githubusercontent.com/kujbol/adaptive_growth_light/main/images/logo.png" alt="Adaptive Growth Light Logo" width="200" style="border-radius: 24px; box-shadow: 0 8px 24px rgba(0,0,0,0.4);">
</p>

<h1 align="center">🌱 Adaptive Growth Light</h1>

<p align="center">
  <strong>Intelligent supplementary plant lighting & photoperiod management for Home Assistant</strong>
</p>

<p align="center">
  <a href="https://github.com/hacs/default"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg" alt="HACS"></a>
  <a href="https://github.com/kujbol/adaptive_growth_light/releases"><img src="https://img.shields.io/github/v/release/kujbol/adaptive_growth_light?color=10b981" alt="GitHub Release"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
</p>

**Adaptive Growth Light** is an intelligent Home Assistant integration and custom Lovelace card designed to provide optimal supplementary lighting for indoor plants.

Instead of rigid automations triggered by static sunrise/sunset offsets, **Adaptive Growth Light** calculates your exact daily natural photoperiod based on your location and dynamically supplements only the missing hours of light required to hit your plants' daily photoperiod target.

---

## 🌟 Key Features

- 🌿 **Target Photoperiod Control**: Set your plant's daily light requirement (e.g. 14.0 hours/day).
  - In summer, when daylight is 16h, the light stays off automatically.
  - In winter, when daylight drops to 8h, the integration automatically provides the 6h supplement.
- ⏰ **Three Routine Modes**:
  - **Morning Only**: Supplements before sunrise.
  - **Evening Only**: Supplements after sunset.
  - **Both (Split)**: Proportional split between morning and evening (e.g. 50% morning / 50% evening).
- 🌅 **Daylight Overlap Buffer**:
  - Configurable overlap (in hours) to smoothly bridge natural and artificial light.
  - Morning routine continues until `sunrise + overlap` (e.g. 1 hour past sunrise).
  - Evening routine begins `sunset - overlap` (e.g. 1 hour before sunset).
- 📊 **Dual-Mode Dashboard Lovelace Card**:
  - **Minimal View**: Compact card featuring active status glow, master automation toggle, next session countdown, and quick statistics.
  - **Advanced View**: Click to reveal interactive sliders for photoperiod, split %, overlap buffer, and a **Seasonal Photoperiod Matrix Chart**.
- 📈 **Year-Round Sunlight Visualization**:
  - Interactive SVG stacked chart displaying natural daylight (solar amber) vs. required supplementary light (emerald green) across all 12 months for your exact coordinates.
- 🔌 **Per-Light Configuration**: Configure each grow light or switch entity independently.
- 📴 **Master Automation Switch**: Toggle automation on/off per plant directly from the card or through Home Assistant entities.
- 🌐 **Full Multi-Language Support**: English and Polish (Polski) translations included.

---

## 📸 Dashboard Card Preview

The custom `adaptive-growth-light-card` is bundled directly with the integration—no separate frontend install needed!

```yaml
type: custom:adaptive-growth-light-card
entity: switch.bathroom_plant_light_automation
# Optional customization:
name: "Monstera & Ferns"
expanded_by_default: false
```

### Card Features:
- **Minimal Mode**:
  - Plant icon with pulsating emerald glow during active sessions.
  - Master automation toggle switch.
  - Status badge: `Active: Morning Supplement`, `Active: Evening Supplement`, `Daylight Active`, `Idle (Rest)`, or `Disabled`.
  - Next scheduled session with countdown time.
  - Daily metrics: Supplement Hours, Natural Sunlight Hours, Target Hours.
- **Advanced Mode**:
  - Target photoperiod slider (6.0h - 18.0h).
  - Routine mode switcher: `[ Morning ]`, `[ Evening ]`, `[ Both ]`.
  - Morning / Evening ratio slider (when `Both` is selected).
  - Daylight Overlap buffer slider (0.0h - 3.0h).
  - Interactive 12-Month Sunlight Stacked Chart with tooltips.
  - Direct manual light toggle button.

---

## ⚙️ How Photoperiod is Calculated

1. **Natural Daylight**: Using astronomical equations from `astral` and your Home Assistant geographical coordinates:
   $$T_{\text{natural}} = t_{\text{sunset}} - t_{\text{sunrise}}$$
2. **Required Supplementary Light**:
   $$T_{\text{supp}} = \max(0, T_{\text{target}} - T_{\text{natural}})$$
3. **Session Windows with Overlap ($O$)**:
   - **Morning**: Ends at $t_{\text{sunrise}} + O$, begins at $(t_{\text{sunrise}} + O) - T_{\text{morning}}$.
   - **Evening**: Begins at $t_{\text{sunset}} - O$, ends at $(t_{\text{sunset}} - O) + T_{\text{evening}}$.

---

## 📦 Installation

### Method 1: HACS (Recommended)

1. Ensure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance.
2. Open HACS > **Integrations** > Three dots in top right > **Custom repositories**.
3. Add the repository URL: `https://github.com/kujbol/adaptive_growth_light`
4. Select category: **Integration**.
5. Click **Download**, then restart Home Assistant.

### Method 2: Manual Installation

1. Download the latest release from the [Releases](https://github.com/kujbol/adaptive_growth_light/releases) page.
2. Copy the `custom_components/adaptive_growth_light` folder into your Home Assistant `<config>/custom_components/` directory.
3. Restart Home Assistant.

---

## 🚀 Setup & Configuration

1. In Home Assistant, navigate to **Settings** > **Devices & Services** > **Add Integration**.
2. Search for **Adaptive Growth Light**.
3. Configure your plant light:
   - **Name**: A friendly name (e.g. `Bathroom Plant Light`).
   - **Plant Light / Switch Entity**: Select your switch or light (e.g. `switch.bathroom_grow_light`).
   - **Target Photoperiod**: Hours of total light per day (default `14.0h`).
   - **Lighting Routine**: `Morning`, `Evening`, or `Both`.
   - **Morning Split %**: Ratio for morning lighting when in `Both` mode (default `50%`).
   - **Daylight Overlap**: Overlap buffer with natural daylight (default `1.0h`).
4. Click **Submit**.

You can add multiple instances for every plant light in your home!

---

## Entities Created per Instance

| Entity ID | Domain | Description |
| :--- | :--- | :--- |
| `switch.<name>_automation` | `switch` | Master switch to pause or resume automated lighting |
| `sensor.<name>_status` | `sensor` | Current state (`supplementing_morning`, `daylight_active`, etc.) |
| `sensor.<name>_next_session` | `sensor` | Upcoming session start time and duration |
| `sensor.<name>_supplementary_hours` | `sensor` | Hours of supplemental light calculated for today |
| `sensor.<name>_natural_daylight` | `sensor` | Natural daylight duration today |
| `sensor.<name>_seasonal_profile` | `sensor` | Carries 12-month solar and photoperiod matrix data |
| `number.<name>_target_photoperiod` | `number` | Slider to adjust target photoperiod |
| `number.<name>_morning_split` | `number` | Slider to adjust morning/evening ratio in `Both` mode |
| `number.<name>_daylight_overlap` | `number` | Slider to adjust daylight overlap buffer in hours |
| `select.<name>_lighting_mode` | `select` | Dropdown to choose between Morning, Evening, and Both |

---

## 🚢 Releasing Updates

To release a new version, use the automated release script:

```bash
python3 release.py 1.0.0
```

The script automatically audits the repository for any accidental credentials or private keys, bumps versions in `manifest.json` and the frontend card, commits, tags, pushes, and creates a GitHub release.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
