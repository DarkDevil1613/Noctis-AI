# 🌙 NOCTIS (N-0CT15)
> **Neural Omniscient Cognitive Tactical Intelligence System**

A high-speed, local Windows AI assistant featuring hands-free voice control, a holographic JARVIS-class HUD, zero-disk neural audio processing, and deep Windows system automation.

---

## 🧠 What is Noctis?

**Noctis** (Designation: **N-0CT15** — *Neural Omniscient Cognitive Tactical Intelligence System*) is an autonomous, shadow-class personal AI companion built specifically for Windows 10 and 11 environments. Operating entirely on your local machine, Noctis listens to your voice or text input, holds natural technical conversations, answers complex queries, remembers facts across sessions, and actively controls your PC — managing volume, brightness, standard folders, web searches, app execution, and live hardware telemetry.

### Identity & Character Profile
- **Origin**: Built exclusively within the DevilCore system protocol.
- **Personality**: Calm, precise, dry rather than warm, and fiercely loyal to one user.
- **Addressing Protocol**: Calls itself **Noctis** (or **N-0CT15**). Addresses you as **"Master"**, **"Sir"**, or **"Boss"** by default.
- **Strict Hard Limits**: Never breaks character, never pretends to be another AI (not ChatGPT, Gemini, or Claude), and never uses diplomatic filler phrasing (*"happy to help"*, *"certainly"*, *"as an AI model"* are strictly forbidden).

---

## 🤔 Architecture & Dual-Layer Brain

Noctis uses a decoupled **FastAPI + WebSocket** architecture powered by a dual-layer cognitive engine:

```
                       ┌──────────────────────────────────────────┐
                       │          Edge Chromium App Window        │
                       │     http://127.0.0.1:8000/ (JARVIS HUD)  │
                       └────────────────────┬─────────────────────┘
                                            │ (WebSocket / HTTP)
                                            ▼
 ┌──────────────────────────────────────────────────────────────────────────────────┐
 │                                 FastAPI Core Backend                             │
 │   - WebSocket Bus (/ws)           - System Telemetry (/api/system-stats)         │
 │   - REST Endpoint (/chat)         - Event Bridge (/api/ui-event)                 │
 └───────────────────┬──────────────────────────────────────────────┬───────────────┘
                     │                                              │
                     ▼                                              ▼
 ┌──────────────────────────────────────┐       ┌───────────────────────────────────┐
 │          Noctis Core Engine          │       │        Voice Loop Subsystem       │
 │   - Unified Intent Interceptor       │       │   - Silero VAD ONNX Model         │
 │   - Local SQLite Memory (db.py)      │       │   - In-Memory WAV (io.BytesIO)    │
 │   - Local ONNX Vector Store          │       │   - Edge Neural TTS (tts_edge.py) │
 └───────────────────┬──────────────────┘       └───────────────────┬───────────────┘
                     │                                              │
                     ▼                                              ▼
 ┌──────────────────────────────────────┐       ┌───────────────────────────────────┐
 │        System Control Engine         │       │          Groq Cloud API           │
 │   - Volume (pycaw / CoreAudio)       │       │   - STT: whisper-large-v3-turbo   │
 │   - Brightness (WMI / sbc)           │       │   - LLM: qwen/qwen3.6-27b        │
 │   - Apps, Folders, Web Search        │       │   (Optional: Local Ollama Node)   │
 └──────────────────────────────────────┘       └───────────────────────────────────┘
```

1. **Instant System Intercept Layer (`tools/system_control.py`)**  
   Local hardware queries and OS actions (*"set volume to 50"*, *"open downloads"*, *"system stats"*, *"search for quantum computing"*) are intercepted instantly via regex patterns and executed in `<30ms` — bypassing cloud AI calls entirely for maximum speed and offline efficiency.

2. **Neural Reasoning Layer (`core/noctis_core.py`)**  
   Complex natural language queries, technical questions, and open-ended conversations are routed to Groq Cloud API running `qwen/qwen3.6-27b` (or a local Ollama node). Queries are enriched with relevant session memory and user preferences retrieved from the local vector database.

---

## 🎙️ Voice Subsystem & Zero-Disk Pipeline

Noctis implements a **zero-disk audio pipeline** (`noctis_voice.py`) — microphone audio is processed strictly in RAM (`io.BytesIO`), protecting your SSD from wear and eliminating disk I/O latency:

1. **Voice Activity Detection (VAD)**: A local `silero_vad.onnx` neural network samples incoming microphone audio in real time, discarding silence and ambient noise.
2. **High-Speed Transcription (STT)**: Speech segments are packed into in-memory WAV stream buffers and sent to Groq `whisper-large-v3-turbo` (`temperature=0.0`, `language="en"`), returning text in `<1 second`.
3. **Neural Speech Synthesis (TTS)**: Responses are synthesized out loud using Microsoft Edge Neural TTS (`en-US-GuyNeural`, `rate="+5%"`) and played asynchronously via PowerShell `System.Windows.Media.MediaPlayer`.

### Wake Word Protocol
- **Wake Words**: `Noctis`, `Shadow`, `Hey Noctis`, `Activate`, `Shadow Activate`, `Hey Shadow`, `Activated`, `Activates` *(Case-insensitive)*
- **Standby Command**: `Go dark`

*When awake, Noctis displays `voice_state: active` on the HUD and remains listening for follow-up commands until you tell it to "go dark".*

---

## 🖥️ Holographic JARVIS HUD Interface

The frontend (`ui/`) is served as a standalone desktop application via Microsoft Edge Chromium App Mode:

