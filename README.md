<div align="center">

# Oasis

**A Dynamic Island for Windows - live weather in a floating pill.**

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

Oasis is a lightweight Electron app that pins a sleek, pill-shaped weather widget to the top of your screen - inspired by the iPhone Dynamic Island. It shows your current temperature and weather condition at a glance, with no taskbar clutter, no window chrome, and six built-in themes.

## Features

- **Live weather** - temperature, feels-like, humidity, and wind speed; fetched from your IP location with no API key
- **Expandable details** - click v to expand into a card showing city, feels-like, humidity, and wind; collapses back to a pill
- **Day / night icons** - shows a crescent moon at night for clear skies, sun during the day
- **Animated icons** - sun rays rotate, raindrops fall, snow drifts, lightning flickers, fog slides
- **6 themes** - Dark, Glass, Neon, Light, Nord, Aurora; switchable live via gear icon or right-click
- **Celsius / Fahrenheit** - toggle units; preference persisted between sessions
- **Position persistence** - remembers where you dragged the island and restores it on next launch
- **Launch at startup** - optional auto-start via the settings menu
- **Always-on-top** - floats above all other windows without stealing focus
- **Frameless & transparent** - only the pill is visible; no borders, no title bar
- **Auto-refresh** - weather updates every 10 minutes automatically

## Themes

| Theme | Description |
|-------|-------------|
| **Dark** | Jet-black pill with white text. The default. |
| **Glass** | Frosted-glass translucency with a soft blur. Works best over a colourful wallpaper. |
| **Neon** | Near-black background with electric-cyan text and icon glow. |
| **Light** | Light-grey pill with dark text. Great over bright desktops. |
| **Nord** | Deep blue-grey from the [Nord](https://www.nordtheme.com/) colour palette. |
| **Aurora** | Purple-to-pink gradient. Bold and vibrant. |

Switch themes at any time: **right-click the island -> Theme**.

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
| **Expand / collapse** | Click the v chevron (left side) |
| **Switch theme** | Gear icon or right-click -> Theme |
| **Change unit** | Gear icon or right-click -> Temperature Unit |
| **Toggle startup** | Gear icon or right-click -> Launch at Startup |
| **Quit** | Gear icon or right-click -> Quit Oasis |

All preferences - theme, temperature unit, window position - are saved automatically and restored on every launch.

## Configuration

Oasis stores a `config.json` file in your Electron app data directory:

- **Windows:** `%APPDATA%\dynamic-island\config.json`

You can edit this file directly while the app is not running:

```json
{
  "theme": "dark",
  "temperatureUnit": "celsius",
  "windowX": 960,
  "windowY": 20
}
```

| Key | Values | Default |
|-----|--------|---------|
| `theme` | `dark` `glass` `neon` `light` `nord` `aurora` | `dark` |
| `temperatureUnit` | `celsius` `fahrenheit` | `celsius` |
| `windowX` | integer (pixels from left) | screen centre |
| `windowY` | integer (pixels from top) | `20` |

## How It Works

```
App launch
  └─ Reads config.json (or uses defaults)
  └─ Restores last window position (windowX / windowY)
  └─ Renders transparent frameless always-on-top window (400 x 210 px)

Weather fetch (on load + every 10 min)
  ├─ ip-api.com       ->  lat, lon, city name
  └─ open-meteo.com   ->  temperature, apparent_temperature, weathercode,
                          relativehumidity_2m, windspeed_10m, is_day
        └─ weathercode mapped to: clear, partly-cloudy, cloudy, fog, rain, snow, thunderstorm
        └─ is_day=0 + clear  ->  night-clear (crescent moon icon)

Expand / collapse (v button)
  └─ CSS class toggle on .island  ->  height 64px <-> 185px
  └─ pill border-radius <-> rounded-rect border-radius (smooth transition)
  └─ city, feels-like, humidity, wind fade in

Settings (gear button or right-click)
  └─ Electron context menu
        ├─ Theme         ->  CSS class on .island  +  saved to config.json
        ├─ Unit          ->  client-side C/F conversion  +  saved to config.json
        └─ Startup       ->  app.setLoginItemSettings()

Window move
  └─ Saves new x, y to config.json automatically
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
├── main.js          # Electron main process - window, IPC, context menu, config
├── preload.js       # Context bridge (IPC -> renderer API)
├── src/
│   ├── index.html   # Renderer - weather display, theme application
│   └── styles.css   # Themes and layout
├── .env.example     # Environment variable reference
└── package.json
```

## Contributing

1. Fork the repo and create a feature branch
2. Make your changes
3. Open a pull request - describe what you changed and why

Bug reports and feature requests are welcome via [GitHub Issues](https://github.com/Crackle2K/oasis/issues).

## License

[MIT](LICENSE) - © 2026 Dinesh Sinnathamby
