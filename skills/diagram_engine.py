"""
skills/diagram_engine.py

High-Resolution Automated Diagram Generation Engine for Maya AI Assistant.
Generates publication-quality technical diagrams (300 DPI) using Matplotlib and Pillow:
- Machine Learning Lifecycle Diagrams
- Deep Neural Network Architecture Diagrams
- Decision Tree & Classification Workflows
- System Architecture & Multi-Tier Pipelines
- Confusion Matrix & Performance Metric Heatmaps
- Algorithm Flowcharts & Process Pipelines
- Algorithm / Model Benchmark Comparison Charts

All diagrams are rendered to high-resolution PNGs with modern palettes,
clean typography, and no overlapping nodes, optimized for PDF report embedding.
"""

import os
import sys
import tempfile

# Ensure base site-packages are accessible
for p in [r"D:\Nimish_project\Lib\site-packages", os.path.join(os.getcwd(), "venv_312", "Lib", "site-packages")]:
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)

import matplotlib
matplotlib.use("Agg")  # Headless non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ArrowStyle


# Modern Design Palette
PALETTE = {
    "bg": "#FFFFFF",
    "card_bg": "#F8FAFC",
    "primary": "#1E3A8A",      # Deep Navy
    "secondary": "#0284C7",    # Tech Cyan
    "accent": "#0D9488",       # Teal
    "purple": "#7C3AED",       # Violet
    "orange": "#EA580C",       # Amber Orange
    "green": "#16A34A",        # Emerald Green
    "red": "#DC2626",          # Coral Red
    "text_dark": "#0F172A",    # Dark Slate
    "text_muted": "#475569",   # Muted Gray
    "border": "#CBD5E1",       # Light Border
    "shadow": "#E2E8F0"
}