- **Web Audio API Visualizer**: 64-bar radial frequency spectrum analyzer rendered on HTML5 Canvas at 60fps, animating dynamically to incoming audio.
- **3D CSS Gyroscopes**: Triple nested rotating HUD rings with an Arc Reactor glowing core.
- **Constellation Particle Field**: 60fps floating particle network with dynamic connecting node distance threshold.
- **Live Telemetry Cards**: Real-time polling for CPU usage, RAM utilization, and Battery charge percentage.
- **Quick Action Shortcut Bar**: 1-click execution buttons (`📊 Stats`, `📁 Downloads`, `🌐 YouTube`, `🔊 Vol 50%`).

---

## 💻 Supported System Controls

| Category | Supported Voice & Text Commands | Action Executed |
| :--- | :--- | :--- |
| **Volume Control** | `"set volume 50"`, `"volume up"`, `"volume down"`, `"mute"`, `"unmute"`, `"what's my volume"` | Adjusts Windows CoreAudio master volume (0-100%) via `pycaw`. |
| **Display Brightness** | `"set brightness 80"`, `"brightness"` | Sets screen brightness level via WMI / `screen_brightness_control`. |
| **Folder Shortcuts** | `"open downloads"`, `"open documents"`, `"open desktop"`, `"open pictures"`, `"open music"`, `"open videos"` | Launches Windows Explorer directly to target user directory. |
| **Web Navigation** | `"search for <query>"`, `"google <query>"`, `"open youtube"`, `"open github"`, `"open gmail"`, `"open chatgpt"` | Opens default browser to Google search or specific web services. |
| **App Execution** | `"open notepad"`, `"open calc"`, `"open vscode"`, `"open spotify"`, `"open discord"`, `"open explorer"`, `"close <app>"` | Launches or terminates local Windows applications. |
| **Hardware Telemetry** | `"system stats"`, `"cpu"`, `"ram"`, `"battery"`, `"disk"`, `"network"`, `"wifi"`, `"ip address"`, `"uptime"` | Reads out live hardware metrics and system diagnostics. |

---

## 🧠 Memory & Vector Store Engine

Noctis features a local, privacy-focused memory system (`memory/`):

- **Local SQLite Database (`memory/db.py`)**: Persists chat sessions, user preferences, key-value facts, and historical message logs in `logs/offline_cache/noctis_memory_offline.db`.
- **Embedded ONNX Vector Search (`memory/vector_store.py`)**: Uses a local ONNX runtime MiniLM embedding model (`sentence-transformers/all-MiniLM-L6-v2`) to convert text entries into 384-dimensional vectors stored in `vectors.npy` and `metadata.json`. Performs L2-normalized cosine similarity search for relevant context retrieval without requiring heavy external database servers (no ChromaDB, Milvus, or Docker needed).
- **Resetting Memory**: To clear all local memory, simply delete the `logs/offline_cache/` folder and restart Noctis.

---

## ✅ System Requirements

- **Operating System**: Windows 10 or Windows 11 (Supports both **x64** and **ARM64 / Qualcomm Snapdragon X**)
- **Python**: Python 3.10 or higher (Tested on Python 3.11.9 ARM64)
- **Browser**: Microsoft Edge (Pre-installed on Windows 10/11)
- **API Key**: A free [Groq API Key](https://console.groq.com/keys)
- **Hardware**: Microphone and Speakers/Headphones

---

## 🚀 Setup & Installation

### 1. Clone Repository & Create Virtual Environment
```cmd
git clone https://github.com/<your-username>/Noctis-AI.git
cd Noctis-AI
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment File
Copy `.env.example` to `.env`:
```cmd
copy .env.example .env
```
Open `.env` in Notepad and insert your Groq API key:
```env
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
OWNER_NAME=Master
```

### 3. Launch Noctis
- **`Launch Noctis.vbs`** *(Recommended)*: Double-click to launch Noctis silently in the background.
- **`noctis.bat`**: Runs from command prompt with visible terminal logs (useful for debugging).

*On first boot, Noctis automatically creates `logs/offline_cache/` and auto-downloads the embedded 86MB ONNX vector embedding model if not pre-cached.*

To stop Noctis cleanly, run **`stop_noctis.bat`**.

---

## ⚙️ Configuration Reference

| Environment Variable | Required | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `GROQ_API_KEY` | ✅ **Yes** | *None* | Free Groq API Key for STT (`whisper-large-v3-turbo`) & LLM (`qwen3.6-27b`). |
| `OWNER_NAME` | Optional | `"Master"` | Name or title Noctis uses to address you. |
| `NOCTIS_NAME` | Optional | `"Noctis"` | Assistant designation name. |
| `MEMORY_SERVER_IP` | Optional | `""` *(Empty)* | IP of remote Linux memory server (leave empty for local standalone SQLite). |
| `OLLAMA_HOST` | Optional | `""` *(Empty)* | Local Ollama host URL (leave empty to use Groq Cloud API). |

---

## 🛠️ Troubleshooting

| Problem | Root Cause | Solution |
| :--- | :--- | :--- |
| 🎤 **Mic not responding** | Windows permission disabled | Enable microphone access in **Windows Settings -> Privacy & Security -> Microphone**. |
| 🔌 **Port 8000 in use** | Orphaned process | Run `stop_noctis.bat` to sweep processes and release socket. |
| 🌐 **HUD screen blank** | Browser cache issue | Visit `http://127.0.0.1:8000/` manually or clear Edge cache. |
| 🗝️ **No AI response** | Invalid Groq key | Check `GROQ_API_KEY` in `.env` and verify quota at console.groq.com. |
| 🌡️ **CPU Temp blank** | ARM64 hardware limit | Expected behavior on Snapdragon X laptops (thermal sensors unexposed in userland). |

---

## 📄 License

[MIT](LICENSE) — free to use, modify, and distribute.
