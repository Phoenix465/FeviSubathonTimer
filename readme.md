# FeviSubathonTimer

A professional, easy-to-use Subathon Timer for [feviknight](https://www.twitch.tv/feviknight) using OBS Studio. This tool helps manage subathon events, automatically updating your stream overlay but requires manual inputs for contributions (twitch, youtube, chzzk, afreeca, streamelements).

### Important: At the end of streams, remember to **PAUSE** the timer otherwise the system will "catch-up" and treat it as if it was on the entire time 

https://github.com/user-attachments/assets/e0822c4c-7394-48c8-8921-9e107fbea76b

## Features
- Real-time subathon timer with customizable settings
- OBS Studio integration for automatic overlay updates
- History logging to CSV for tracking event progress
- Autosave and recovery to prevent data loss
- Simple web interface for control and monitoring

## Prerequisites
- **OBS Studio** (Windows, Mac, or Linux)
- **Python 3.12+** (Recommended: 3.12 - version developed in)
- Basic familiarity with installing Python packages

## Setup Instructions

### 1. Download and Extract
- Download the project ZIP from the [GitHub repository](https://github.com/Phoenix465/FeviSubathonTimer) ([release v1.0.0](https://github.com/Phoenix465/FeviSubathonTimer/releases/tag/v1.0.0))
- Extract all files to a folder (e.g., `C:\Users\YourName\FeviSubathonTimer`).

### 2. Install Python Dependencies
Open a terminal in the project folder and run:
```bash
pip install -r requirements.txt
```

### 3. Configure the Project
- Edit `config.json` to set your timer rules, OBS connection details, and other preferences.
- Example config options:
  - `port`: Webserver address (default: `5050`)
  - `obs_host`: OBS WebSocket address (default: `localhost`)
  - `obs_port`: OBS WebSocket port (default: `4455`)
  - `timer_start`: Initial timer value
  - `contribution_map_seconds`: Time added per subscription

### 4. Set Up OBS Studio
- Install the [OBS WebSocket plugin](https://github.com/obsproject/obs-websocket) if not already included (OBS 28+ has it built-in).
- Enable WebSocket server in OBS (`Tools > WebSocket Server Settings`).
- Note the port and password, and update `config.json` accordingly.
- Ensure that there exists two Text(GDI+) labels called (these can be in any scene and all will be updated at the same time)
 - 1) `FeviSubathonTimer-Points`
 - 2) `FeviSubathonTimer-Timer`
- Ensure that the labels are **NOT** set to read from a file, as the program will update the text directly.
### 5. Run the Project
Start the timer server:
```bash
python app.py
```
- The web interface will be available at `http://localhost:5050` (or your configured port).
- Control the timer, view history, and monitor subathon progress from your browser.

## Support & Contributions
- For issues or feature requests, open a GitHub issue.
- Pull requests are welcome!

## License
MIT License

---
Enjoy your subathon!

