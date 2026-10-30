/**
 * MAYA // CYBER COMPANION OS — PIXEL-PERFECT WEB RUNTIME
 * Complete 1:1 replica of main.py:
 * - Hexagon Radar Scanner with rotating beam
 * - Arc Reactor with 45 particle physics & segmented rings
 * - 32-Bar Dual-Wave Harmonic Spectrum Equalizer
 * - Exact Terminal Dialogue Stream with rich color tags
 * - Live Telemetry & Rapid Command Deck
 */

// ── Colors Matching main.py ──
const COLOR_BG            = "#020611";
const COLOR_CARD_BG       = "#040a17";
const COLOR_CARD_BORDER   = "#0a223e";
const COLOR_CYAN          = "#00f0ff";
const COLOR_CYAN_DIM      = "#0284c7";
const COLOR_GREEN         = "#10b981";
const COLOR_GOLD          = "#f59e0b";
const COLOR_PURPLE        = "#a855f7";
const COLOR_ROSE          = "#f43f5e";
const COLOR_WHITE         = "#ffffff";
const TXT_PRIMARY         = "#e2e8f0";
const TXT_MUTED           = "#64748b";
const TXT_CYAN            = "#38bdf8";

// ── State Variables ──
let currentState = "STANDBY"; // "STANDBY", "LISTENING", "PROCESSING", "SPEAKING"
let ttsMuted = false;
let animT = 0.0;
let arcAngle1 = 0.0;
let arcAngle2 = 0.0;
let radarAngle = 0.0;
let lastFrameTime = performance.now();
const spectrumHeights = new Float32Array(32).fill(0.15);

// ── DOM References ──
const statusPill = document.getElementById("statusPill");
const statusLabel = document.getElementById("statusLabel");
const greetingLabel = document.getElementById("greetingLabel");
const clockLabel = document.getElementById("clockLabel");
const moodLabel = document.getElementById("moodLabel");
const terminalBox = document.getElementById("terminalBox");
const commandEntry = document.getElementById("commandEntry");
const btnListen = document.getElementById("btnListen");
const btnMute = document.getElementById("btnMute");
const cpuLabel = document.getElementById("cpuLabel");
const ramLabel = document.getElementById("ramLabel");
const diskLabel = document.getElementById("diskLabel");
const mediaPreviewBox = document.getElementById("mediaPreviewBox");
const generatedImg = document.getElementById("generatedImg");
const mediaTitle = document.getElementById("mediaTitle");

const reactorCanvas = document.getElementById("reactorCanvas");
const rCtx = reactorCanvas.getContext("2d");

const eqCanvas = document.getElementById("eqCanvas");
const eqCtx = eqCanvas.getContext("2d");

const radarCanvas = document.getElementById("radarCanvas");
const radCtx = radarCanvas.getContext("2d");

// ============================================================
// 1. SPARKLE PARTICLE SYSTEM FOR ARC REACTOR (MATCHING main.py)
// ============================================================
class Particle {
  constructor(cx, cy) {
    this.cx = cx;
    this.cy = cy;
    this.radius = 40 + Math.random() * 115;
    this.angle = Math.random() * Math.PI * 2;
    this.speed = (0.015 + Math.random() * 0.03) * (Math.random() > 0.5 ? 1 : -1);
    this.size = [2, 3, 3, 4, 5][Math.floor(Math.random() * 5)];
    const colors = [COLOR_CYAN, COLOR_CYAN, "#ec4899", COLOR_GOLD, COLOR_WHITE, COLOR_GREEN];
    this.color = colors[Math.floor(Math.random() * colors.length)];
  }

  update(dtScale = 1.0) {
    this.angle += this.speed * dtScale;
    if (this.angle > Math.PI * 2) this.angle -= Math.PI * 2;
    else if (this.angle < 0) this.angle += Math.PI * 2;
  }

  getPos() {
    return {
      x: this.cx + this.radius * Math.cos(this.angle),
      y: this.cy + this.radius * Math.sin(this.angle)
    };
  }
}

const particles = [];
for (let i = 0; i < 45; i++) {
  particles.push(new Particle(reactorCanvas.width / 2, reactorCanvas.height / 2));
}

