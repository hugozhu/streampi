# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/claude-code) when working with code in this repository.

## Project Overview

StreamPi is a low-cost, fast-response system monitoring tool for DevOps/SRE teams. It combines:
- **Raspberry Pi** as the hardware platform
- **StreamDeck/StreamDock** (programmable LCD button device) as the physical interface
- **Python 3.12+ with FastAPI** as the software framework

The project enables 24/7 monitoring of cloud-native applications with quick physical button access to key metrics.

## Architecture

```
streampi/
├── main.py              # FastAPI server entry point
├── cli.py               # StreamDeck device driver & key event handling
├── config.json          # Live configuration (contains secrets, in .gitignore)
├── config_sample.json   # Configuration template
├── Assets/              # Fonts (.ttf) and icons (.png)
├── plugins/             # Plugin system
│   ├── plugin.py        # Base StreamDeckPlugin class
│   ├── streamdeck.py    # StreamDeck utility class (text rendering, etc.)
│   └── *_plugin.py      # Individual plugins (auto-discovered)
└── routers/             # FastAPI route definitions
    └── streamdeck.py    # Admin API endpoints
```

## Key Commands

```bash
# Install dependencies (using uv)
uv sync

# Run in development mode
fastapi dev main.py --port 8000

# Run in production mode
fastapi run main.py --port 8000

# Run CLI device driver separately
python cli.py
```

## Plugin System

Plugins are auto-discovered from `plugins/*_plugin.py` files:
- File naming: snake_case (e.g., `btc_plugin.py`)
- Class naming: CamelCase (e.g., `BtcPlugin`)
- Base class: `StreamDeckPlugin` from `plugins/plugin.py`

### Plugin Lifecycle Methods
- `on_will_appear(deck)`: Called when plugin becomes visible
- `on_will_disappear(deck)`: Called when plugin goes off-screen
- `on_key_down(deck)`: Physical key pressed
- `on_key_up(deck)`: Physical key released
- `on_key_long_pressed(deck)`: Key held >1 second
- `on_key_double_click(deck)`: Rapid double-click

### Creating a New Plugin
1. Create `plugins/your_plugin.py`
2. Define `YourPlugin(StreamDeckPlugin)` class
3. Implement lifecycle methods as needed
4. Add to `config.json` scenes array

## Configuration

`config.json` structure:
- `server_port`: FastAPI server port
- `device_model`: "streamdeck" (Elgato) or "streamdock" (Chinese alternative)
- `proxy`: Optional SOCKS5 proxy for API requests
- `plugins`: Global plugin configurations
- `scenes`: 2D array of buttons per page (typically 16 buttons per scene)

## Tech Stack

- **FastAPI** + uvicorn (web framework)
- **asyncio** + uvloop (async runtime)
- **StreamDeck/StreamDock SDK** (USB device drivers)
- **PIL/Pillow** + CairoSVG (image/text rendering)
- **httpx** with SOCKS5 proxy support (HTTP client)
- **aiocache** (in-memory caching)
- **DingTalk Stream API** (messaging integration)

## API Endpoints

Admin routes at `/admin`:
- `GET /admin/ok` - Health check
- `GET /admin/lcd_on` - Turn screen on
- `GET /admin/lcd_off` - Turn screen off
- `GET /admin/prev` - Previous page
- `GET /admin/next` - Next page

API docs: `http://localhost:8000/docs`

## Hardware Setup

Required udev rules for USB device access:
```bash
# StreamDeck (Elgato)
SUBSYSTEMS=="usb", ATTRS{idVendor}=="0fd9", ATTRS{idProduct}=="0063", MODE="0666"

# StreamDock (妙控宝)
SUBSYSTEMS=="usb", ATTRS{idVendor}=="5500", ATTRS{idProduct}=="1001", MODE="0666"
```

## Important Notes

- `config.json` contains API keys/tokens - never commit to git
- Codebase uses async/await throughout - maintain this pattern
- Text rendering uses custom fonts from `Assets/` directory
- Proxy support is important for geolocation-restricted APIs
