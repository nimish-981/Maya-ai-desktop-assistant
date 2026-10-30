---
title: MAYA Cyber Companion OS
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# MAYA — Multilingual AI Companion & Autonomous Agent

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Nebius%20Token%20Factory-7928CA)](https://tokenfactory.nebius.com)
[![Model](https://img.shields.io/badge/Model-NVIDIA%20Nemotron--70B-76B900)](https://build.nvidia.com)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB)](https://python.org)

**Built for the Nebius x NVIDIA Global AI Hackathon**

*An Iron Man / JARVIS-inspired autonomous desktop voice assistant, powered by NVIDIA Nemotron-70B on Nebius Token Factory.*

</div>

---

## 🚀 Nebius Token Factory & NVIDIA Nemotron Integration

Maya leverages the ultra-low-latency **Nebius Token Factory** infrastructure running **NVIDIA's Llama-3.1-Nemotron-70B-Instruct** open-source foundation model as its cognitive engine:

- **Nebius Token Factory:** Provides high-throughput, low-latency API access on dedicated NVIDIA GPU clusters. This sub-second response time is critical for real-time natural voice conversation and instant desktop tool triggering.
- **NVIDIA Nemotron-70B:** Acts as Maya's brain, performing high-precision agentic tool selection across 119+ Windows system functions, understanding bilingual queries (English + Gujarati), and delivering empathetic emotional intelligence.

---

## ✨ Key Capabilities

1. **Autonomous Multi-Agent Architecture (195+ Tools):**
   - **Central AI Orchestrator:** Dynamic intent routing with specialized sub-agents: Operating System Agent, Browser Research Agent, Coding Developer Agent, Productivity & Calendar Agent, Document RAG Agent, Smart Home Agent, and Security Audit Agent.
   - **Explainable Action Receipts:** Every tool execution produces an auditable receipt with execution time, parameters, status, and undo capabilities.
   - Full OS control: Wi-Fi, Bluetooth, Airplane Mode, Mobile Hotspot toggles, window snapping, app switching, and safe power operations.
   - App control: Auto-launch and control any installed Windows software.
   - Screen & Camera awareness: Real-time OCR screen reading (`winocr`) and webcam snapshot analysis (`opencv-python`).
   - Developer tooling: Git status, diff summaries, log inspection, commit assistance, project scaffolding, test execution, and security code reviews.
   - Document RAG & Office: Word (.docx) reading, Excel spreadsheets, duplicate file detection, presentation outlines, and local document semantic retrieval.
   - Calendar & Scheduling: Time-blocked daily schedules, calendar events, meeting agendas, goal/deadline tracking, and habit streaks.
   - Contacts & WhatsApp: Address book management, WhatsApp web/app messaging, and suggested email replies.
   - Smart Home & IoT: Home Assistant integration, smart plugs/lights, and automation scenes.
   - Android Companion: ADB device status, battery monitoring, SMS composition, remote app launches, and PC-to-phone file transfer.

2. **Multilingual Speech & Natural TTS (English, Hindi, Gujarati):**
   - Understands spoken commands in **English**, **Hindi (हिन्दी)**, and **Gujarati (ગુજરાતી)**.
   - Expressive neural voices powered by Microsoft Edge Neural TTS (`en-IN-NeerjaNeural`, `hi-IN-SwaraNeural`, and `gu-IN-DhwaniNeural`).
   - Automatic language detection and instant barge-in speech interruption.

3. **Emotional Intelligence & Mood Adaptation:**
   - Real-time sentiment analysis classifies user emotional states (Empathetic, Cheerful, Playful, Focused, Alert, Standby).
   - Adapts vocal inflection, pitch modulation (Hz), rate, and conversational persona accordingly.

4. **Encrypted Long-Term Memory Vault & Security:**
   - AES-256 Fernet encryption for personal preferences, memories, and facts in SQLite (`maya_history.db`).
   - Project-specific milestone tracking, memory export/purge, and automated PII redaction.

5. **Cyberpunk Arc Reactor Desktop Interface & 3D Web HUD:**
   - CustomTkinter Bento Grid UI with real-time mic FFT audio-reactive spectrum analyzer and rotating Arc Reactor visualizer.
   - Three.js 3D glowing particle orb with bloom shaders in `web-ui/`.

---

## 🛠️ System Architecture

```
User Voice / Text Input
         │
         ▼
Wake Word ("Maya") & Edge Neural STT
         │
         ▼
┌────────────────────────────────────────────────────────┐
│  Nebius Token Factory (Inference Platform)             │
│  Model: nvidia/Llama-3.1-Nemotron-70B-Instruct          │
│                                                        │
│  - Multilingual Intent Classification (EN / GU)        │
│  - Function Calling & Tool Selection                   │
│  - Emotion & Sentiment Modulation                      │
└────────────────────────────────────────────────────────┘
         │
         ├─── Tool Calls ───► Windows Hardware, OS APIs, Skills
         │                     (Wi-Fi, Bluetooth, OCR, File Ops)
         ▼
Natural Spoken Response via Edge Neural Voice
```

---

## 📦 Getting Started

### 1. Prerequisites
- Windows 10/11
- Python 3.10+ (Python 3.12 recommended)
- Microphone & Speakers / Headphones

### 2. Installation

Clone this repository and install dependencies:
```bash
git clone --branch sanitized-project-import https://github.com/nimish-981/Maya-ai-desktop-assistant.git
cd Maya-ai-desktop-assistant
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. API Configuration

Get your Nebius Token Factory API key from the [Nebius Builder Program](https://dev.nebius.com/builders).

Set your environment variable:
```powershell
$env:NEBIUS_API_KEY = "your_nebius_api_key_here"
```

For a persistent Windows user variable, use `setx` instead, then open a new terminal:
```powershell
setx NEBIUS_API_KEY "your_nebius_api_key_here"
```

If you use Groq as a fallback provider, set `GROQ_API_KEY` the same way. Maya reads API keys from environment variables; it does not load `.env` files. Never put real API keys in `config.yaml`, source files, Git commits, or your public Devpost submission. Keep the example values in `.env.example` as placeholders only.

### 4. Running Maya

Run the desktop interface:
```bash
python main.py
```
Or launch the Web UI visualizer:
```bash
python run_web_ui.py
```

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).