// ============================================================
// 2. RENDERING LOOPS (60 FPS TARGET LERP PHYSICS)
// ============================================================
function renderLoop(now) {
  let dt = (now - lastFrameTime) / 1000.0;
  lastFrameTime = now;
  dt = Math.min(Math.max(dt, 0.001), 0.05);

  animT += dt * 1.6;
  arcAngle1 += dt * 0.95;
  arcAngle2 -= dt * 1.25;

  // 1. Arc Reactor
  renderArcReactor(dt);

  // 2. Harmonic Equalizer
  renderEqualizer(dt);

  // 3. Hexagon Radar Scanner
  renderRadar(dt);

  requestAnimationFrame(renderLoop);
}
requestAnimationFrame(renderLoop);

// --- Arc Reactor Canvas ---
function renderArcReactor(dt) {
  const w = reactorCanvas.width;
  const h = reactorCanvas.height;
  const cx = w / 2;
  const cy = h / 2;

  rCtx.clearRect(0, 0, w, h);

  // Crosshairs Axis
  rCtx.strokeStyle = "#071b30";
  rCtx.lineWidth = 1;
  rCtx.beginPath();
  rCtx.moveTo(cx, 10); rCtx.lineTo(cx, h - 10);
  rCtx.moveTo(10, cy); rCtx.lineTo(w - 10, cy);
  rCtx.stroke();

  // Color theme based on state
  let cRing = COLOR_CYAN;
  let cSec = COLOR_CYAN_DIM;
  if (currentState === "LISTENING") {
    cRing = COLOR_GOLD;
    cSec = "#fde047";
  } else if (currentState === "PROCESSING") {
    cRing = COLOR_PURPLE;
    cSec = "#d8b4fe";
  } else if (currentState === "SPEAKING") {
    cRing = COLOR_GREEN;
    cSec = "#6ee7b7";
  }

  // Outer Segmented Arcs (clockwise)
  const rOuter = Math.min(cx, cy) * 0.82;
  rCtx.lineWidth = 2.5;

  rCtx.strokeStyle = cRing;
  rCtx.beginPath();
  rCtx.arc(cx, cy, rOuter, arcAngle1, arcAngle1 + 1.3);
  rCtx.stroke();

  rCtx.strokeStyle = cSec;
  rCtx.lineWidth = 1.5;
  rCtx.beginPath();
  rCtx.arc(cx, cy, rOuter, arcAngle1 + 2.1, arcAngle1 + 2.9);
  rCtx.stroke();

  rCtx.strokeStyle = cRing;
  rCtx.lineWidth = 2.5;
  rCtx.beginPath();
  rCtx.arc(cx, cy, rOuter, arcAngle1 + 3.6, arcAngle1 + 5.2);
  rCtx.stroke();

  // Middle Segmented Arcs (counter-clockwise)
  const rMid = Math.min(cx, cy) * 0.58;
  rCtx.strokeStyle = cSec;
  rCtx.lineWidth = 2.0;
  rCtx.beginPath();
  rCtx.arc(cx, cy, rMid, arcAngle2, arcAngle2 + 1.9);
  rCtx.stroke();

  rCtx.strokeStyle = cRing;
  rCtx.lineWidth = 2.2;
  rCtx.beginPath();
  rCtx.arc(cx, cy, rMid, arcAngle2 + 2.8, arcAngle2 + 3.8);
  rCtx.stroke();

  rCtx.strokeStyle = cSec;
  rCtx.lineWidth = 1.5;
  rCtx.beginPath();
  rCtx.arc(cx, cy, rMid, arcAngle2 + 4.7, arcAngle2 + 5.4);
  rCtx.stroke();

  // Inner Glowing Ring
  const rInner = Math.min(cx, cy) * 0.36;
  rCtx.strokeStyle = cRing;
  rCtx.lineWidth = 2;
  rCtx.beginPath();
  rCtx.arc(cx, cy, rInner, 0, Math.PI * 2);
  rCtx.stroke();

  // Pulsing Core
  const pulse = Math.sin(animT * 2.8) * 3.5;
  const rCore = 14 + pulse;

  rCtx.strokeStyle = cSec;
  rCtx.lineWidth = 1;
  rCtx.beginPath();
  rCtx.arc(cx, cy, rCore + 8, 0, Math.PI * 2);
  rCtx.stroke();

  rCtx.fillStyle = cRing;
  rCtx.shadowColor = cRing;
  rCtx.shadowBlur = 14;
  rCtx.beginPath();
  rCtx.arc(cx, cy, rCore, 0, Math.PI * 2);
  rCtx.fill();
  rCtx.shadowBlur = 0;

  rCtx.fillStyle = COLOR_WHITE;
  rCtx.beginPath();
  rCtx.arc(cx, cy, 5, 0, Math.PI * 2);
  rCtx.fill();

  // Orbiting Sparkle Particles
  const dtScale = dt * 60.0;
  for (const p of particles) {
    p.cx = cx;
    p.cy = cy;
    p.update(dtScale);
    const pos = p.getPos();
    rCtx.fillStyle = p.color;
    rCtx.beginPath();
    rCtx.arc(pos.x, pos.y, p.size / 2, 0, Math.PI * 2);
    rCtx.fill();
  }
}

