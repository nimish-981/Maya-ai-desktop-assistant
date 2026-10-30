/* ==========================================================================
   MAYA HOLOGRAPHIC AI ASSISTANT - APPLICATION LOGIC & HUD CONTROLLER
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    initParticles();
    initSparklines();
    initTelemetryLoop();
    initChatHandlers();
});

/* ================= 1. CYBER DUST PARTICLE CANVAS ================= */

function initParticles() {
    const canvas = document.getElementById('particle-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener('resize', resize);

    const particles = [];
    const count = 55;

    for (let i = 0; i < count; i++) {
        particles.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            size: Math.random() * 2.2 + 0.8,
            speedY: -(Math.random() * 0.7 + 0.2),
            speedX: (Math.random() - 0.5) * 0.35,
            opacity: Math.random() * 0.6 + 0.2,
            color: Math.random() > 0.4 ? 'rgba(0, 240, 255, ' : 'rgba(168, 85, 247, '
        });
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        particles.forEach(p => {
            p.y += p.speedY;
            p.x += p.speedX;

            if (p.y < 0) {
                p.y = canvas.height + 10;
                p.x = Math.random() * canvas.width;
            }

            ctx.fillStyle = p.color + p.opacity + ')';
            ctx.shadowBlur = 8;
            ctx.shadowColor = p.color + '0.8)';
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fill();
        });

        requestAnimationFrame(animate);
    }
    animate();
}

/* ================= 2. SPARKLINES CHART SYSTEM ================= */

const sparkHistory = {
    cpu: [18, 22, 20, 25, 23, 28, 24, 21, 23],
    ram: [62, 64, 65, 63, 65, 66, 64, 65, 65],
    disk: [42, 42, 42, 42, 42, 42, 42, 42, 42]
};

function drawSparkline(canvasId, data, colorStroke, colorFill) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;

    ctx.clearRect(0, 0, w, h);

    const min = 0;
    const max = 100;
    const step = w / (data.length - 1);

    ctx.beginPath();
    data.forEach((val, i) => {
        const x = i * step;
        const y = h - ((val - min) / (max - min)) * (h - 6) - 3;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });

    ctx.strokeStyle = colorStroke;
    ctx.lineWidth = 1.8;
    ctx.shadowBlur = 6;
    ctx.shadowColor = colorStroke;
    ctx.stroke();

    // Area fill
    ctx.lineTo(w, h);
    ctx.lineTo(0, h);
    ctx.closePath();
    ctx.fillStyle = colorFill;
    ctx.shadowBlur = 0;
    ctx.fill();
}

function initSparklines() {
    drawSparkline('spark-cpu', sparkHistory.cpu, '#00f0ff', 'rgba(0, 240, 255, 0.12)');
    drawSparkline('spark-ram', sparkHistory.ram, '#a78bfa', 'rgba(167, 139, 250, 0.12)');
    drawSparkline('spark-disk', sparkHistory.disk, '#f59e0b', 'rgba(245, 158, 11, 0.12)');
}

/* ================= 3. TELEMETRY & LIVE RADIAL GAUGES ================= */

function updateRadialGauge(dialElement, percent, colorClass) {
    if (!dialElement) return;
    const circle = dialElement.querySelector('.gauge-fill');
    const valText = dialElement.querySelector('.gauge-val');
    if (circle) {
        const circumference = 251.2;
        const offset = circumference - (percent / 100) * circumference;
        circle.style.strokeDashoffset = offset;
    }
    if (valText) {
        valText.textContent = Math.round(percent) + '%';
    }
}

