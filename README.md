# ♟️ WhoCaresLetsChess

A fully local, AI-powered chess puzzle trainer built with Python and Tkinter.  
Solve 5 hand-curated tactical puzzles, get AI hints, and see full move explanations — all offline, no internet required after setup.

---

## Features

- **Interactive chessboard** — click a piece, then click its destination to move
- **5 curated tactical puzzles** — covering pins, forks, checkmates, and Scholar's Mate
- **Sequential puzzle navigation** — work through puzzles in order with ◀ Prev / Next ▶ buttons
- **Progress tracker** — "Puzzle X of 5" counter with clickable pip dots
- **AI-powered hints** — Mistral identifies the key piece without revealing the destination
- **AI solution explanations** — full plain-English breakdown of why the move works
- **Anti-hallucination prompts** — board state is pre-parsed with `python-chess` and fed to the AI as plain English, not raw FEN
- **Fully offline** after initial setup

---

## Project Structure

```
WhoCaresLetsChess/
├── main.py          # Entry point
├── ui.py            # Tkinter GUI — Canvas chessboard, navigation, AI panel
├── chess_logic.py   # Tactical motif detection & puzzle generation helpers
├── ai_helper.py     # Ollama prompt builder, hint & explanation functions
├── storage.py       # puzzles.json read/write & initialisation
├── puzzles.json     # 5 curated tactical puzzles
├── requirements.txt # Python dependencies
└── .gitignore
```

---

## Prerequisites

### 1. Python 3.10+
Download from https://www.python.org/downloads/

### 2. Ollama
Download from https://ollama.com/download — install and leave it running in the system tray.

### 3. Pull the Mistral model (once, ~4 GB)
```bash
ollama pull mistral
```

---

## Installation

```bash
# Clone the repo
git clone https://github.com/Antobruh/WhoCaresLetsChess.git
cd WhoCaresLetsChess

# Install Python dependencies
pip install -r requirements.txt
```

---

## Running

```bash
python main.py
```

The app loads immediately with all 5 puzzles ready to go.

---

## Controls

| Action | How |
|--------|-----|
| Move a piece | Click piece → click destination square |
| Next puzzle | Click **Next ▶** |
| Previous puzzle | Click **◀ Prev** |
| Retry same puzzle | Click **↺ Retry** |
| Get an AI hint | Click **💡 Get Hint** |
| Reveal the solution | Click **✅ Show Solution** |
| Jump to any puzzle | Click the pip dot for that puzzle |

---

## The 5 Puzzles

| # | Title | Theme |
|---|-------|-------|
| 1 | The Classic Pin | Pin |
| 2 | Knight Fork Fiesta | Fork |
| 3 | Scholar's Trap | Checkmate (Queen) |
| 4 | Discovered Check | Fork + Check |
| 5 | Back-Rank Blaster | Back-rank checkmate |

---

## How It Works

1. **Puzzles** — `puzzles.json` ships 5 hand-verified positions. Solutions are stored in exact SAN notation (including `x` for captures and `#` for checkmates) so move comparisons are exact.
2. **Hints** — `ai_helper.py` parses the solution with `python-chess` to extract the moving piece and its square, then prompts Mistral to give a one-sentence hint — never revealing the destination.
3. **Explanations** — the board is described in plain English (not raw FEN) before being sent to Mistral, eliminating piece-hallucination errors.
4. **UI** — `ui.py` uses a `tk.Canvas` for pixel-perfect rendering of squares, coordinates, and Unicode chess pieces. AI calls run in background threads to keep the UI responsive.

---

## Requirements

```
python-chess
requests
```