// --- Equalizer Canvas ---
function renderEqualizer(dt) {
  const w = eqCanvas.width;
  const h = eqCanvas.height;
  const cy = h / 2;

  eqCtx.clearRect(0, 0, w, h);

  const numBars = 32;
  const gap = 4;
  const barWidth = Math.max(4, (w - (numBars * gap)) / numBars);

  let ampMult = 0.38;
  let barColor = COLOR_CYAN;
  let capColor = COLOR_CYAN;
  let hasCaps = false;

  if (currentState === "LISTENING") {
    ampMult = 0.88;
    barColor = COLOR_GOLD;
    capColor = COLOR_CYAN;
    hasCaps = true;
  } else if (currentState === "PROCESSING") {
    ampMult = 0.68;
    barColor = COLOR_PURPLE;
    capColor = COLOR_CYAN;
    hasCaps = false;
  } else if (currentState === "SPEAKING") {
    ampMult = 0.96;
    barColor = COLOR_GREEN;
    capColor = COLOR_WHITE;
    hasCaps = true;
  }

  const totalW = numBars * barWidth + (numBars - 1) * gap;
  const startX = (w - totalW) / 2;
  const lerpRate = Math.min(1.0, 14.0 * dt);

  for (let i = 0; i < numBars; i++) {
    const norm = i / (numBars - 1);
    const envelope = Math.sin(norm * Math.PI);

    const wave1 = Math.sin(animT * 3.6 + i * 0.45);
    const wave2 = Math.cos(animT * 2.3 - i * 0.32);
    let targetH = (0.35 + 0.35 * wave1 + 0.30 * wave2) * envelope * ampMult;
    targetH = Math.max(0.08, Math.min(targetH, 0.95));

    spectrumHeights[i] += (targetH - spectrumHeights[i]) * lerpRate;
    const curH = spectrumHeights[i];

    const halfH = curH * (h * 0.42);
    const bx = startX + i * (barWidth + gap);
    const y1 = cy - halfH;
    const y2 = cy + halfH;

    // Bar Line
    eqCtx.strokeStyle = barColor;
    eqCtx.lineWidth = barWidth;
    eqCtx.lineCap = "round";
    eqCtx.beginPath();
    eqCtx.moveTo(bx, y1);
    eqCtx.lineTo(bx, y2);
    eqCtx.stroke();

    // Round Caps
    if (hasCaps) {
      eqCtx.fillStyle = capColor;
      eqCtx.beginPath();
      eqCtx.arc(bx, y1, 2, 0, Math.PI * 2);
      eqCtx.fill();

      eqCtx.beginPath();
      eqCtx.arc(bx, y2, 2, 0, Math.PI * 2);
      eqCtx.fill();
    }
  }
}

