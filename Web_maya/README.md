# 🌐 MAYA // CYBER COMPANION OS — WEB RUNTIME
**Official Web Edition for Nebius x NVIDIA Global AI Hackathon**

Maya Web Edition brings the complete, authentic desktop Cyberpunk experience of Maya directly to the web browser. Judges and users can interact with Maya through **voice speech recognition, neural text-to-speech audio synthesis, autonomous AI reasoning, and neural image generation** from any modern web browser without installing local desktop dependencies.

---

## ⚡ Key Highlights
* **Identical Cyber-OS UI:** Features the exact dark cyberpunk aesthetic (`#020611`, `#040a17`, `#00f0ff` neon accents), top status bar, telemetry bars, and interactive activity matrix feed.
* **Canvas Arc Reactor Engine:** Real-time HTML5 Canvas animation featuring 45 sparkle particles in polar orbit, rotating segmented neon rings, and a pulsing core that reacts to Maya's cognitive state.
* **Audio Harmonic Spectrum:** 32-bar visualizer bouncing to speech and cognitive harmonics.
* **Full Multimodal Capabilities:**
  * **Speech Recognition:** Web Speech API voice capture with push-to-talk microphone.
  * **Neural Voice Synthesis:** Audio vocal response with mute/unmute control.
  * **Neural Image Generation:** Real-time visual asset generation via Pollinations AI.
  * **NVIDIA Open Model Pipeline:** Powered by NVIDIA open-source models (`Nemotron-70B`) served on Nebius Token Factory.

---

## 🚀 How to Run Locally (Instant Test)

### Option A: Double-Click (Windows)
Double-click `run_web_maya.bat`. It will automatically launch your default browser at:
```text
http://localhost:8080
```

### Option B: Command Line (Any OS)
```bash
python app.py
```
Open [http://localhost:8080](http://localhost:8080) in Google Chrome or Microsoft Edge for full Web Speech API support.

---

## 🌍 How to Deploy for Free (To get your Devpost Live Demo Link)

To get a permanent public URL (e.g., `https://maya-ai.onrender.com` or `https://huggingface.co/spaces/...`) for the hackathon judges:

### 1. Render.com (Recommended - 100% Free)
1. Push this `Web_maya` folder or your repository to GitHub.
2. Sign in to [Render.com](https://render.com) and click **New > Web Service**.
3. Select your GitHub repository.
4. Set:
   * **Root Directory:** `Web_maya` (or leave blank if repository root)
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `python app.py`
5. Click **Deploy**. In ~2 minutes, Render gives you a free HTTPS link (e.g., `https://maya-ai.onrender.com`).

### 2. Hugging Face Spaces (Alternative - 100% Free)
1. Go to [Hugging Face Spaces](https://huggingface.co/spaces) and click **Create new Space**.
2. Space SDK: Choose **Docker** or **Static**.
3. Upload the files from `Web_maya/`.
4. Your space is live instantly at: `https://huggingface.co/spaces/YOUR_USERNAME/maya-ai`.

---

## ⚙️ Environment Variables (Optional)

You can set these in your hosting dashboard or local `.env`:
* `PORT`: Port to listen on (default: `8080`)
* `NEBIUS_API_KEY`: Your Nebius Token Factory API key (claimed with code `NEBIUS-DEVPOST-GLOBAL26`)
* `NEBIUS_BASE_URL`: `https://api.tokenfactory.nebius.com/v1`
* `MODEL_NAME`: `nvidia/llama-3.1-nemotron-70b-instruct`