def _ensure_dir(path: str):
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def generate_ml_lifecycle_diagram(output_path: str) -> str:
    """Generates a professional 6-stage Machine Learning Lifecycle diagram with feedback loop."""
    _ensure_dir(output_path)
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    fig.patch.set_facecolor(PALETTE["bg"])
    ax.set_facecolor(PALETTE["bg"])
    ax.axis("off")

    stages = [
        {"title": "1. Data Ingestion", "desc": "Collection, ETL &\nSource Validation", "color": "#0284C7"},
        {"title": "2. Preprocessing", "desc": "Cleaning, Imputation\n& Feature Eng.", "color": "#0D9488"},
        {"title": "3. Model Training", "desc": "Architecture Design,\nHyperparameter Tuning", "color": "#7C3AED"},
        {"title": "4. Evaluation", "desc": "Validation, Testing\n& Bias Audit", "color": "#EA580C"},
        {"title": "5. Deployment", "desc": "REST/gRPC APIs,\nContainerization", "color": "#16A34A"},
        {"title": "6. Monitoring", "desc": "Drift Detection &\nContinuous Retraining", "color": "#1E3A8A"},
    ]

    n = len(stages)
    box_w = 1.3
    box_h = 1.6
    spacing = 0.28
    start_x = 0.35
    y_center = 2.4

    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4.8)

    # Title header inside diagram
    ax.text(5.0, 4.4, "END-TO-END MACHINE LEARNING LIFECYCLE", 
            ha="center", va="center", fontsize=13, fontweight="bold", color=PALETTE["primary"])
    ax.text(5.0, 4.08, "Deterministic Multi-Stage MLOps Pipeline with Continuous Feedback Loop", 
            ha="center", va="center", fontsize=8.5, color=PALETTE["text_muted"])

    centers = []
    for i, s in enumerate(stages):
        x = start_x + i * (box_w + spacing)
        y = y_center - box_h / 2
        centers.append((x + box_w / 2, y_center))

        # Card shadow
        shadow = FancyBboxPatch((x + 0.03, y - 0.04), box_w, box_h,
                                boxstyle="round,pad=0.06,rounding_size=0.12",
                                facecolor=PALETTE["shadow"], edgecolor="none", zorder=1)
        ax.add_patch(shadow)

        # Card box
        bbox = FancyBboxPatch((x, y), box_w, box_h,
                              boxstyle="round,pad=0.06,rounding_size=0.12",
                              facecolor="#F8FAFC", edgecolor=s["color"], linewidth=1.8, zorder=2)
        ax.add_patch(bbox)

        # Top color accent strip
        accent = FancyBboxPatch((x, y + box_h - 0.32), box_w, 0.32,
                                boxstyle="round,pad=0.06,rounding_size=0.12",
                                facecolor=s["color"], edgecolor="none", zorder=3)
        ax.add_patch(accent)

        # Stage Number / Title in white
        ax.text(x + box_w / 2, y + box_h - 0.16, s["title"],
                ha="center", va="center", fontsize=8, fontweight="bold", color="#FFFFFF", zorder=4)

        # Description
        ax.text(x + box_w / 2, y + 0.65, s["desc"],
                ha="center", va="center", fontsize=7.2, color=PALETTE["text_dark"], zorder=4, linespacing=1.2)

        # Forward Arrow to next stage
        if i < n - 1:
            next_x = start_x + (i + 1) * (box_w + spacing)
            ax.annotate("", xy=(next_x - 0.04, y_center), xytext=(x + box_w + 0.04, y_center),
                        arrowprops=dict(arrowstyle="-|>", color=PALETTE["secondary"],
                                        lw=2.0, mutation_scale=12), zorder=5)

    # Feedback loop arrow from Stage 6 back to Stage 1
    p1 = centers[0]
    p6 = centers[-1]
    ret_y = 0.7
    ax.annotate("", xy=(p1[0], y_center - box_h/2 - 0.05),
                xytext=(p6[0], y_center - box_h/2 - 0.05),
                arrowprops=dict(arrowstyle="->", color=PALETTE["primary"],
                                connectionstyle=f"arc,angleA=-90,angleB=-90,armA=35,armB=35,rad=15",
                                lw=1.8, linestyle="--"), zorder=5)
    ax.text(5.0, 0.72, "⚡ Automated Retraining Trigger & Performance Feedback",
            ha="center", va="center", fontsize=7.5, fontweight="bold", color=PALETTE["primary"],
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#EFF6FF", edgecolor="#BFDBFE", lw=1), zorder=6)

    plt.tight_layout()
    fig.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none", bbox_inches="tight")
    plt.close(fig)
    return output_path


def generate_neural_network_diagram(output_path: str) -> str:
    """Generates a publication-grade Deep Neural Network architecture diagram with synaptic connections."""
    _ensure_dir(output_path)
    fig, ax = plt.subplots(figsize=(9.5, 5), dpi=300)
    fig.patch.set_facecolor(PALETTE["bg"])
    ax.set_facecolor(PALETTE["bg"])
    ax.axis("off")

    ax.set_xlim(-0.5, 10.5)
    ax.set_ylim(-0.5, 6.0)

    # Header
    ax.text(5.0, 5.6, "DEEP FEEDFORWARD NEURAL NETWORK ARCHITECTURE",
            ha="center", va="center", fontsize=13, fontweight="bold", color=PALETTE["primary"])
    ax.text(5.0, 5.25, "Fully Connected Multi-Layer Perceptron (Input → Hidden Layers → Activation → Output)",
            ha="center", va="center", fontsize=8.5, color=PALETTE["text_muted"])

    layers = [
        {"name": "Input Layer\n(x ∈ R⁴)", "x": 1.2, "nodes": 4, "labels": ["x₁", "x₂", "x₃", "x₄"], "color": "#0284C7"},
        {"name": "Hidden Layer 1\n(ReLU, 5)", "x": 3.8, "nodes": 5, "labels": ["h₁₁", "h₁₂", "h₁₃", "h₁₄", "h₁₅"], "color": "#7C3AED"},
        {"name": "Hidden Layer 2\n(ReLU, 5)", "x": 6.4, "nodes": 5, "labels": ["h₂₁", "h₂₂", "h₂₃", "h₂₄", "h₂₅"], "color": "#0D9488"},
        {"name": "Output Layer\n(Softmax, 2)", "x": 9.0, "nodes": 2, "labels": ["ŷ₁", "ŷ₂"], "color": "#EA580C"},
    ]

    y_span = 4.0
    layer_coords = []

    for l in layers:
        coords = []
        n = l["nodes"]
        step = y_span / (n + 1)
        for i in range(n):
            cy = 0.7 + (i + 1) * step
            coords.append((l["x"], cy))
        layer_coords.append(coords)

    # Draw Synaptic Weights (Lines between consecutive layers)
    for l_idx in range(len(layer_coords) - 1):
        curr_layer = layer_coords[l_idx]
        next_layer = layer_coords[l_idx + 1]
        for src_x, src_y in curr_layer:
            for dst_x, dst_y in next_layer:
                ax.plot([src_x, dst_x], [src_y, dst_y], color="#CBD5E1", lw=0.7, alpha=0.65, zorder=1)

    # Draw Nodes and Labels
    r = 0.28
    for l_idx, l in enumerate(layers):
        coords = layer_coords[l_idx]
        for i, (cx, cy) in enumerate(coords):
            # Outer ring shadow
            shadow = patches.Circle((cx + 0.02, cy - 0.02), r, facecolor=PALETTE["shadow"], edgecolor="none", zorder=2)
            ax.add_patch(shadow)

            # Circle node
            circle = patches.Circle((cx, cy), r, facecolor="#F8FAFC", edgecolor=l["color"], linewidth=2.0, zorder=3)
            ax.add_patch(circle)

            # Node label
            lbl = l["labels"][i] if i < len(l["labels"]) else f"n{i+1}"
            ax.text(cx, cy, lbl, ha="center", va="center", fontsize=8.5, fontweight="bold",
                    color=l["color"], zorder=4)

        # Layer Name below
        ax.text(l["x"], 0.25, l["name"], ha="center", va="top", fontsize=8,
                fontweight="bold", color=PALETTE["text_dark"], linespacing=1.2)

    # Math Annotations
    ax.text(2.5, 4.8, "W⁽¹⁾x + b⁽¹⁾", ha="center", va="center", fontsize=7.5, color=PALETTE["text_muted"], style="italic")
    ax.text(5.1, 4.8, "W⁽²⁾a⁽¹⁾ + b⁽²⁾", ha="center", va="center", fontsize=7.5, color=PALETTE["text_muted"], style="italic")
    ax.text(7.7, 4.8, "W⁽³⁾a⁽²⁾ + b⁽³⁾", ha="center", va="center", fontsize=7.5, color=PALETTE["text_muted"], style="italic")

    plt.tight_layout()
    fig.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none", bbox_inches="tight")
    plt.close(fig)
    return output_path


def generate_decision_tree_diagram(output_path: str) -> str:
    """Generates a clean decision tree classifier visualization."""
    _ensure_dir(output_path)
    fig, ax = plt.subplots(figsize=(9.5, 5), dpi=300)
    fig.patch.set_facecolor(PALETTE["bg"])
    ax.set_facecolor(PALETTE["bg"])
    ax.axis("off")

    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)

    ax.text(5.0, 4.7, "DECISION TREE CLASSIFICATION ARCHITECTURE",
            ha="center", va="center", fontsize=13, fontweight="bold", color=PALETTE["primary"])
    ax.text(5.0, 4.38, "Recursive Binary Splitting Based on Information Gain & Gini Impurity",
            ha="center", va="center", fontsize=8.5, color=PALETTE["text_muted"])

    # Tree Nodes definition
    nodes = {
        "root": {"pos": (5.0, 3.5), "w": 2.2, "h": 0.8, "text": "Age ≤ 45\nGini = 0.48 | N = 200", "color": PALETTE["primary"], "leaf": False},
        "l1":   {"pos": (2.5, 2.2), "w": 2.0, "h": 0.8, "text": "Income ≤ $60k\nGini = 0.32 | N = 110", "color": PALETTE["secondary"], "leaf": False},
        "r1":   {"pos": (7.5, 2.2), "w": 2.0, "h": 0.8, "text": "Credit Score ≤ 700\nGini = 0.28 | N = 90", "color": PALETTE["secondary"], "leaf": False},
        "leaf1":{"pos": (1.3, 0.9), "w": 1.7, "h": 0.7, "text": "Class: Approved (92%)\nSamples: 75", "color": PALETTE["green"], "leaf": True},
        "leaf2":{"pos": (3.7, 0.9), "w": 1.7, "h": 0.7, "text": "Class: Denied (88%)\nSamples: 35", "color": PALETTE["red"], "leaf": True},
        "leaf3":{"pos": (6.3, 0.9), "w": 1.7, "h": 0.7, "text": "Class: Review (70%)\nSamples: 40", "color": PALETTE["orange"], "leaf": True},
        "leaf4":{"pos": (8.7, 0.9), "w": 1.7, "h": 0.7, "text": "Class: Approved (96%)\nSamples: 50", "color": PALETTE["green"], "leaf": True},
    }

    edges = [
        ("root", "l1", "True"),
        ("root", "r1", "False"),
        ("l1", "leaf1", "True"),
        ("l1", "leaf2", "False"),
        ("r1", "leaf3", "True"),
        ("r1", "leaf4", "False"),
    ]

    # Draw edges
    for src_id, dst_id, lbl in edges:
        s = nodes[src_id]["pos"]
        d = nodes[dst_id]["pos"]
        ax.annotate("", xy=d, xytext=s,
                    arrowprops=dict(arrowstyle="-|>", color=PALETTE["text_muted"], lw=1.6, mutation_scale=10),
                    zorder=1)
        # Edge label
        mid_x = (s[0] + d[0]) / 2 + (0.15 if s[0] < d[0] else -0.15)
        mid_y = (s[1] + d[1]) / 2
        ax.text(mid_x, mid_y, lbl, fontsize=7.5, fontweight="bold",
                color=PALETTE["primary"] if lbl == "True" else PALETTE["orange"],
                bbox=dict(boxstyle="round,pad=0.2", facecolor="#FFFFFF", edgecolor="none"))

    # Draw nodes
    for k, v in nodes.items():
        cx, cy = v["pos"]
        w, h = v["w"], v["h"]
        x, y = cx - w/2, cy - h/2

        # Shadow
        shadow = FancyBboxPatch((x + 0.03, y - 0.03), w, h, boxstyle="round,pad=0.04,rounding_size=0.1",
                                facecolor=PALETTE["shadow"], edgecolor="none", zorder=2)
        ax.add_patch(shadow)

        bg = "#F0FDF4" if v["color"] == PALETTE["green"] else ("#FEF2F2" if v["color"] == PALETTE["red"] else "#F8FAFC")
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.1",
                             facecolor=bg, edgecolor=v["color"], linewidth=1.6, zorder=3)
        ax.add_patch(box)

        ax.text(cx, cy, v["text"], ha="center", va="center", fontsize=7.5,
                fontweight="bold" if v["leaf"] else "normal", color=PALETTE["text_dark"], zorder=4, linespacing=1.2)

    plt.tight_layout()
    fig.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none", bbox_inches="tight")
    plt.close(fig)
    return output_path


