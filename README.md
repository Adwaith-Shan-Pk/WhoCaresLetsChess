# ♟️ Local AI Chess Puzzle Generator

A fully local, AI-powered chess puzzle trainer built with Python.
Detects tactical motifs such as **pins, forks, skewers, and back-rank mates**, and uses a local LLM via **Ollama** to generate context-aware hints and explanations — all offline, no internet needed.

---

## Features

- **Interactive chessboard** — click a piece, click the destination to move
- **Board coordinates** — rank numbers (1–8) and file letters (a–h) displayed for easy navigation
- **Tactical puzzles** — Pin, Fork, Skewer, Back-rank mate
- **Puzzle controls:**
  - **New Puzzle** — load a random puzzle
  - **Retry Puzzle** — reset the current puzzle
  - **Get Hint** — AI-generated hint that identifies the key piece without spoiling the move
  - **Show Solution** — reveals the move with a full AI explanation
- **Anti-hallucination hints** — the AI is given a plain-English board description so it always mentions the correct piece
- **Fully offline** after initial setup

---

## Project Structure

```
WhoCaresLetsChess/
├── main.py          # Entry point
├── ui.py            # Tkinter GUI (Canvas-based chessboard)
├── chess_logic.py   # Tactical motif detection & puzzle generation
├── ai_helper.py     # Ollama prompt builder & query functions
├── storage.py       # puzzles.json read/write
├── requirements.txt # Python dependencies
├── .gitignore
└── puzzles.json     # Auto-generated on first run
```

---

## Prerequisites

### 1. Python 3.10+
Download from https://www.python.org/downloads/

### 2. Ollama
Download from https://ollama.com/download — install and leave it running (it sits in the system tray).

### 3. Pull the model (once)
```bash
ollama pull llama3.2:3b
```

---

## Installation

```bash
# Clone the repo
git clone <your-repo-url>
cd WhoCaresLetsChess

# Install Python dependencies
pip install -r requirements.txt
```

---

## Running

```bash
python main.py
```

That's it. The app will auto-generate puzzles on the first run.

---

## Controls

| Action | How |
|--------|-----|
| Move a piece | Click piece → Click destination square |
| New puzzle | Click **New Puzzle** |
| Retry same puzzle | Click **Retry Puzzle** |
| Get a hint | Click **Get Hint** |
| See the solution | Click **Show Solution** |

---

## How It Works

1. **Puzzle generation** — `chess_logic.py` scans legal moves from a set of known tactical FEN positions and detects motifs (fork, pin, skewer, back-rank mate) using the `python-chess` library.
2. **Hints** — `ai_helper.py` parses the solution move with `python-chess` to extract the exact piece and square, then constructs a tightly constrained prompt so the AI names the right piece every time.
3. **Storage** — Puzzles are saved to `puzzles.json` and loaded on startup so generation only runs once.
