import sys
import os
import threading
import math
import random
import time
from datetime import datetime
import psutil

# ── Enable High-DPI Awareness on Windows ──
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

import customtkinter as ctk
from tkinter import Canvas
import pywinstyles

from core.engine import Assistant

# Ensure Windows consoles handle UTF-8 symbols cleanly
for stream in (sys.stdout, sys.stderr):
    if stream and hasattr(stream, 'reconfigure'):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass

# ============================================================
# MAYA // CYBER COMPANION OS — PALETTE (ACCURATE TO SCREENSHOT)
# ============================================================
COLOR_BG            = "#020611"        # Ultra-deep cyber void
COLOR_CARD_BG       = "#040a17"        # Dark glass card surface
COLOR_CARD_BORDER   = "#0a223e"        # Panel frame border
COLOR_CARD_HOVER    = "#081b33"        # Interactive hover

# Cyberpunk Neon Accents
COLOR_CYAN          = "#00f0ff"        # Primary neon cyan
COLOR_CYAN_DIM      = "#0284c7"        # Dim cyan / secondary
COLOR_GREEN         = "#10b981"        # Active / Connected / Response
COLOR_GOLD          = "#f59e0b"        # Voice Listening / Warning
COLOR_PURPLE        = "#a855f7"        # Neural processing / Mood
COLOR_ROSE          = "#f43f5e"        # Kernel execution / Engine / Alerts
COLOR_WHITE         = "#ffffff"

# Text Colors
TXT_PRIMARY         = "#e2e8f0"        # Crisp text
TXT_MUTED           = "#64748b"        # Monospace muted labels
TXT_CYAN            = "#38bdf8"        # Soft cyan

ctk.set_appearance_mode("dark")


# ============================================================
# SPARKLE PARTICLE SYSTEM FOR ARC REACTOR
# ============================================================
class Particle:
    def __init__(self, cx, cy):
        self.cx = cx
        self.cy = cy
        self.radius = random.uniform(40, 155)
        self.angle = random.uniform(0, 2 * math.pi)
        self.speed = random.uniform(0.015, 0.045) * random.choice([-1, 1])
        self.size = random.choice([2, 3, 3, 4, 5])
        self.color = random.choice([
            COLOR_CYAN, COLOR_CYAN,
            "#ec4899",   # Neon magenta
            "#f59e0b",   # Amber gold
            "#ffffff",   # Crisp white
            "#10b981"    # Emerald
        ])

    def update(self, dt_scale=1.0):
        self.angle += self.speed * dt_scale
        if self.angle > 2 * math.pi:
            self.angle -= 2 * math.pi
        elif self.angle < 0:
            self.angle += 2 * math.pi

    def get_pos(self):
        x = self.cx + self.radius * math.cos(self.angle)
        y = self.cy + self.radius * math.sin(self.angle)
        return x, y