// --- Hexagon Radar Scanner Canvas ---
function renderRadar(dt) {
  radarAngle = (radarAngle + dt * 2.4) % (2 * Math.PI);
  const cx = 55;
  const cy = 55;

  radCtx.clearRect(0, 0, 110, 110);

  // Dim Axis Lines
  radCtx.strokeStyle = "#0a2a47";
  radCtx.lineWidth = 1;
  radCtx.beginPath();
  radCtx.moveTo(10, cy); radCtx.lineTo(100, cy);
  radCtx.moveTo(cx, 10); radCtx.lineTo(cx, 100);
  radCtx.stroke();

  // Target Circle
  radCtx.strokeStyle = COLOR_CYAN_DIM;
  radCtx.lineWidth = 1.2;
  radCtx.beginPath();
  radCtx.arc(cx, cy, 38, 0, Math.PI * 2);
  radCtx.stroke();

  // Inscribed Hexagon
  const rHex = 28;
  radCtx.strokeStyle = COLOR_CYAN;
  radCtx.lineWidth = 1.5;
  radCtx.beginPath();
  for (let i = 0; i < 6; i++) {
    const ang = (Math.PI / 3) * i - Math.PI / 6;
    const hx = cx + rHex * Math.cos(ang);
    const hy = cy + rHex * Math.sin(ang);
    if (i === 0) radCtx.moveTo(hx, hy);
    else radCtx.lineTo(hx, hy);
  }
  radCtx.closePath();
  radCtx.stroke();

  // Sweeping Radar Beam
  const rx = cx + 36 * Math.cos(radarAngle);
  const ry = cy + 36 * Math.sin(radarAngle);
  radCtx.strokeStyle = COLOR_CYAN;
  radCtx.lineWidth = 1.5;
  radCtx.beginPath();
  radCtx.moveTo(cx, cy);
  radCtx.lineTo(rx, ry);
  radCtx.stroke();

  // Central Red Node
  radCtx.fillStyle = COLOR_ROSE;
  radCtx.beginPath();
  radCtx.arc(cx, cy, 5, 0, Math.PI * 2);
  radCtx.fill();
}

// ============================================================
// 3. HEADER CLOCK & GREETING (MATCHING main.py)
// ============================================================
function updateHeader() {
  const now = new Date();
  const hr = now.getHours();

  let greet = "GOOD MORNING";
  let icon = "☀️";
  if (hr >= 12 && hr < 17) {
    greet = "GOOD AFTERNOON";
    icon = "⛅";
  } else if (hr >= 17) {
    greet = "GOOD EVENING";
    icon = "🌙";
  }

  const days = ["SUNDAY", "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY"];
  const months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
  const dayStr = `${days[now.getDay()]} // ${months[now.getMonth()]} ${String(now.getDate()).padStart(2, "0")}, ${now.getFullYear()}`;

  greetingLabel.textContent = `${greet} // ROOT: NIMISH ${icon}   |   ${dayStr}`;

  let displayHours = hr % 12 || 12;
  const ampm = hr >= 12 ? "PM" : "AM";
  const mins = String(now.getMinutes()).padStart(2, "0");
  const secs = String(now.getSeconds()).padStart(2, "0");
  clockLabel.textContent = `[ ${String(displayHours).padStart(2, "0")}:${mins}:${secs} ${ampm} ]`;
}
setInterval(updateHeader, 1000);
updateHeader();

// ============================================================
// 4. STATE MANAGEMENT (MATCHING main.py)
// ============================================================
function setSystemState(stateName) {
  currentState = stateName;
  statusPill.className = "status-pill";

  if (stateName === "LISTENING") {
    statusPill.classList.add("listening");
    statusLabel.textContent = "● LISTENING...";
    moodLabel.textContent = "[ STATUS: LISTENING... SPEAK NOW ]";
    moodLabel.style.color = COLOR_GOLD;
    btnListen.classList.add("listening");
    btnListen.textContent = "🎙️   LISTENING...";
  } else if (stateName === "PROCESSING") {
    statusPill.classList.add("processing");
    statusLabel.textContent = "● PROCESSING...";
    moodLabel.textContent = "[ MOOD: THINKING // REASONING ◆ ]";
    moodLabel.style.color = COLOR_PURPLE;
    btnListen.classList.remove("listening");
    btnListen.textContent = "🎙️   TAP TO SPEAK [LISTEN]";
  } else if (stateName === "SPEAKING") {
    statusPill.classList.add("speaking");
    statusLabel.textContent = "● VOCALIZING...";
    moodLabel.textContent = "[ MOOD: SPEAKING // AUDIO ACTIVE ◆ ]";
    moodLabel.style.color = COLOR_GREEN;
    btnListen.classList.remove("listening");
    btnListen.textContent = "🎙️   TAP TO SPEAK [LISTEN]";
  } else {
    // STANDBY
    statusLabel.textContent = "● STANDBY";
    moodLabel.textContent = "[ MOOD: READY // CALM ATTENTIVE ◆ ]";
    moodLabel.style.color = COLOR_CYAN;
    btnListen.classList.remove("listening");
    btnListen.textContent = "🎙️   TAP TO SPEAK [LISTEN]";
  }
}