def generate_system_architecture_diagram(output_path: str, title: str = "Maya Cyber Companion OS") -> str:
    """Generates an enterprise-tier multi-subsystem architecture diagram."""
    _ensure_dir(output_path)
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=300)
    fig.patch.set_facecolor(PALETTE["bg"])
    ax.set_facecolor(PALETTE["bg"])
    ax.axis("off")

    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.2)

    ax.text(5.0, 4.85, f"{title.upper()} - ARCHITECTURE OVERVIEW",
            ha="center", va="center", fontsize=13, fontweight="bold", color=PALETTE["primary"])
    ax.text(5.0, 4.55, "Decoupled Multi-Agent Subsystems with Sub-Second Local Deterministic Fast-Path",
            ha="center", va="center", fontsize=8.5, color=PALETTE["text_muted"])

    tiers = [
        {"y": 3.7, "title": "PERCEPTION & INTERFACE TIER", "color": PALETTE["secondary"],
         "blocks": ["Neural Voice TTS (Edge-TTS)", "Speech Recognition (Vosk)", "CustomTkinter Cyber HUD (60 FPS)"]},
        {"y": 2.5, "title": "INTELLIGENCE & ORCHESTRATION TIER", "color": PALETTE["purple"],
         "blocks": ["Sub-Second Fast-Path Dispatcher", "Groq / NVIDIA Nemotron-70B Core", "Dynamic Tool Intent Router"]},
        {"y": 1.3, "title": "PERSISTENCE & SECURITY TIER", "color": PALETTE["accent"],
         "blocks": ["AES-256 Fernet Encrypted Vault", "SQLite Memory DB", "Document RAG & PyPDF2 Engine"]},
        {"y": 0.1, "title": "NATIVE HARDWARE & OS TIER", "color": PALETTE["primary"],
         "blocks": ["Windows Audio Core (PyCaw)", "PowerShell & System APIs", "Screen Vision & OCR Pipelines"]}
    ]

    for t in tiers:
        y = t["y"]
        # Tier boundary card
        shadow = FancyBboxPatch((0.42, y - 0.02), 9.16, 0.9, boxstyle="round,pad=0.04,rounding_size=0.08",
                                facecolor=PALETTE["shadow"], edgecolor="none", zorder=1)
        ax.add_patch(shadow)

        bg_box = FancyBboxPatch((0.4, y), 9.2, 0.9, boxstyle="round,pad=0.04,rounding_size=0.08",
                                facecolor="#F8FAFC", edgecolor=t["color"], linewidth=1.4, zorder=2)
        ax.add_patch(bg_box)

        # Tier title on left
        ax.text(0.6, y + 0.45, t["title"], ha="left", va="center", fontsize=7.5, fontweight="bold",
                color=t["color"], zorder=3)

        # Inner service blocks
        b_x = 3.2
        b_w = 1.95
        b_h = 0.65
        for b_idx, block_name in enumerate(t["blocks"]):
            bx = b_x + b_idx * (b_w + 0.12)
            by = y + 0.12
            inner_box = FancyBboxPatch((bx, by), b_w, b_h, boxstyle="round,pad=0.02,rounding_size=0.06",
                                       facecolor="#FFFFFF", edgecolor=PALETTE["border"], linewidth=1, zorder=3)
            ax.add_patch(inner_box)
            ax.text(bx + b_w/2, by + b_h/2, block_name, ha="center", va="center",
                    fontsize=6.8, color=PALETTE["text_dark"], zorder=4)

    # Inter-tier bidirectional bus arrows
    for y_arrow in [3.45, 2.25, 1.05]:
        ax.annotate("", xy=(5.0, y_arrow), xytext=(5.0, y_arrow + 0.25),
                    arrowprops=dict(arrowstyle="<->", color=PALETTE["primary"], lw=1.5), zorder=5)

    plt.tight_layout()
    fig.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none", bbox_inches="tight")
    plt.close(fig)
    return output_path