function initTelemetryLoop() {
    setInterval(() => {
        // Minor realistic fluctuations for visual feedback
        const cpuJitter = Math.floor(Math.sin(Date.now() / 2000) * 4 + 23);
        const ramJitter = Math.floor(Math.cos(Date.now() / 3000) * 1.5 + 65);

        // Update radial gauges
        const dials = document.querySelectorAll('.dial-item');
        if (dials[0]) updateRadialGauge(dials[0].querySelector('.radial-gauge'), cpuJitter);
        if (dials[1]) updateRadialGauge(dials[1].querySelector('.radial-gauge'), ramJitter);

        // Update header & labels
        const hdrCpu = document.getElementById('hdr-cpu');
        const hdrRam = document.getElementById('hdr-ram');
        const sparkCpuVal = document.getElementById('spark-cpu-val');
        const sparkRamVal = document.getElementById('spark-ram-val');

        if (hdrCpu) hdrCpu.textContent = `CPU ${cpuJitter}%`;
        if (hdrRam) hdrRam.textContent = `RAM ${ramJitter}%`;
        if (sparkCpuVal) sparkCpuVal.textContent = `${cpuJitter}%`;
        if (sparkRamVal) sparkRamVal.textContent = `${ramJitter}%`;

        // Push to sparkline history
        sparkHistory.cpu.push(cpuJitter);
        sparkHistory.cpu.shift();
        sparkHistory.ram.push(ramJitter);
        sparkHistory.ram.shift();

        initSparklines();
    }, 2200);
}

/* ================= 4. CHAT INTERACTION & PYWEBVIEW BRIDGE ================= */

function initChatHandlers() {
    const input = document.getElementById('chat-input');
    const sendBtn = document.getElementById('btn-chat-send');
    const micBtn = document.getElementById('btn-chat-mic');
    const headerMic = document.getElementById('btn-header-mic');

    if (sendBtn) {
        sendBtn.addEventListener('click', () => submitChat());
    }
    if (input) {
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') submitChat();
        });
    }

    if (micBtn) micBtn.addEventListener('click', triggerVoiceListen);
    if (headerMic) headerMic.addEventListener('click', triggerVoiceListen);
}

function submitChat() {
    const input = document.getElementById('chat-input');
    if (!input) return;
    const text = input.value.trim();
    if (!text) return;

    appendUserMessage(text);
    input.value = '';

    // Route command to Python desktop bridge if running via run_desktop_app.py
    if (window.pywebview && window.pywebview.api && window.pywebview.api.send_command) {
        window.pywebview.api.send_command(text);
        setMayaState('THINKING', 'PROCESSING...');
    } else {
        // In standalone browser mode, provide intelligent simulated response
        setMayaState('THINKING', 'PROCESSING...');
        setTimeout(() => {
            const replies = [
                `Executing: "${text}". All subsystems responded with code 200 OK.`,
                `Got it! I am processing "${text}" with NVIDIA Nemotron-70B.`,
                `Task complete. Your system health is nominal and memory vault updated.`,
                `જરૂર! હું તમારો કમાન્ડ "${text}" પૂર્ણ કરી રહી છું.`
            ];
            const chosen = replies[Math.floor(Math.random() * replies.length)];
            appendAssistantMessage(chosen);
            setMayaState('IDLE', 'STANDBY');
            addTerminalLog(`Executed tool call for "${text}"`, 'sys');
        }, 800);
    }
}

function appendUserMessage(text) {
    const stream = document.getElementById('chat-stream');
    if (!stream) return;

    const div = document.createElement('div');
    div.className = 'msg-bubble user-bubble';
    div.innerHTML = `
        <div class="bubble-header">
            <span class="avatar-dot" style="background:#00f0ff;box-shadow:0 0 6px #00f0ff;"></span>
            <span class="sender-name" style="color:#7dd3fc;">NIMISH</span>
        </div>
        <div class="bubble-content">${escapeHTML(text)}</div>
    `;
    stream.appendChild(div);
    stream.scrollTop = stream.scrollHeight;
}

function appendAssistantMessage(text) {
    const stream = document.getElementById('chat-stream');
    if (!stream) return;

    const div = document.createElement('div');
    div.className = 'msg-bubble assistant-bubble';
    div.innerHTML = `
        <div class="bubble-header">
            <span class="avatar-dot"></span>
            <span class="sender-name">MAYA</span>
        </div>
        <div class="bubble-content">${escapeHTML(text)}</div>
    `;
    stream.appendChild(div);
    stream.scrollTop = stream.scrollHeight;
}

function sendSuggestion(text) {
    const input = document.getElementById('chat-input');
    if (input) {
        input.value = text;
        submitChat();
    }
}