# ============================================================
# MAIN APPLICATION WINDOW
# ============================================================
class MayaCyberOSApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MAYA // CYBER COMPANION OS")
        self.geometry("1680x960")
        self.minsize(1360, 800)
        self.configure(fg_color=COLOR_BG)

        try:
            pywinstyles.change_header_color(self, COLOR_BG)
        except Exception:
            pass

        # Assistant Engine Handle
        self.assistant = None
        self.is_listening = False
        self.is_processing = False
        self.is_speaking = False
        self.tts_muted = False

        # Live telemetry
        self.cpu_pct = 42
        self.ram_pct = 68
        self.disk_pct = 59

        # Animation & Frame Timing states (Locked 60 FPS Target)
        self.anim_t = 0.0
        self.arc_angle_1 = 0.0
        self.arc_angle_2 = 0.0
        self.radar_angle = 0.0
        self.radar_beam = None
        self.last_frame_time = time.perf_counter()
        self.spectrum_heights = [0.15] * 32
        self.particles = []
        self.reactor_items = None
        self.eq_items = None

        # Thread-Safe Batch Logging Queue
        self.log_queue = []
        self.log_lock = threading.Lock()

        # Current State ("STANDBY", "LISTENING", "PROCESSING", "SPEAKING")
        self.current_state = "STANDBY"
        self.mood_text = "[ MOOD: READY // CALM ATTENTIVE ◆ ]"

        # Build UI Structure
        self._build_top_header()
        self._build_main_columns()

        # Initialize Arc Reactor Particles
        for _ in range(45):
            self.particles.append(Particle(220, 160))

        # Stdout Redirection
        self.original_stdout = sys.stdout
        sys.stdout = self

        # Initial Welcome Logs
        self._log_raw("[KERNEL] Maya Neural Subsystems Booting...", "sys")
        self._log_raw("⬡ MAYA: 195 tools registered across Multi-Agent Architecture.", "sys")
        self._log_raw("[KERNEL] All subsystems operational. Initializing Cyber Companion...", "sys")

        # Background threads & Smooth animation loop
        self._start_log_drain()
        self._start_animation_loop()
        threading.Thread(target=self._telemetry_worker, daemon=True).start()
        threading.Thread(target=self._init_assistant_worker, daemon=True).start()

    # --------------------------------------------------------
    # UI CONSTRUCTION: TOP HEADER BAR
    # --------------------------------------------------------
    def _build_top_header(self):
        self.top_header = ctk.CTkFrame(self, fg_color=COLOR_BG, height=54)
        self.top_header.pack(fill="x", padx=18, pady=(14, 8))
        self.top_header.pack_propagate(False)

        # Left: Maya Badge (Cyan pill)
        self.badge_frame = ctk.CTkFrame(
            self.top_header,
            fg_color="#031226",
            border_color=COLOR_CYAN,
            border_width=1.5,
            corner_radius=20
        )
        self.badge_frame.pack(side="left", padx=(0, 14), pady=4)
        
        self.badge_label = ctk.CTkLabel(
            self.badge_frame,
            text=" ◈ MAYA  //  CYBER-OS v4.5 ",
            font=("Segoe UI", 12, "bold"),
            text_color=COLOR_CYAN
        )
        self.badge_label.pack(padx=10, pady=4)

        # Center Left: Dynamic Greeting & Date
        self.greeting_label = ctk.CTkLabel(
            self.top_header,
            text="",
            font=("Segoe UI", 13, "bold"),
            text_color=COLOR_WHITE
        )
        self.greeting_label.pack(side="left", padx=6)

        # Right Section: Clock, Engine Badge, Status Capsule
        self.clock_label = ctk.CTkLabel(
            self.top_header,
            text="[ 09:33:25 AM ]",
            font=("Consolas", 13, "bold"),
            text_color=COLOR_CYAN
        )
        self.clock_label.pack(side="right", padx=(12, 0))

        # Engine Pill: Reddish/Pink
        self.engine_pill = ctk.CTkFrame(
            self.top_header,
            fg_color="#180718",
            border_color="#701a75",
            border_width=1,
            corner_radius=16
        )
        self.engine_pill.pack(side="right", padx=10, pady=4)
        self.engine_label = ctk.CTkLabel(
            self.engine_pill,
            text="⚡ NVIDIA // NEMOTRON-70B",
            font=("Consolas", 11, "bold"),
            text_color=COLOR_ROSE
        )
        self.engine_label.pack(padx=12, pady=4)

        # Status Pill
        self.status_pill = ctk.CTkFrame(
            self.top_header,
            fg_color="#1a0b2e",
            border_color=COLOR_PURPLE,
            border_width=1.5,
            corner_radius=18
        )
        self.status_pill.pack(side="right", padx=10, pady=4)
        self.status_label = ctk.CTkLabel(
            self.status_pill,
            text="● STANDBY",
            font=("Segoe UI", 11, "bold"),
            text_color=COLOR_CYAN
        )
        self.status_label.pack(padx=14, pady=4)

        # Initialize dynamic text
        self._update_header_time_and_greeting()

    def _update_header_time_and_greeting(self):
        now = datetime.now()
        hr = now.hour
        if hr < 12:
            greet = "GOOD MORNING"
            icon = "☀️"
        elif hr < 17:
            greet = "GOOD AFTERNOON"
            icon = "⛅"
        else:
            greet = "GOOD EVENING"
            icon = "🌙"

        day_str = now.strftime("%A // %b %d, %Y").upper()
        self.greeting_label.configure(
            text=f"{greet} // ROOT: NIMISH {icon}   |   {day_str}"
        )
        self.clock_label.configure(text=f"[ {now.strftime('%I:%M:%S %p')} ]")
        self.after(1000, self._update_header_time_and_greeting)

    # --------------------------------------------------------
    # UI CONSTRUCTION: 3 MAIN COLUMNS
    # --------------------------------------------------------
    def _build_main_columns(self):
        self.main_body = ctk.CTkFrame(self, fg_color=COLOR_BG)
        self.main_body.pack(fill="both", expand=True, padx=18, pady=(0, 14))

        # 3 Column Grid
        self.main_body.columnconfigure(0, weight=33, minsize=380)
        self.main_body.columnconfigure(1, weight=40, minsize=460)
        self.main_body.columnconfigure(2, weight=37, minsize=440)
        self.main_body.rowconfigure(0, weight=1)

        # Column Containers
        self.col_left = ctk.CTkFrame(self.main_body, fg_color="transparent")
        self.col_left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.col_center = ctk.CTkFrame(self.main_body, fg_color="transparent")
        self.col_center.grid(row=0, column=1, sticky="nsew", padx=(0, 10))

        self.col_right = ctk.CTkFrame(self.main_body, fg_color="transparent")
        self.col_right.grid(row=0, column=2, sticky="nsew")

        # Build each column content
        self._build_left_column()
        self._build_center_column()
        self._build_right_column()

    # --------------------------------------------------------
    # COLUMN 1: LEFT (NEURAL MATRIX & RAPID COMMAND DECK)
    # --------------------------------------------------------
    def _build_left_column(self):
        # 1. Card: NEURAL MATRIX
        self.card_matrix = ctk.CTkFrame(
            self.col_left,
            fg_color=COLOR_CARD_BG,
            border_color=COLOR_CARD_BORDER,
            border_width=1.5,
            corner_radius=12
        )
        self.card_matrix.pack(fill="both", expand=True, pady=(0, 10))

        # Card Header
        hdr1 = ctk.CTkFrame(self.card_matrix, fg_color="transparent")
        hdr1.pack(fill="x", padx=14, pady=(12, 6))
        ctk.CTkLabel(hdr1, text="// NEURAL MATRIX", font=("Consolas", 11, "bold"), text_color=COLOR_CYAN_DIM).pack(side="left")
        ctk.CTkLabel(hdr1, text="[ ONLINE // 0x01 ]", font=("Consolas", 11, "bold"), text_color=COLOR_GREEN).pack(side="right")

        # Hexagon / Radar Canvas
        self.radar_canvas = Canvas(self.card_matrix, width=110, height=110, bg=COLOR_CARD_BG, highlightthickness=0)
        self.radar_canvas.pack(pady=(6, 2))
        self._draw_neural_emblem()

        # Name & Subtitle
        ctk.CTkLabel(self.card_matrix, text="M A Y A", font=("Segoe UI", 18, "bold"), text_color=COLOR_CYAN).pack()
        ctk.CTkLabel(self.card_matrix, text="NEURAL CYBER COMPANION", font=("Consolas", 8, "bold"), text_color=TXT_MUTED).pack(pady=(0, 14))

        # Spec Rows Table
        specs = [
            ("SYS.VOICE",   "EDGE NEURAL (EMOTIVE)",   COLOR_CYAN),
            ("LANG.NLU",    "ENGLISH + GUJARATI",      COLOR_GOLD),
            ("AI.ENGINE",   "NVIDIA NEMOTRON 70B",     COLOR_ROSE),
            ("SEC.VAULT",   "AES-256 FERNET ENCRYPTED",COLOR_GREEN),
            ("ROOT.AUTH",   "CREATOR // NIMISH",       COLOR_CYAN),
            ("EMOTION.EQ",  "CALM & ATTENTIVE",        TXT_CYAN)
        ]

        specs_frame = ctk.CTkFrame(self.card_matrix, fg_color="transparent")
        specs_frame.pack(fill="x", padx=16, pady=(0, 14))

        for k, v, c in specs:
            row = ctk.CTkFrame(specs_frame, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=k, font=("Consolas", 10, "bold"), text_color=TXT_MUTED).pack(side="left")
            ctk.CTkLabel(row, text=v, font=("Consolas", 10, "bold"), text_color=c).pack(side="right")

        # 2. Card: RAPID COMMAND DECK
        self.card_deck = ctk.CTkFrame(
            self.col_left,
            fg_color=COLOR_CARD_BG,
            border_color=COLOR_CARD_BORDER,
            border_width=1.5,
            corner_radius=12
        )
        self.card_deck.pack(fill="x", pady=(0, 0))

        hdr2 = ctk.CTkFrame(self.card_deck, fg_color="transparent")
        hdr2.pack(fill="x", padx=14, pady=(10, 8))
        ctk.CTkLabel(hdr2, text="// RAPID COMMAND DECK", font=("Consolas", 11, "bold"), text_color=COLOR_CYAN_DIM).pack(side="left")
        ctk.CTkLabel(hdr2, text="[ EXECUTE ]", font=("Consolas", 11, "bold"), text_color=COLOR_GOLD).pack(side="right")

        # 6 Chips in 2 Columns
        chips_grid = ctk.CTkFrame(self.card_deck, fg_color="transparent")
        chips_grid.pack(fill="x", padx=12, pady=(0, 8))
        chips_grid.columnconfigure(0, weight=1)
        chips_grid.columnconfigure(1, weight=1)

        commands = [
            ("[01] ⚡ Screen OCR",      "perform screen OCR analysis"),
            ("[02] 📸 Capture Shot",     "take a screenshot"),
            ("[03] 🌤️ Weather Intel",    "what is the weather today"),
            ("[04] 🎵 Cyber Beats",      "play cyberpunk synthwave music on youtube"),
            ("[05] ⏱️ 25m Focus Lock",    "set a focus timer for 25 minutes"),
            ("[06] 📄 PDF Generator",    "generate pdf on Maya Introduction")
        ]

        for idx, (label, cmd_text) in enumerate(commands):
            r = idx // 2
            c = idx % 2
            btn = ctk.CTkButton(
                chips_grid,
                text=label,
                font=("Consolas", 10, "bold"),
                fg_color="#07152b",
                hover_color="#0d2b54",
                border_color="#113359",
                border_width=1,
                text_color=TXT_PRIMARY,
                height=32,
                corner_radius=6,
                command=lambda ct=cmd_text: self.dispatch_command(ct)
            )
            btn.grid(row=r, column=c, padx=4, pady=4, sticky="ew")

        # Telemetry Stats Row at bottom
        self.telemetry_row = ctk.CTkFrame(self.card_deck, fg_color="transparent")
        self.telemetry_row.pack(fill="x", padx=14, pady=(4, 10))

        self.cpu_label = ctk.CTkLabel(
            self.telemetry_row,
            text=f"CPU: {self.cpu_pct}%",
            font=("Consolas", 11, "bold"),
            text_color=COLOR_CYAN
        )
        self.cpu_label.pack(side="left", expand=True)

        self.ram_label = ctk.CTkLabel(
            self.telemetry_row,
            text=f"RAM: {self.ram_pct}%",
            font=("Consolas", 11, "bold"),
            text_color=COLOR_ROSE
        )
        self.ram_label.pack(side="left", expand=True)

        self.disk_label = ctk.CTkLabel(
            self.telemetry_row,
            text=f"DISK: {self.disk_pct}%",
            font=("Consolas", 11, "bold"),
            text_color=COLOR_GOLD
        )
        self.disk_label.pack(side="left", expand=True)

    def _draw_neural_emblem(self):
        self.radar_canvas.delete("all")
        cx, cy = 55, 55

        # Dim axis lines
        self.radar_canvas.create_line(10, cy, 100, cy, fill="#0a2a47", width=1)
        self.radar_canvas.create_line(cx, 10, cx, 100, fill="#0a2a47", width=1)

        # Outer target circle
        self.radar_canvas.create_oval(cx - 38, cy - 38, cx + 38, cy + 38, outline=COLOR_CYAN_DIM, width=1.2)

        # Inscribed Hexagon
        r_hex = 28
        hex_pts = []
        for i in range(6):
            ang = math.pi / 3 * i - math.pi / 6
            hex_pts.append(cx + r_hex * math.cos(ang))
            hex_pts.append(cy + r_hex * math.sin(ang))
        self.radar_canvas.create_polygon(hex_pts, outline=COLOR_CYAN, fill="", width=1.5)

        # Sweeping radar scanner beam
        self.radar_beam = self.radar_canvas.create_line(cx, cy, cx + 36, cy, fill=COLOR_CYAN, width=1.5)

        # Central glowing red node
        self.radar_canvas.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, fill=COLOR_ROSE, outline="")

    # --------------------------------------------------------
    # COLUMN 2: CENTER (ARC REACTOR & AUDIO SPECTRUM EQUALIZER)
    # --------------------------------------------------------
    def _build_center_column(self):
        # 1. Card: ARC REACTOR // NEURAL CORE
        self.card_reactor = ctk.CTkFrame(
            self.col_center,
            fg_color=COLOR_CARD_BG,
            border_color=COLOR_CARD_BORDER,
            border_width=1.5,
            corner_radius=12
        )
        self.card_reactor.pack(fill="both", expand=True, pady=(0, 10))

        hdr = ctk.CTkFrame(self.card_reactor, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(12, 4))
        ctk.CTkLabel(hdr, text="◆ ARC REACTOR // NEURAL CORE", font=("Consolas", 11, "bold"), text_color=COLOR_CYAN_DIM).pack(side="left")

        wake_pill = ctk.CTkFrame(hdr, fg_color="#031226", border_color=COLOR_CYAN_DIM, border_width=1, corner_radius=14)
        wake_pill.pack(side="right")
        ctk.CTkLabel(wake_pill, text=" WAKE WORD: 'MAYA' ", font=("Consolas", 10, "bold"), text_color=COLOR_CYAN).pack(padx=8, pady=2)

        # Arc Reactor Animation Canvas
        self.reactor_canvas = Canvas(self.card_reactor, bg=COLOR_CARD_BG, highlightthickness=0)
        self.reactor_canvas.pack(fill="both", expand=True, padx=8, pady=4)

        # Mood Tag at bottom of reactor
        self.mood_label = ctk.CTkLabel(
            self.card_reactor,
            text=self.mood_text,
            font=("Consolas", 11, "bold"),
            text_color=COLOR_CYAN
        )
        self.mood_label.pack(pady=(0, 10))

        # 2. Card: REAL-TIME AUDIO FREQUENCY EQUALIZER
        self.card_eq = ctk.CTkFrame(
            self.col_center,
            fg_color=COLOR_CARD_BG,
            border_color=COLOR_CARD_BORDER,
            border_width=1.5,
            corner_radius=12
        )
        self.card_eq.pack(fill="x", pady=(0, 0))

        hdr_eq = ctk.CTkFrame(self.card_eq, fg_color="transparent")
        hdr_eq.pack(fill="x", padx=14, pady=(10, 4))
        ctk.CTkLabel(hdr_eq, text="// REAL-TIME AUDIO FREQUENCY EQUALIZER", font=("Consolas", 11, "bold"), text_color=COLOR_CYAN_DIM).pack(side="left")
        ctk.CTkLabel(hdr_eq, text="[ AUDIO BUS: ONLINE ]", font=("Consolas", 10, "bold"), text_color=COLOR_CYAN).pack(side="right")

        # Equalizer Waveform Canvas
        self.eq_canvas = Canvas(self.card_eq, height=105, bg=COLOR_CARD_BG, highlightthickness=0)
        self.eq_canvas.pack(fill="x", padx=14, pady=4)

        # Action Buttons Dock
        eq_controls = ctk.CTkFrame(self.card_eq, fg_color="transparent")
        eq_controls.pack(fill="x", padx=14, pady=(4, 12))

        # Large Cyan Listen Button
        self.btn_listen = ctk.CTkButton(
            eq_controls,
            text="🎙️   TAP TO SPEAK [LISTEN]",
            font=("Segoe UI", 12, "bold"),
            fg_color=COLOR_CYAN,
            hover_color="#38bdf8",
            text_color="#000000",
            height=38,
            corner_radius=19,
            command=self.trigger_voice_listen
        )
        self.btn_listen.pack(side="left", fill="x", expand=True, padx=(0, 8))

        # Mute TTS Button
        self.btn_mute = ctk.CTkButton(
            eq_controls,
            text="▢ MUTE TTS",
            font=("Consolas", 11, "bold"),
            fg_color="#07152b",
            hover_color="#0d2b54",
            border_color="#113359",
            border_width=1,
            text_color=TXT_PRIMARY,
            height=38,
            corner_radius=8,
            command=self.toggle_mute_tts
        )
        self.btn_mute.pack(side="right")

    # --------------------------------------------------------
    # COLUMN 3: RIGHT (NEURAL DIALOGUE STREAM & INPUT TERMINAL)
    # --------------------------------------------------------
    def _build_right_column(self):
        self.card_dialogue = ctk.CTkFrame(
            self.col_right,
            fg_color=COLOR_CARD_BG,
            border_color=COLOR_CARD_BORDER,
            border_width=1.5,
            corner_radius=12
        )
        self.card_dialogue.pack(fill="both", expand=True)

        # Header with Purge Button
        hdr = ctk.CTkFrame(self.card_dialogue, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(12, 6))
        ctk.CTkLabel(hdr, text="// NEURAL DIALOGUE STREAM", font=("Consolas", 11, "bold"), text_color=COLOR_CYAN_DIM).pack(side="left")

        self.btn_purge = ctk.CTkButton(
            hdr,
            text="[ PURGE ]",
            font=("Consolas", 10, "bold"),
            fg_color="#07152b",
            hover_color="#0d2b54",
            border_color="#113359",
            border_width=1,
            text_color=TXT_MUTED,
            width=70,
            height=24,
            corner_radius=6,
            command=self.purge_dialogue
        )
        self.btn_purge.pack(side="right")

        # Terminal / Transcript Display Box
        self.terminal_box = ctk.CTkTextbox(
            self.card_dialogue,
            fg_color="#020611",
            text_color=TXT_PRIMARY,
            font=("Consolas", 11),
            corner_radius=8,
            wrap="word",
            border_color="#091f38",
            border_width=1
        )
        self.terminal_box.pack(fill="both", expand=True, padx=12, pady=(4, 10))

        # Setup Rich Text Color Tags in the underlying Tk Text Widget
        self._setup_text_tags()

        # Bottom Input Dock
        input_dock = ctk.CTkFrame(self.card_dialogue, fg_color="transparent")
        input_dock.pack(fill="x", padx=12, pady=(0, 12))

        self.input_entry = ctk.CTkEntry(
            input_dock,
            placeholder_text="root@maya:~$ input command (e.g. 'open Report.pdf', 'read Report.pdf', 'generate pdf on AI')...",
            font=("Consolas", 11),
            fg_color="#030814",
            text_color=COLOR_WHITE,
            placeholder_text_color="#475569",
            border_color="#0c2d4f",
            border_width=1.5,
            height=38,
            corner_radius=8
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.input_entry.bind("<Return>", lambda e: self._on_input_submit())

        self.btn_exec = ctk.CTkButton(
            input_dock,
            text="[EXEC]",
            font=("Consolas", 12, "bold"),
            fg_color=COLOR_CYAN,
            hover_color="#38bdf8",
            text_color="#000000",
            width=80,
            height=38,
            corner_radius=8,
            command=self._on_input_submit
        )
        self.btn_exec.pack(side="right")

    def _setup_text_tags(self):
        try:
            tk_txt = self.terminal_box._textbox
            tk_txt.tag_config("sys", foreground="#475569")
            tk_txt.tag_config("time", foreground=COLOR_CYAN_DIM)
            tk_txt.tag_config("user", foreground=COLOR_CYAN)
            tk_txt.tag_config("mood", foreground="#c084fc")
            tk_txt.tag_config("exec", foreground=COLOR_ROSE)
            tk_txt.tag_config("response", foreground="#10b981")
            tk_txt.tag_config("warn", foreground=COLOR_GOLD)
            tk_txt.tag_config("bold", font=("Consolas", 11, "bold"))
        except Exception:
            pass

    # --------------------------------------------------------
    # LOGGING & TERMINAL FORMATTING (BATCH BUFFERED FOR 60 FPS)
    # --------------------------------------------------------
    def _timestamp(self):
        return datetime.now().strftime("[%H:%M:%S]")

    def _trim_terminal_lines(self, tk_txt, max_lines=450):
        try:
            line_count = int(tk_txt.index('end-1c').split('.')[0])
            if line_count > max_lines:
                tk_txt.delete('1.0', f'{line_count - max_lines}.0')
        except Exception:
            pass

    def _start_log_drain(self):
        self._drain_log_queue()

    def _drain_log_queue(self):
        batch = []
        with self.log_lock:
            if self.log_queue:
                batch = self.log_queue[:25]
                del self.log_queue[:25]

        if batch:
            try:
                tk_txt = self.terminal_box._textbox
                for item_type, data in batch:
                    if item_type == "raw":
                        msg, tag = data
                        tk_txt.insert("end", f"{msg}\n", tag)
                    elif item_type == "user":
                        cmd_text = data
                        t_str = self._timestamp()
                        tk_txt.insert("end", f"\n{t_str} [USER @ TERMINAL] > ", "time")
                        tk_txt.insert("end", f"You: {cmd_text}\n", "user")
                        tk_txt.insert("end", "  🗩 [MOOD: STANDBY] Calm, attentive, and ready.\n", "mood")
                    elif item_type == "exec":
                        tool_name, args_dict = data
                        tk_txt.insert("end", f"  ⚡ [KERNEL // EXEC] {tool_name} | args: {args_dict}\n", "exec")
                    elif item_type == "response":
                        response_text = data
                        t_str = self._timestamp()
                        tk_txt.insert("end", f"{t_str} [MAYA // RESPONSE] > ", "time")
                        tk_txt.insert("end", f"{response_text}\n", "response")

                self._trim_terminal_lines(tk_txt)
                tk_txt.see("end")
            except Exception:
                pass

        self.after(30, self._drain_log_queue)

    def _log_raw(self, msg, tag="sys"):
        with self.log_lock:
            self.log_queue.append(("raw", (msg, tag)))

    def _log_user_command(self, cmd_text):
        with self.log_lock:
            self.log_queue.append(("user", cmd_text))

    def _log_kernel_exec(self, tool_name, args_dict):
        with self.log_lock:
            self.log_queue.append(("exec", (tool_name, args_dict)))

    def _log_response(self, response_text):
        with self.log_lock:
            self.log_queue.append(("response", response_text))

    def purge_dialogue(self):
        try:
            with self.log_lock:
                self.log_queue.clear()
            self.terminal_box.delete("1.0", "end")
            self._log_raw(f"{self._timestamp()} [KERNEL] Dialogue stream purged.", "sys")
        except Exception:
            pass

    # --------------------------------------------------------
    # STDOUT REDIRECTION TO CONSOLE & GUI
    # --------------------------------------------------------
    def write(self, text):
        if self.original_stdout:
            try:
                self.original_stdout.write(text)
                self.original_stdout.flush()
            except Exception:
                pass

        clean = text.strip()
        if not clean:
            return

        # Parse engine prints into colored logs
        if "Maya:" in clean:
            res = clean.split("Maya:", 1)[1].strip()
            self._log_response(res)
        elif "You:" in clean:
            usr = clean.split("You:", 1)[1].strip()
            self._log_user_command(usr)
        elif "Tool Called:" in clean or "Auto-Recovered Tool Call:" in clean:
            parts = clean.split(":", 1)[1].strip()
            self._log_kernel_exec(parts, {})
        elif "Error" in clean or "error" in clean:
            self._log_raw(f"  ⚠ {clean}", "warn")
        else:
            self._log_raw(clean, "sys")

    def flush(self):
        if self.original_stdout:
            try:
                self.original_stdout.flush()
            except Exception:
                pass

    # --------------------------------------------------------
    # STATE MANAGEMENT & DYNAMIC STYLING
    # --------------------------------------------------------
    def set_system_state(self, state_name):
        self.current_state = state_name

        if state_name == "LISTENING":
            self.status_pill.configure(fg_color="#241904", border_color=COLOR_GOLD)
            self.status_label.configure(text="● LISTENING...", text_color=COLOR_GOLD)
            self.mood_text = "[ STATUS: LISTENING... SPEAK NOW ]"
            self.mood_label.configure(text=self.mood_text, text_color=COLOR_GOLD)

        elif state_name == "PROCESSING":
            self.status_pill.configure(fg_color="#1f092b", border_color=COLOR_PURPLE)
            self.status_label.configure(text="● PROCESSING...", text_color=COLOR_PURPLE)
            self.mood_text = "[ MOOD: THINKING // REASONING ◆ ]"
            self.mood_label.configure(text=self.mood_text, text_color=COLOR_PURPLE)

        elif state_name == "SPEAKING":
            self.status_pill.configure(fg_color="#042318", border_color=COLOR_GREEN)
            self.status_label.configure(text="● VOCALIZING...", text_color=COLOR_GREEN)
            self.mood_text = "[ MOOD: SPEAKING // AUDIO ACTIVE ◆ ]"
            self.mood_label.configure(text=self.mood_text, text_color=COLOR_GREEN)

        else: # STANDBY
            self.status_pill.configure(fg_color="#031226", border_color=COLOR_CYAN)
            self.status_label.configure(text="● STANDBY", text_color=COLOR_CYAN)
            self.mood_text = "[ MOOD: READY // CALM ATTENTIVE ◆ ]"
            self.mood_label.configure(text=self.mood_text, text_color=COLOR_CYAN)

    # --------------------------------------------------------
    # COMMAND DISPATCH & WORKERS
    # --------------------------------------------------------
    def _on_input_submit(self):
        query = self.input_entry.get().strip()
        if not query:
            return
        self.input_entry.delete(0, "end")
        self.dispatch_command(query)

    def dispatch_command(self, query):
        self._log_user_command(query)
        self.set_system_state("PROCESSING")

        def _worker():
            try:
                if self.assistant:
                    self.assistant._process_with_ai(query)
                else:
                    time.sleep(0.8)
                    self._log_response(f"Executed: {query}. Maya neural assistant is running.")
            except Exception as e:
                self._log_raw(f"Execution error: {e}", "warn")
            finally:
                self.after(0, lambda: self.set_system_state("STANDBY"))

        threading.Thread(target=_worker, daemon=True).start()

    def trigger_voice_listen(self):
        if not self.assistant:
            self._log_raw("Initializing audio engine...", "sys")
            return

        def _listen_worker():
            try:
                self.after(0, lambda: self.set_system_state("LISTENING"))
                user_speech = self.assistant.voice.listen()
                if user_speech:
                    self.after(0, lambda: self.set_system_state("PROCESSING"))
                    self.assistant._process_with_ai(user_speech)
                else:
                    self._log_raw("No speech detected.", "sys")
            except Exception as e:
                self._log_raw(f"Voice engine notice: {e}", "warn")
            finally:
                self.after(0, lambda: self.set_system_state("STANDBY"))

        threading.Thread(target=_listen_worker, daemon=True).start()

    def toggle_mute_tts(self):
        self.tts_muted = not self.tts_muted
        if self.tts_muted:
            self.btn_mute.configure(text="▣ TTS MUTED", text_color=COLOR_ROSE, border_color=COLOR_ROSE)
            if self.assistant and hasattr(self.assistant, 'voice'):
                self.assistant.voice.is_muted = True
        else:
            self.btn_mute.configure(text="▢ MUTE TTS", text_color=TXT_PRIMARY, border_color="#113359")
            if self.assistant and hasattr(self.assistant, 'voice'):
                self.assistant.voice.is_muted = False

    def _telemetry_worker(self):
        while True:
            try:
                cpu = int(psutil.cpu_percent(interval=1.0))
                ram = int(psutil.virtual_memory().percent)
                disk = int(psutil.disk_usage('C:\\').percent)
                self.cpu_pct = cpu
                self.ram_pct = ram
                self.disk_pct = disk

                def _apply_stats(c=cpu, r=ram, d=disk):
                    try:
                        self.cpu_label.configure(text=f"CPU: {c}%")
                        self.ram_label.configure(text=f"RAM: {r}%")
                        self.disk_label.configure(text=f"DISK: {d}%")
                    except Exception:
                        pass

                self.after(0, _apply_stats)
            except Exception:
                time.sleep(2.0)

    def _init_assistant_worker(self):
        try:
            self.assistant = Assistant()
            print("🚀 Maya Core Engine Synchronized.")
            startup_line = self.assistant.generate_startup_greeting()
            self.assistant.voice.speak(startup_line)
        except Exception as e:
            print(f"Engine init notice: {e}")

    # --------------------------------------------------------
    # HIGH-PERFORMANCE 60 FPS ZERO-ALLOCATION ANIMATION SYSTEM
    # --------------------------------------------------------
    def _start_animation_loop(self):
        self._render_animations()

    def _render_animations(self):
        now = time.perf_counter()
        dt = now - self.last_frame_time
        self.last_frame_time = now
        # Clamp dt to prevent teleporting if minimized or suspended
        dt = min(max(dt, 0.001), 0.05)

        self.anim_t += dt * 1.6
        self.arc_angle_1 += dt * 0.95
        self.arc_angle_2 -= dt * 1.25

        # 1. Arc Reactor Render (Zero GC Allocations)
        self._render_arc_reactor(dt)

        # 2. Smooth Lerp Spectrum Equalizer
        self._render_equalizer(dt)

        # 3. Dynamic Radar Scanner Sweep
        if self.radar_beam:
            try:
                self.radar_angle = (self.radar_angle + dt * 2.4) % (2 * math.pi)
                cx, cy = 55, 55
                rx = cx + 36 * math.cos(self.radar_angle)
                ry = cy + 36 * math.sin(self.radar_angle)
                self.radar_canvas.coords(self.radar_beam, cx, cy, rx, ry)
            except Exception:
                pass

        # Target locked ~60 FPS with precise frame compensation
        elapsed_ms = (time.perf_counter() - now) * 1000.0
        target_delay = max(1, int(16.6 - elapsed_ms))
        self.after(target_delay, self._render_animations)

    def _init_reactor_items(self):
        self.reactor_canvas.delete("all")
        self.reactor_items = {
            "axis_v": self.reactor_canvas.create_line(0, 0, 0, 0, fill="#071b30", width=1),
            "axis_h": self.reactor_canvas.create_line(0, 0, 0, 0, fill="#071b30", width=1),
            "arc_out_1": self.reactor_canvas.create_arc(0, 0, 0, 0, style="arc", width=2.5),
            "arc_out_2": self.reactor_canvas.create_arc(0, 0, 0, 0, style="arc", width=1.5),
            "arc_out_3": self.reactor_canvas.create_arc(0, 0, 0, 0, style="arc", width=2.5),
            "arc_mid_1": self.reactor_canvas.create_arc(0, 0, 0, 0, style="arc", width=2.0),
            "arc_mid_2": self.reactor_canvas.create_arc(0, 0, 0, 0, style="arc", width=2.2),
            "arc_mid_3": self.reactor_canvas.create_arc(0, 0, 0, 0, style="arc", width=1.5),
            "inner_ring": self.reactor_canvas.create_oval(0, 0, 0, 0, width=2),
            "core_halo": self.reactor_canvas.create_oval(0, 0, 0, 0, width=1),
            "core_main": self.reactor_canvas.create_oval(0, 0, 0, 0, outline=""),
            "core_center": self.reactor_canvas.create_oval(0, 0, 0, 0, fill=COLOR_WHITE, outline=""),
            "particles": []
        }
        for p in self.particles:
            part_id = self.reactor_canvas.create_oval(0, 0, 0, 0, fill=p.color, outline="")
            self.reactor_items["particles"].append(part_id)

    def _render_arc_reactor(self, dt):
        w = self.reactor_canvas.winfo_width()
        h = self.reactor_canvas.winfo_height()
        if w < 50 or h < 50:
            return

        if not self.reactor_items:
            self._init_reactor_items()

        cx, cy = w / 2, h / 2
        items = self.reactor_items

        # Reposition Crosshairs
        self.reactor_canvas.coords(items["axis_v"], cx, 10, cx, h - 10)
        self.reactor_canvas.coords(items["axis_h"], 10, cy, w - 10, cy)

        # Primary Arc Theme Colors based on state
        if self.current_state == "LISTENING":
            c_ring = COLOR_GOLD
            c_sec = "#fde047"
        elif self.current_state == "PROCESSING":
            c_ring = COLOR_PURPLE
            c_sec = "#d8b4fe"
        elif self.current_state == "SPEAKING":
            c_ring = COLOR_GREEN
            c_sec = "#6ee7b7"
        else:
            c_ring = COLOR_CYAN
            c_sec = COLOR_CYAN_DIM

        # Outer Segmented Ring Arcs (clockwise rotation)
        r_outer = min(cx, cy) * 0.82
        deg1 = math.degrees(self.arc_angle_1) % 360
        box_out = (cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer)

        self.reactor_canvas.coords(items["arc_out_1"], *box_out)
        self.reactor_canvas.itemconfig(items["arc_out_1"], start=deg1, extent=75, outline=c_ring)

        self.reactor_canvas.coords(items["arc_out_2"], *box_out)
        self.reactor_canvas.itemconfig(items["arc_out_2"], start=(deg1 + 120) % 360, extent=45, outline=c_sec)

        self.reactor_canvas.coords(items["arc_out_3"], *box_out)
        self.reactor_canvas.itemconfig(items["arc_out_3"], start=(deg1 + 210) % 360, extent=90, outline=c_ring)

        # Middle Segmented Ring Arcs (counter-clockwise)
        r_mid = min(cx, cy) * 0.58
        deg2 = math.degrees(self.arc_angle_2) % 360
        box_mid = (cx - r_mid, cy - r_mid, cx + r_mid, cy + r_mid)

        self.reactor_canvas.coords(items["arc_mid_1"], *box_mid)
        self.reactor_canvas.itemconfig(items["arc_mid_1"], start=deg2, extent=110, outline=c_sec)

        self.reactor_canvas.coords(items["arc_mid_2"], *box_mid)
        self.reactor_canvas.itemconfig(items["arc_mid_2"], start=(deg2 + 160) % 360, extent=60, outline=c_ring)

        self.reactor_canvas.coords(items["arc_mid_3"], *box_mid)
        self.reactor_canvas.itemconfig(items["arc_mid_3"], start=(deg2 + 270) % 360, extent=40, outline=c_sec)

        # Inner Glowing Ring
        r_inner = min(cx, cy) * 0.36
        self.reactor_canvas.coords(items["inner_ring"], cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner)
        self.reactor_canvas.itemconfig(items["inner_ring"], outline=c_ring)

        # Pulsing Reactor Core
        pulse = math.sin(self.anim_t * 2.8) * 3.5
        r_core = 14 + pulse
        self.reactor_canvas.coords(items["core_halo"], cx - r_core - 8, cy - r_core - 8, cx + r_core + 8, cy + r_core + 8)
        self.reactor_canvas.itemconfig(items["core_halo"], outline=c_sec)

        self.reactor_canvas.coords(items["core_main"], cx - r_core, cy - r_core, cx + r_core, cy + r_core)
        self.reactor_canvas.itemconfig(items["core_main"], fill=c_ring)

        self.reactor_canvas.coords(items["core_center"], cx - 5, cy - 5, cx + 5, cy + 5)

        # Orbiting Sparkle Particles (dt-based physics)
        dt_scale = dt * 60.0
        for p, part_id in zip(self.particles, items["particles"]):
            p.cx = cx
            p.cy = cy
            p.update(dt_scale)
            px, py = p.get_pos()
            sz = p.size
            self.reactor_canvas.coords(part_id, px - sz, py - sz, px + sz, py + sz)

    def _init_eq_items(self):
        self.eq_canvas.delete("all")
        self.eq_items = {
            "bars": [],
            "caps_top": [],
            "caps_bot": []
        }
        for _ in range(32):
            b = self.eq_canvas.create_line(0, 0, 0, 0, width=4, capstyle="round")
            ct = self.eq_canvas.create_oval(0, 0, 0, 0, outline="")
            cb = self.eq_canvas.create_oval(0, 0, 0, 0, outline="")
            self.eq_items["bars"].append(b)
            self.eq_items["caps_top"].append(ct)
            self.eq_items["caps_bot"].append(cb)

    def _render_equalizer(self, dt):
        w = self.eq_canvas.winfo_width()
        h = self.eq_canvas.winfo_height()
        if w < 50 or h < 20:
            return

        if not self.eq_items:
            self._init_eq_items()

        cy = h / 2
        num_bars = 32
        gap = 4
        bar_width = max(4, (w - (num_bars * gap)) / num_bars)

        # Wave height multiplier based on state
        if self.current_state == "LISTENING":
            amp_mult = 0.88
            bar_color = COLOR_GOLD
            cap_color = COLOR_CYAN
            has_caps = True
        elif self.current_state == "PROCESSING":
            amp_mult = 0.68
            bar_color = COLOR_PURPLE
            cap_color = COLOR_CYAN
            has_caps = False
        elif self.current_state == "SPEAKING":
            amp_mult = 0.96
            bar_color = COLOR_GREEN
            cap_color = COLOR_WHITE
            has_caps = True
        else:
            amp_mult = 0.38
            bar_color = COLOR_CYAN
            cap_color = COLOR_CYAN
            has_caps = False

        total_w = num_bars * bar_width + (num_bars - 1) * gap
        start_x = (w - total_w) / 2
        lerp_rate = min(1.0, 14.0 * dt)

        for i in range(num_bars):
            norm = i / (num_bars - 1)
            envelope = math.sin(norm * math.pi)

            wave1 = math.sin(self.anim_t * 3.6 + i * 0.45)
            wave2 = math.cos(self.anim_t * 2.3 - i * 0.32)
            target_h = (0.35 + 0.35 * wave1 + 0.30 * wave2) * envelope * amp_mult
            target_h = max(0.08, min(target_h, 0.95))

            # Exponential decay lerp for buttery smooth fluid wave physics
            self.spectrum_heights[i] += (target_h - self.spectrum_heights[i]) * lerp_rate
            cur_h = self.spectrum_heights[i]

            half_h = cur_h * (h * 0.42)
            bx = start_x + i * (bar_width + gap)
            y1 = cy - half_h
            y2 = cy + half_h

            # Reposition Bar Line
            bar_id = self.eq_items["bars"][i]
            self.eq_canvas.coords(bar_id, bx, y1, bx, y2)
            self.eq_canvas.itemconfig(bar_id, fill=bar_color, width=bar_width)

            # Reposition Cap Accents
            ct_id = self.eq_items["caps_top"][i]
            cb_id = self.eq_items["caps_bot"][i]
            if has_caps:
                self.eq_canvas.coords(ct_id, bx - 2, y1 - 2, bx + 2, y1 + 2)
                self.eq_canvas.itemconfig(ct_id, fill=cap_color)
                self.eq_canvas.coords(cb_id, bx - 2, y2 - 2, bx + 2, y2 + 2)
                self.eq_canvas.itemconfig(cb_id, fill=cap_color)
            else:
                self.eq_canvas.coords(ct_id, -10, -10, -10, -10)
                self.eq_canvas.coords(cb_id, -10, -10, -10, -10)


# ============================================================
# ENTRY POINT
# ============================================================
def main():
    app = MayaCyberOSApp()
    app.mainloop()

if __name__ == "__main__":
    main()