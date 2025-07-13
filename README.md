# AOL Instant Messenger - Classic Revival (Tkinter Edition)

Relive the nostalgia of classic AOL Instant Messenger with this cross-platform Python client. Featuring old-school UI aesthetics, Windows-style buttons, iconic sounds, and multi-window support, this chat client is designed for both fun and retro functionality.

## 🚀 Features

- 🖥️ Cross-platform (Windows `.exe`, macOS `.app`)
- 💬 Real-time text chat with server connection
- 🔔 Sound notifications (`welcome`, `gotmail`, `goodbye`, `im`)
- 🪟 Three-window layout:
  - Main chat window
  - Online Users list
- 📁 Automatic login with saved credentials (`login.json`)
- 📝 Message logging per user
- 🔊 Windows native sound via `winsound` and fallback to `playsound` for macOS

## 📦 Installation

### Windows (.exe)

1. Download the latest `windows.zip` from the [Releases](#) tab.
2. Extract and run `AOLMessenger.exe`.

### macOS (.pkg)

1. Download the `.pkg` file from the [Releases](#).
2. This is in beta so the app may not work

> macOS users: First-time run may require granting audio permissions.

## 🛠 Build From Source

### Requirements

- Python 3.8+
- `playsound` (for macOS)
- `pyinstaller` (for packaging)

### Running

```bash
python main.py