// ============================================================
// 5. TERMINAL LOGGING (MATCHING main.py EXACT TEXT TAGS)
// ============================================================
function getTimestamp() {
  const d = new Date();
  return `[${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}:${String(d.getSeconds()).padStart(2, "0")}]`;
}

function logUserCommand(cmdText) {
  const tStr = getTimestamp();
  const line = document.createElement("div");
  line.className = "term-line";
  line.innerHTML = `<span class="line-time">${tStr} [USER @ TERMINAL] &gt; </span><span class="line-user">You: ${escapeHtml(cmdText)}</span>`;
  terminalBox.appendChild(line);

  const moodDiv = document.createElement("div");
  moodDiv.className = "term-line line-mood";
  moodDiv.textContent = "  🗩 [MOOD: STANDBY] Calm, attentive, and ready.";
  terminalBox.appendChild(moodDiv);

  scrollTerminal();
}

function logKernelExec(toolName, argsDict) {
  const line = document.createElement("div");
  line.className = "term-line line-exec";
  let text = String(toolName || "").trim();
  if (argsDict && typeof argsDict === "object" && Object.keys(argsDict).length > 0 && !text.includes("| args:")) {
    text += ` | args: ${JSON.stringify(argsDict)}`;
  }
  line.textContent = `  ⚡ [KERNEL // EXEC] ${text}`;
  terminalBox.appendChild(line);
  scrollTerminal();
}

function logResponse(responseText) {
  const tStr = getTimestamp();
  const line = document.createElement("div");
  line.className = "term-line";
  line.innerHTML = `<span class="line-time">${tStr} [MAYA // RESPONSE] &gt; </span><span class="line-response">${escapeHtml(responseText)}</span>`;
  terminalBox.appendChild(line);
  scrollTerminal();
}

function logRaw(msg, type = "sys") {
  const line = document.createElement("div");
  line.className = `term-line line-${type}`;
  line.textContent = msg;
  terminalBox.appendChild(line);
  scrollTerminal();
}

function scrollTerminal() {
  terminalBox.scrollTop = terminalBox.scrollHeight;
}

function purgeDialogue() {
  terminalBox.innerHTML = "";
  logRaw(`${getTimestamp()} [KERNEL] Dialogue stream purged.`, "sys");
}

function escapeHtml(text) {
  return String(text).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// ============================================================
// 6. COMMAND DISPATCH (MATCHING main.py)
// ============================================================
async function dispatchCommand(query) {
  if (!query || !query.trim()) return;

  logUserCommand(query);
  setSystemState("PROCESSING");

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: query, mute_tts: ttsMuted })
    });

    if (!res.ok) throw new Error(`HTTP Error ${res.status}`);
    const data = await res.json();

    // Update dynamic mood if provided
    if (data.mood) {
      moodLabel.textContent = `[ MOOD: ${data.mood} ◆ ]`;
    }

    // Log any kernel executions
    if (data.tools && Array.isArray(data.tools)) {
      data.tools.forEach(tool => {
        logKernelExec(tool);
      });
    }

    const reply = data.reply || "Directive executed successfully.";
    logResponse(reply);

    // If an image was generated, show media preview
    if (data.image_url) {
      showMediaPreview(data.image_url, query);
    }

    // Single voice playback:
    // Plays Maya's Neural Voice directly in the browser with 0 repetition!
    if (!ttsMuted) {
      if (data.audio_url) {
        playNeuralAudio(data.audio_url, reply);
      } else {
        speak(reply);
      }
    } else {
      setSystemState("STANDBY");
    }
  } catch (err) {
    console.error("Execution error:", err);
    logRaw(`  ⚠ Execution error: ${err.message}`, "warn");
    setSystemState("STANDBY");
  }
}