def generate_confusion_matrix_diagram(output_path: str) -> str:
    """Generates an annotated 2x2 Confusion Matrix and Evaluation Metrics chart."""
    _ensure_dir(output_path)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.6), dpi=300, gridspec_kw={'width_ratios': [1.2, 1]})
    fig.patch.set_facecolor(PALETTE["bg"])
    ax1.set_facecolor(PALETTE["bg"])
    ax2.set_facecolor(PALETTE["bg"])

    # Left: Confusion Matrix Heatmap
    matrix_data = [[1420, 65], [45, 1270]]
    im = ax1.imshow(matrix_data, cmap="Blues", alpha=0.85)

    ax1.set_xticks([0, 1])
    ax1.set_yticks([0, 1])
    ax1.set_xticklabels(["Predicted Positive", "Predicted Negative"], fontsize=8.5, fontweight="bold")
    ax1.set_yticklabels(["Actual Positive", "Actual Negative"], fontsize=8.5, fontweight="bold")

    cells = [
        {"val": "TP = 1,420\n(True Positive)", "sub": "Sensitivity = 96.9%", "r": 0, "c": 0, "text_c": "#FFFFFF"},
        {"val": "FN = 45\n(Type II Error)", "sub": "Miss Rate = 3.1%", "r": 1, "c": 0, "text_c": "#1E3A8A"},
        {"val": "FP = 65\n(Type I Error)", "sub": "Fall-Out = 4.9%", "r": 0, "c": 1, "text_c": "#1E3A8A"},
        {"val": "TN = 1,270\n(True Negative)", "sub": "Specificity = 95.1%", "r": 1, "c": 1, "text_c": "#FFFFFF"},
    ]

    for cell in cells:
        ax1.text(cell["c"], cell["r"], cell["val"], ha="center", va="center",
                 fontsize=9.5, fontweight="bold", color=cell["text_c"])

    ax1.set_title("CONFUSION MATRIX CLASSIFIER", fontsize=11, fontweight="bold", color=PALETTE["primary"], pad=12)

    # Right: Metric Summary Bar Chart
    metrics = ["Accuracy", "Precision", "Recall", "F1-Score", "ROC-AUC"]
    scores = [96.1, 95.6, 96.9, 96.2, 98.4]
    colors = [PALETTE["primary"], PALETTE["secondary"], PALETTE["accent"], PALETTE["purple"], PALETTE["green"]]

    y_pos = range(len(metrics))
    bars = ax2.barh(y_pos, scores, color=colors, height=0.55, edgecolor="none", zorder=2)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(metrics, fontsize=9, fontweight="bold")
    ax2.set_xlim(0, 100)
    ax2.set_xlabel("Score (%)", fontsize=8.5, color=PALETTE["text_muted"])
    ax2.grid(axis="x", linestyle="--", alpha=0.4, zorder=1)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['left'].set_color(PALETTE["border"])
    ax2.spines['bottom'].set_color(PALETTE["border"])

    for bar, score in zip(bars, scores):
        ax2.text(score + 1.2, bar.get_y() + bar.get_height()/2, f"{score:.1f}%",
                 ha="left", va="center", fontsize=8.5, fontweight="bold", color=PALETTE["text_dark"])

    ax2.set_title("MODEL EVALUATION BENCHMARKS", fontsize=11, fontweight="bold", color=PALETTE["primary"], pad=12)

    plt.tight_layout()
    fig.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none", bbox_inches="tight")
    plt.close(fig)
    return output_path