function triggerVoiceListen() {
    setMayaState('LISTENING', 'LISTENING...');
    addTerminalLog('Listening for speech input...', 'sys');

    if (window.pywebview && window.pywebview.api && window.pywebview.api.trigger_listen) {
        window.pywebview.api.trigger_listen();
    } else {
        // Fallback Web Speech Recognition if available in Chrome/Edge
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
            const rec = new SpeechRec();
            rec.lang = 'en-US';
            rec.onresult = (e) => {
                const transcript = e.results[0][0].transcript;
                appendUserMessage(transcript);
                setMayaState('THINKING', 'PROCESSING...');
                setTimeout(() => {
                    appendAssistantMessage(`Heard command: "${transcript}". Executing right away.`);
                    setMayaState('IDLE', 'STANDBY');
                }, 700);
            };
            rec.onerror = () => setMayaState('IDLE', 'STANDBY');
            rec.start();
        } else {
            setTimeout(() => {
                setMayaState('IDLE', 'STANDBY');
            }, 2000);
        }
    }
}

/* ================= 5. SHORTCUTS & ACTION DISPATCHER ================= */

function executeQuickAction(action) {
    const actionsMap = {
        'update_system': {
            cmd: 'Check and update system packages',
            log: 'Running Windows Update & Python package integrity check...'
        },
        'clean_cache': {
            cmd: 'Clean temporary junk files and cache',
            log: 'Cleaning user temp files, DNS cache, and recycling bin...'
        },
        'system_info': {
            cmd: 'Show detailed system overview and specs',
            log: 'Generating neofetch hardware and kernel summary...'
        },
        'smart_backup': {
            cmd: 'Backup memory vault to secure cloud storage',
            log: 'Encrypting and saving snapshot of maya_history.db...'
        }
    };

    const target = actionsMap[action];
    if (!target) return;

    addTerminalLog(target.log, 'sys');
    addLogEntry('[INFO] ' + target.log, 'info');

    if (window.pywebview && window.pywebview.api && window.pywebview.api.send_command) {
        window.pywebview.api.send_command(target.cmd);
    } else {
        appendUserMessage(target.cmd);
        setMayaState('THINKING', 'PROCESSING...');
        setTimeout(() => {
            appendAssistantMessage(`Action "${action}" completed successfully.`);
            setMayaState('IDLE', 'STANDBY');
        }, 700);
    }
}

/* ================= 6. DESKTOP BRIDGE HOOKS (window.setMayaState & logs) ================= */

window.setMayaState = function(state, text) {
    const indicator = document.getElementById('ai-status-indicator');
    if (indicator) {
        indicator.textContent = text || state;
        if (state === 'LISTENING') indicator.style.color = '#ffd700';
        else if (state === 'THINKING') indicator.style.color = '#a855f7';
        else if (state === 'SPEAKING') indicator.style.color = '#00ffaa';
        else indicator.style.color = '#00f0ff';
    }

    // Voice waves animation boost
    const waves = document.getElementById('voice-waves');
    if (waves) {
        if (state === 'SPEAKING' || state === 'LISTENING') {
            waves.style.opacity = '1';
        } else {
            waves.style.opacity = '0.4';
        }
    }
};

window.addTerminalLog = function(msg, logType) {
    const termLogs = document.getElementById('term-logs');
    if (!termLogs) return;

    const row = document.createElement('div');
    row.className = 'log-line';
    const now = new Date().toTimeString().split(' ')[0];

    let color = '#94a3b8';
    if (logType === 'user') color = '#38bdf8';
    if (logType === 'sys') color = '#00f0ff';
    if (msg.includes('Maya:')) color = '#c4b5fd';

    row.innerHTML = `<span style="color:#64748b;">[${now}]</span> <span style="color:${color};">${escapeHTML(msg)}</span>`;
    termLogs.appendChild(row);

    const termBody = document.getElementById('terminal-content');
    if (termBody) termBody.scrollTop = termBody.scrollHeight;
};

function addLogEntry(text, type) {
    const logsContainer = document.getElementById('logs-container');
    if (!logsContainer) return;

    const now = new Date().toTimeString().split(' ')[0];
    const div = document.createElement('div');
    div.className = 'log-entry';
    div.innerHTML = `<span class="log-ts">${now}</span> <span class="badge ${type}">[${type.toUpperCase()}]</span> ${escapeHTML(text)}`;
    logsContainer.prepend(div);
}

function escapeHTML(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