function showMediaPreview(url, prompt) {
  generatedImg.src = url;
  mediaTitle.textContent = `Generated: ${prompt}`;
  mediaPreviewBox.style.display = "block";
  scrollTerminal();
}

function submitCommand() {
  const q = commandEntry.value.trim();
  if (q) {
    commandEntry.value = "";
    dispatchCommand(q);
  }
}

commandEntry.addEventListener("keydown", (e) => {
  if (e.key === "Enter") submitCommand();
});

function dispatchCmd(cmdText) {
  dispatchCommand(cmdText);
}

// ============================================================
// 7. MULTILINGUAL SPEECH RECOGNITION & SYNTHESIS
// ============================================================
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
let isVoiceListening = false;

const SUPPORTED_VOICE_LANGS = [
  { code: "en-IN", label: "EN (India)" },
  { code: "gu-IN", label: "ગુજરાતી (GU)" },
  { code: "hi-IN", label: "हिन्दी (HI)" },
  { code: "en-US", label: "EN (US)" }
];
let currentVoiceLangIndex = 0; // Default Indian English

function cycleVoiceLanguage() {
  currentVoiceLangIndex = (currentVoiceLangIndex + 1) % SUPPORTED_VOICE_LANGS.length;
  const l = SUPPORTED_VOICE_LANGS[currentVoiceLangIndex];
  if (recognition) {
    recognition.lang = l.code;
  }
  const btnLang = document.getElementById("btnVoiceLang");
  if (btnLang) {
    btnLang.textContent = `🌐 ${l.label}`;
  }
  logRaw(`[SYS] Speech Recognition set to ${l.label} (${l.code})`, "sys");
}

if (SpeechRecognition) {
  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = SUPPORTED_VOICE_LANGS[currentVoiceLangIndex].code;

  recognition.onstart = () => {
    isVoiceListening = true;
    setSystemState("LISTENING");
  };

  recognition.onresult = (e) => {
    const speech = e.results[0][0].transcript;
    if (speech) {
      dispatchCommand(speech);
    }
  };

  recognition.onerror = () => {
    isVoiceListening = false;
    setSystemState("STANDBY");
  };

  recognition.onend = () => {
    isVoiceListening = false;
    if (currentState === "LISTENING") {
      setSystemState("STANDBY");
    }
  };
}

function toggleVoiceListen() {
  if (!recognition) {
    alert("Speech recognition not supported in this browser. Please use Chrome or Edge.");
    return;
  }
  if (isVoiceListening) {
    recognition.stop();
  } else {
    try {
      recognition.start();
    } catch (e) {
      console.warn("Speech recognition error:", e);
    }
  }
}

let currentAudio = null;

function stopAllAudio() {
  if (currentAudio) {
    try {
      currentAudio.pause();
      currentAudio.currentTime = 0;
    } catch (e) {}
    currentAudio = null;
  }
  if (window.speechSynthesis) {
    try {
      window.speechSynthesis.cancel();
    } catch (e) {}
  }
}

function playNeuralAudio(audioUrl, fallbackText) {
  if (ttsMuted) {
    setSystemState("STANDBY");
    return;
  }

  stopAllAudio();
  setSystemState("SPEAKING");

  currentAudio = new Audio(audioUrl);

  currentAudio.onplay = () => {
    setSystemState("SPEAKING");
  };

  currentAudio.onended = () => {
    currentAudio = null;
    setSystemState("STANDBY");
  };

  currentAudio.onerror = (err) => {
    console.warn("Audio playback error, falling back to browser speech synthesis:", err);
    currentAudio = null;
    speak(fallbackText);
  };

  currentAudio.play().catch((err) => {
    console.warn("Autoplay policy or decode error, falling back:", err);
    speak(fallbackText);
  });
}