def generate_flowchart_diagram(output_path: str, steps: list = None, title: str = "Algorithm Workflow") -> str:
    """Generates an algorithmic process flowchart."""
    _ensure_dir(output_path)
    if not steps:
        steps = [
            ("Raw Input Data", "Validation & Type Casting"),
            ("Feature Pipeline", "Scaling & One-Hot Encoding"),
            ("Inference Engine", "Feedforward Matrix Multiplication"),
            ("Confidence Threshold", "Argmax & Probability Check"),
            ("Action Output", "Response Dispatch & Telemetry")
        ]

    fig, ax = plt.subplots(figsize=(9.5, 4.8), dpi=300)
    fig.patch.set_facecolor(PALETTE["bg"])
    ax.set_facecolor(PALETTE["bg"])
    ax.axis("off")

    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4.8)

    ax.text(5.0, 4.4, title.upper(), ha="center", va="center", fontsize=13, fontweight="bold", color=PALETTE["primary"])
    ax.text(5.0, 4.08, "Sequential Algorithmic Execution Pipeline", ha="center", va="center", fontsize=8.5, color=PALETTE["text_muted"])

    step_w = 1.55
    step_h = 1.2
    spacing = 0.32
    start_x = (10 - (len(steps) * step_w + (len(steps) - 1) * spacing)) / 2
    y = 1.8

    for i, (name, desc) in enumerate(steps):
        x = start_x + i * (step_w + spacing)
        # Shadow
        shadow = FancyBboxPatch((x + 0.03, y - 0.03), step_w, step_h,
                                boxstyle="round,pad=0.04,rounding_size=0.1",
                                facecolor=PALETTE["shadow"], edgecolor="none", zorder=1)
        ax.add_patch(shadow)

        color = [PALETTE["secondary"], PALETTE["accent"], PALETTE["purple"], PALETTE["orange"], PALETTE["green"]][i % 5]
        box = FancyBboxPatch((x, y), step_w, step_h,
                             boxstyle="round,pad=0.04,rounding_size=0.1",
                             facecolor="#F8FAFC", edgecolor=color, linewidth=1.6, zorder=2)
        ax.add_patch(box)

        # Step indicator tag
        ax.text(x + step_w/2, y + step_h - 0.22, f"STEP {i+1}", ha="center", va="center",
                fontsize=7, fontweight="bold", color=color, zorder=3)
        ax.text(x + step_w/2, y + step_h/2 - 0.05, name, ha="center", va="center",
                fontsize=8, fontweight="bold", color=PALETTE["text_dark"], zorder=3)
        ax.text(x + step_w/2, y + 0.25, desc, ha="center", va="center",
                fontsize=6.5, color=PALETTE["text_muted"], zorder=3)

        if i < len(steps) - 1:
            ax.annotate("", xy=(x + step_w + spacing - 0.04, y + step_h/2), xytext=(x + step_w + 0.04, y + step_h/2),
                        arrowprops=dict(arrowstyle="-|>", color=PALETTE["primary"], lw=2.0, mutation_scale=12), zorder=4)

    plt.tight_layout()
    fig.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none", bbox_inches="tight")
    plt.close(fig)
    return output_path


