<div align="center">

# 🏝️ Oasis

**A Dynamic Island for Windows — live weather in a floating pill.**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-brightgreen.svg)](package.json)
[![Platform](https://img.shields.io/badge/platform-Windows-0078D4?logo=windows&logoColor=white)](https://github.com/Crackle2K/oasis)
[![Built with Electron](https://img.shields.io/badge/built%20with-Electron-47848F?logo=electron&logoColor=white)](https://electronjs.org)
[![Node.js](https://img.shields.io/badge/Node.js-18%2B-339933?logo=node.js&logoColor=white)](https://nodejs.org)
[![Stars](https://img.shields.io/github/stars/Crackle2K/oasis?style=social)](https://github.com/Crackle2K/oasis/stargazers)
[![Issues](https://img.shields.io/github/issues/Crackle2K/oasis)](https://github.com/Crackle2K/oasis/issues)
[![Last Commit](https://img.shields.io/github/last-commit/Crackle2K/oasis)](https://github.com/Crackle2K/oasis/commits/main)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/Crackle2K/oasis/pulls)

</div>

---

Oasis is a lightweight Electron app that pins a sleek, pill-shaped weather widget to the top of your screen — inspired by the iPhone Dynamic Island. It shows your current temperature and weather condition at a glance, with no taskbar clutter, no window chrome, and six built-in themes.

## Features

- **Live weather** — fetches real-time temperature and conditions using your IP location (no API key required)
- **6 themes** — Dark, Glass, Neon, Light, Nord, and Aurora; switchable at runtime via right-click
- **Celsius / Fahrenheit** — toggle units from the right-click menu; preference is saved
- **Always-on-top** — floats above all other windows without stealing focus
- **Draggable** — reposition the island anywhere on screen by clicking and dragging
- **Frameless & transparent** — only the pill is visible; no borders, no title bar
- **Auto-refresh** — weather updates every 10 minutes automatically
- **Zero config** — works out of the box; settings persist automatically between sessions

## Themes

| Theme | Description |
|-------|-------------|
| **Dark** | Jet-black pill with white text. The default. |
| **Glass** | Frosted-glass translucency with a soft blur. Works best over a colourful wallpaper. |
| **Neon** | Near-black background with electric-cyan text and icon glow. |
| **Light** | Light-grey pill with dark text. Great over bright desktops. |
| **Nord** | Deep blue-grey from the [Nord](https://www.nordtheme.com/) colour palette. |
| **Aurora** | Purple-to-pink gradient. Bold and vibrant. |

Switch themes at any time: **right-click the island → Theme**.

## Getting Started

### Prerequisites

- [Node.js](https://nodejs.org/) 18 or later
- npm (bundled with Node.js)

### Installation

```bash
git clone https://github.com/Crackle2K/oasis.git
cd oasis
npm install
```

### Running

```bash
npm start
```

For development with DevTools access on port 9222:

```bash
npm run dev
```

## Usage

| Action | How |
|--------|-----|
| **Reposition** | Click and drag the island |
| **Switch theme** | Click the ⚙ gear icon (right side) or right-click → Theme |
| **Change unit** | Click the ⚙ gear icon (right side) or right-click → Temperature Unit |
| **Quit** | Click the ⚙ gear icon (right side) or right-click → Quit Oasis |

Settings (theme and temperature unit) are saved automatically to your system's app data folder and restored on every launch.

## Configuration

Oasis stores a `config.json` file in your Electron app data directory:

- **Windows:** `%APPDATA%\dynamic-island\config.json`

You can edit this file directly while the app is not running:

```json
{
  "theme": "dark",
  "temperatureUnit": "celsius"
}
```

| Key | Values | Default |
|-----|--------|---------|
| `theme` | `dark` `glass` `neon` `light` `nord` `aurora` | `dark` |
| `temperatureUnit` | `celsius` `fahrenheit` | `celsius` |

## How It Works

```
App launch
  └─ Reads config.json (or uses defaults)
  └─ Renders transparent, frameless, always-on-top window

Weather fetch (on load + every 10 min)
  ├─ ip-api.com  →  latitude / longitude
  └─ open-meteo.com  →  temperature + WMO weather code
        └─ mapped to: clear, partly-cloudy, cloudy, fog, rain, snow, thunderstorm

Right-click
  └─ Electron context menu
        ├─ Theme change  →  CSS class on .island  +  saved to config.json
        └─ Unit change   →  client-side conversion  +  saved to config.json
```

Both APIs are free and require no authentication.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Runtime | [Electron](https://electronjs.org) |
| Language | JavaScript (vanilla) |
| UI | HTML5 + CSS3 (custom properties, `backdrop-filter`) |
| HTTP | [node-fetch](https://github.com/node-fetch/node-fetch) |
| Geolocation | [ip-api.com](https://ip-api.com) |
| Weather | [Open-Meteo](https://open-meteo.com) |
| Config | `fs` + Electron `userData` |

## Project Structure

```
oasis/
├── main.js          # Electron main process — window, IPC, context menu, config
├── preload.js       # Context bridge (IPC → renderer API)
├── src/
│   ├── index.html   # Renderer — weather display, theme application
│   └── styles.css   # Themes and layout
├── .env.example     # Environment variable reference
└── package.json
```

## Contributing

1. Fork the repo and create a feature branch
2. Make your changes
3. Open a pull request — describe what you changed and why

Bug reports and feature requests are welcome via [GitHub Issues](https://github.com/Crackle2K/oasis/issues).

## License

[MIT](LICENSE) — © 2026 Dinesh Sinnathamby