function speak(text) {
  if (ttsMuted || !window.speechSynthesis) {
    setSystemState("STANDBY");
    return;
  }

  stopAllAudio();
  setSystemState("SPEAKING");

  const clean = text.replace(/[*#`_~]/g, "").slice(0, 320);
  const utterance = new SpeechSynthesisUtterance(clean);
  utterance.rate = 1.05;

  const voices = window.speechSynthesis.getVoices();
  const isGu = /[\u0A80-\u0AFF]/.test(clean);
  const isHi = /[\u0900-\u097F]/.test(clean);
  let v = null;
  if (isGu) {
    v = voices.find(x => x.lang.includes("gu") || x.name.toLowerCase().includes("dhwani") || x.name.toLowerCase().includes("gujarati"));
  } else if (isHi) {
    v = voices.find(x => x.lang.includes("hi") || x.name.toLowerCase().includes("swara") || x.name.toLowerCase().includes("hindi") || x.name.toLowerCase().includes("kalpana"));
  }
  if (!v) {
    v = voices.find(x => x.lang.includes("en-IN") || x.name.includes("Neerja") || x.name.includes("Zira")) || voices[0];
  }
  if (v) utterance.voice = v;

  utterance.onend = () => setSystemState("STANDBY");
  utterance.onerror = () => setSystemState("STANDBY");

  window.speechSynthesis.speak(utterance);
}

function toggleMuteTTS() {
  ttsMuted = !ttsMuted;
  if (ttsMuted) {
    btnMute.textContent = "▣ TTS MUTED";
    btnMute.classList.add("muted");
    stopAllAudio();
    setSystemState("STANDBY");
  } else {
    btnMute.textContent = "▢ MUTE TTS";
    btnMute.classList.remove("muted");
  }
}

// Live Telemetry updates (Real PC Metrics via psutil)
async function updateLiveTelemetry() {
  try {
    const res = await fetch("/api/telemetry");
    if (res.ok) {
      const data = await res.json();
      if (data.cpu_percent !== undefined) {
        cpuLabel.textContent = `CPU: ${data.cpu_percent}%`;
      }
      if (data.ram_percent !== undefined) {
        ramLabel.textContent = `RAM: ${data.ram_percent}%`;
      }
      if (data.tools_registered !== undefined) {
        const toolsPill = document.querySelector(".top-pill-cyan");
        if (toolsPill) toolsPill.textContent = `◈ TOOLS: ${data.tools_registered} LOADED`;
      }
    }
  } catch (e) {
    // network fallback
  }
}
setInterval(updateLiveTelemetry, 2500);
updateLiveTelemetry();


// ============================================================
// TOOL ARSENAL MODAL (198 REGISTERED TOOLS EXPLORER & RUNNER)
// ============================================================
let allRegisteredTools = [];
let activeCategory = "ALL";
let activeSearchQuery = "";

const toolsModalOverlay = document.getElementById("toolsModalOverlay");
const btnOpenArsenal = document.getElementById("btnOpenArsenal");
const btnCloseModal = document.getElementById("btnCloseModal");
const searchToolsInput = document.getElementById("searchToolsInput");
const toolsGridContainer = document.getElementById("toolsGridContainer");
const toolCountBadge = document.getElementById("toolCountBadge");
const categoryTabs = document.getElementById("categoryTabs");

if (btnOpenArsenal) {
  btnOpenArsenal.addEventListener("click", () => {
    toolsModalOverlay.classList.add("active");
    if (allRegisteredTools.length === 0) {
      loadAllTools();
    }
  });
}

if (btnCloseModal) {
  btnCloseModal.addEventListener("click", () => {
    toolsModalOverlay.classList.remove("active");
  });
}

if (toolsModalOverlay) {
  toolsModalOverlay.addEventListener("click", (e) => {
    if (e.target === toolsModalOverlay) {
      toolsModalOverlay.classList.remove("active");
    }
  });
}

async function loadAllTools() {
  try {
    if (toolsGridContainer) {
      toolsGridContainer.innerHTML = `<div class="loading-tools">⚡ Synchronizing 198 System Tools from Neural Kernel...</div>`;
    }
    const res = await fetch("/api/tools");
    if (res.ok) {
      const data = await res.json();
      allRegisteredTools = data.tools || [];
      if (toolCountBadge) toolCountBadge.textContent = allRegisteredTools.length;
      if (btnOpenArsenal) btnOpenArsenal.textContent = `◈ TOOL ARSENAL [${allRegisteredTools.length}]`;
      renderTools();
    } else {
      if (toolsGridContainer) {
        toolsGridContainer.innerHTML = `<div class="loading-tools" style="color:var(--color-rose);">Failed to retrieve tool manifest.</div>`;
      }
    }
  } catch (err) {
    if (toolsGridContainer) {
      toolsGridContainer.innerHTML = `<div class="loading-tools" style="color:var(--color-rose);">Network error loading tools: ${err}</div>`;
    }
  }
}

function renderTools() {
  if (!toolsGridContainer) return;

  const filtered = allRegisteredTools.filter(tool => {
    const matchesCat = (activeCategory === "ALL" || tool.category === activeCategory);
    const q = activeSearchQuery.toLowerCase().trim();
    const matchesQuery = !q || tool.name.toLowerCase().includes(q) || tool.description.toLowerCase().includes(q);
    return matchesCat && matchesQuery;
  });

  if (filtered.length === 0) {
    toolsGridContainer.innerHTML = `<div class="loading-tools" style="color:var(--txt-muted);">No tools found matching query "${activeSearchQuery}".</div>`;
    return;
  }

  toolsGridContainer.innerHTML = filtered.map(tool => {
    const paramsText = tool.parameters && tool.parameters.length > 0 
      ? `args: (${tool.parameters.join(", ")})` 
      : "zero-args (instant)";

    return `
      <div class="tool-item-card">
        <div class="tool-top-row">
          <div class="tool-name-label">⚙️ ${tool.name}</div>
          <span class="tool-cat-badge">${tool.category}</span>
        </div>
        <div class="tool-desc-text" title="${tool.full_doc.replace(/"/g, '&quot;')}">${tool.description}</div>
        <div class="tool-bottom-row">
          <span class="tool-params-label">${paramsText}</span>
          <button class="btn-run-tool" onclick="executeToolByName('${tool.name}', ${JSON.stringify(tool.parameters || [])})">⚡ RUN TOOL</button>
        </div>
      </div>
    `;
  }).join("");
}

// Category tabs click listener
if (categoryTabs) {
  categoryTabs.addEventListener("click", (e) => {
    const tabBtn = e.target.closest(".tab-btn");
    if (!tabBtn) return;
    categoryTabs.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    tabBtn.classList.add("active");
    activeCategory = tabBtn.getAttribute("data-cat") || "ALL";
    renderTools();
  });
}

// Live search input listener
if (searchToolsInput) {
  searchToolsInput.addEventListener("input", (e) => {
    activeSearchQuery = e.target.value;
    renderTools();
  });
}

// Direct tool execution runner
async function executeToolByName(toolName, paramList) {
  if (paramList && paramList.length > 0) {
    // If tool requires arguments, prefill the input dock for the user
    toolsModalOverlay.classList.remove("active");
    commandEntry.value = `maya ${toolName.replace(/_/g, " ")} `;
    commandEntry.focus();
    logRaw(`[TOOL SELECTION] Ready to execute ${toolName}. Please complete any parameters and press Enter.`, "sys");
    return;
  }

  // Zero-arg instant tool execution
  logKernelExec(`${toolName} | args: {}`);
  setSystemState("PROCESSING");
  
  try {
    const res = await fetch("/api/execute_tool", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tool_name: toolName, args: {} })
    });
    
    if (res.ok) {
      const data = await res.json();
      toolsModalOverlay.classList.remove("active");
      const reply = data.result || "Tool executed successfully.";
      logResponse(reply);
      setSystemState("SPEAKING");
      setTimeout(() => setSystemState("STANDBY"), 3000);
    } else {
      logRaw(`Tool execution failed with status: ${res.status}`, "warn");
      setSystemState("STANDBY");
    }
  } catch (err) {
    logRaw(`Tool execution network error: ${err}`, "warn");
    setSystemState("STANDBY");
  }
}

// Load tools on boot in background so they are ready instantly
loadAllTools();