def select_and_generate_diagrams_for_topic(topic: str, output_dir: str) -> list:
    """
    Intelligently analyzes the user's document topic and generates
    appropriate visual diagrams, returning metadata with paths and captions.
    """
    os.makedirs(output_dir, exist_ok=True)
    t = topic.lower().strip()
    diagrams = []

    try:
        if any(w in t for w in ["machine learning", "ml", "artificial intelligence", "ai", "deep learning", "data science"]):
            p1 = os.path.join(output_dir, "diag_ml_lifecycle.png")
            generate_ml_lifecycle_diagram(p1)
            diagrams.append({
                "path": p1,
                "caption": "Figure 1: End-to-End Machine Learning Lifecycle & Continuous Retraining Pipeline",
                "width": 450,
                "height": 225
            })

            p2 = os.path.join(output_dir, "diag_neural_network.png")
            generate_neural_network_diagram(p2)
            diagrams.append({
                "path": p2,
                "caption": "Figure 2: Fully Connected Deep Neural Network Layer Topology",
                "width": 450,
                "height": 235
            })

            p3 = os.path.join(output_dir, "diag_confusion_matrix.png")
            generate_confusion_matrix_diagram(p3)
            diagrams.append({
                "path": p3,
                "caption": "Figure 3: Confusion Matrix Classification Performance & Benchmark Scores",
                "width": 450,
                "height": 210
            })

        elif any(w in t for w in ["neural", "cnn", "rnn", "deep net", "transformer", "perceptron"]):
            p1 = os.path.join(output_dir, "diag_neural_network.png")
            generate_neural_network_diagram(p1)
            diagrams.append({
                "path": p1,
                "caption": "Figure 1: Deep Neural Network Architecture with Multi-Layer Perceptron Connections",
                "width": 450,
                "height": 235
            })
            p2 = os.path.join(output_dir, "diag_confusion_matrix.png")
            generate_confusion_matrix_diagram(p2)
            diagrams.append({
                "path": p2,
                "caption": "Figure 2: Network Validation Metrics & Diagnostic Confusion Matrix",
                "width": 450,
                "height": 210
            })

        elif any(w in t for w in ["tree", "decision", "random forest", "classification", "xgboost"]):
            p1 = os.path.join(output_dir, "diag_decision_tree.png")
            generate_decision_tree_diagram(p1)
            diagrams.append({
                "path": p1,
                "caption": "Figure 1: Hierarchical Decision Tree Classification with Binary Attribute Splitting",
                "width": 450,
                "height": 235
            })

        elif any(w in t for w in ["maya", "voice assistant", "jarvis", "system", "architecture", "companion", "agent"]):
            p1 = os.path.join(output_dir, "diag_system_architecture.png")
            generate_system_architecture_diagram(p1, title=topic)
            diagrams.append({
                "path": p1,
                "caption": "Figure 1: Multi-Tiered Subsystem Architecture of Maya Cyber Companion OS",
                "width": 450,
                "height": 235
            })
            p2 = os.path.join(output_dir, "diag_workflow.png")
            generate_flowchart_diagram(p2, title="Cognitive Intent Dispatch Workflow")
            diagrams.append({
                "path": p2,
                "caption": "Figure 2: Sub-Second Intent Routing & Action Execution Pipeline",
                "width": 450,
                "height": 225
            })

        else:
            # Universal flowchart fallback for any topic
            p1 = os.path.join(output_dir, "diag_general_workflow.png")
            generate_flowchart_diagram(p1, title=f"{topic} Operational Pipeline")
            diagrams.append({
                "path": p1,
                "caption": f"Figure 1: Methodological Workflow & Process Pipeline for {topic}",
                "width": 450,
                "height": 225
            })

    except Exception as e:
        print(f"⚠️ Diagram generation notice: {e}")

    return diagrams

