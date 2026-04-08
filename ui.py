# ui.py
import tkinter as tk
from tkinter import ttk, scrolledtext
import chess
import threading
from chess_logic import generate_puzzle
from ai_helper import give_hint, explain_solution
from storage import load_puzzles, init_if_empty

SQUARE_SIZE  = 65   # pixels per square
RANK_MARGIN  = 24   # left margin reserved for rank numbers (1-8)
FILE_MARGIN  = 20   # bottom margin reserved for file letters (a-h)
TOP_MARGIN   = 4    # tiny top padding




class ChessUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("♟️ Local AI Chess Puzzle Generator")
        self.geometry("1020x740")
        self.resizable(True, True)
        self.minsize(960, 660)
        self.configure(bg="#1a1a2e")

        self.board           = chess.Board()
        self.current_puzzle  = None
        self.solution        = None
        self.motif           = None
        self.solved          = False
        self.selected_square = None
        self.highlighted     = []      # list of (rank, file) currently highlighted

        # ── Puzzle list & navigation state ───────────────────────────────
        self.puzzles         = []      # full ordered list
        self.puzzle_index    = 0       # current index (0-based)

        self._ai_busy        = False   # prevent overlapping AI calls

        self.create_widgets()
        init_if_empty()
        self.puzzles = load_puzzles()
        self.puzzle_index = 0
        self._load_puzzle_at(self.puzzle_index)

    # ------------------------------------------------------------------ #
    #  Widget layout
    # ------------------------------------------------------------------ #
    def create_widgets(self):
        # ── Top title bar ─────────────────────────────────────────────────
        title_bar = tk.Frame(self, bg="#16213e", pady=8)
        title_bar.pack(fill="x")
        tk.Label(
            title_bar,
            text="♟️  Local AI Chess Puzzle Trainer",
            font=("Arial", 18, "bold"),
            bg="#16213e", fg="#e2e8f0"
        ).pack(side="left", padx=18)
        tk.Label(
            title_bar,
            text="Powered by Ollama  •  mistral  •  Fully Local",
            font=("Arial", 10),
            bg="#16213e", fg="#64748b"
        ).pack(side="right", padx=18)

        # ── Main content area ─────────────────────────────────────────────
        content = tk.Frame(self, bg="#1a1a2e", padx=14, pady=10)
        content.pack(fill="both", expand=True)

        # ── Left: board ───────────────────────────────────────────────────
        left_frame = tk.Frame(content, bg="#1a1a2e")
        left_frame.pack(side="left", anchor="n")
        self.create_chessboard(left_frame)

        # ── Right: controls ───────────────────────────────────────────────
        right_frame = tk.Frame(content, bg="#1a1a2e")
        right_frame.pack(side="left", fill="both", expand=True, padx=(16, 0))

        self._build_puzzle_header(right_frame)
        self._build_controls(right_frame)
        self._build_hint_panel(right_frame)

    # -- Puzzle header (title, progress bar, diff badge, description) ------
    def _build_puzzle_header(self, parent):
        hdr = tk.Frame(parent, bg="#16213e", bd=0, relief="flat",
                       pady=10, padx=12)
        hdr.pack(fill="x", pady=(0, 10))

        # Row 1: title
        row1 = tk.Frame(hdr, bg="#16213e")
        row1.pack(fill="x")
        self.puzzle_title_var = tk.StringVar(value="Loading…")
        tk.Label(row1, textvariable=self.puzzle_title_var,
                 font=("Arial", 14, "bold"), bg="#16213e", fg="#f1f5f9",
                 anchor="w").pack(side="left")

        # Row 2: "Puzzle X of N" counter
        row2 = tk.Frame(hdr, bg="#16213e")
        row2.pack(fill="x", pady=(4, 6))
        self.progress_var = tk.StringVar(value="Puzzle 0 of 0")
        tk.Label(row2, textvariable=self.progress_var,
                 font=("Arial", 11), bg="#16213e", fg="#94a3b8").pack(side="left")
        self.motif_var = tk.StringVar(value="")
        tk.Label(row2, textvariable=self.motif_var,
                 font=("Arial", 10, "italic"), bg="#16213e", fg="#60a5fa"
                 ).pack(side="right")

        # Row 3: step progress bar (coloured dots)
        self.pip_frame = tk.Frame(hdr, bg="#16213e")
        self.pip_frame.pack(fill="x", pady=(2, 4))
        self.pip_labels = []   # will be rebuilt when puzzle count is known

        # Feedback label
        self.feedback_var = tk.StringVar(value="")
        self.feedback_label = tk.Label(
            parent, textvariable=self.feedback_var,
            font=("Arial", 12, "bold"), bg="#1a1a2e", fg="#10b981", anchor="w")
        self.feedback_label.pack(fill="x", pady=(0, 6))

    def _build_controls(self, parent):
        ctl = tk.Frame(parent, bg="#0f3460", pady=10, padx=12)
        ctl.pack(fill="x", pady=(0, 10))

        tk.Label(ctl, text="Controls", font=("Arial", 11, "bold"),
                 bg="#0f3460", fg="#e2e8f0").pack(anchor="w", pady=(0, 6))

        # Navigation row
        nav = tk.Frame(ctl, bg="#0f3460")
        nav.pack(fill="x", pady=(0, 6))
        self._mk_btn(nav, "◀  Prev", self.prev_puzzle, "#374151").pack(side="left", padx=3, fill="x", expand=True)
        self._mk_btn(nav, "Next  ▶", self.next_puzzle, "#374151").pack(side="left", padx=3, fill="x", expand=True)
        self._mk_btn(nav, "↺ Retry", self.retry_puzzle,"#374151").pack(side="left", padx=3, fill="x", expand=True)

        # AI row
        ai_row = tk.Frame(ctl, bg="#0f3460")
        ai_row.pack(fill="x")
        self._mk_btn(ai_row, "💡 Get Hint",      self.get_hint,      "#1d4ed8").pack(side="left", padx=3, fill="x", expand=True)
        self._mk_btn(ai_row, "✅ Show Solution",  self.show_solution, "#065f46").pack(side="left", padx=3, fill="x", expand=True)

    def _mk_btn(self, parent, text, cmd, bg):
        return tk.Button(
            parent, text=text, command=cmd,
            bg=bg, fg="white", activebackground="#4b5563",
            font=("Arial", 10, "bold"), relief="flat",
            padx=6, pady=5, cursor="hand2",
            bd=0, highlightthickness=0
        )

    def _build_hint_panel(self, parent):
        lf = tk.Frame(parent, bg="#0f172a", bd=1, relief="solid")
        lf.pack(fill="both", expand=True)

        tk.Label(lf, text=" 🤖 AI Hint & Explanation ",
                 font=("Arial", 11, "bold"), bg="#0f172a", fg="#94a3b8"
                 ).pack(anchor="w", padx=10, pady=(8, 2))

        self.ai_status_var = tk.StringVar(value="")
        self.ai_status_label = tk.Label(
            lf, textvariable=self.ai_status_var,
            font=("Arial", 9, "italic"), bg="#0f172a", fg="#f59e0b")
        self.ai_status_label.pack(anchor="w", padx=10)

        self.hint_text = scrolledtext.ScrolledText(
            lf, height=13, font=("Consolas", 10),
            wrap=tk.WORD, background="#0f172a", foreground="#e2e8f0",
            insertbackground="white", relief="flat", bd=0,
            padx=10, pady=8
        )
        self.hint_text.pack(fill="both", expand=True, padx=4, pady=4)

    # ------------------------------------------------------------------ #
    #  Canvas-based chessboard
    # ------------------------------------------------------------------ #
    def create_chessboard(self, parent):
        canvas_w = RANK_MARGIN + 8 * SQUARE_SIZE
        canvas_h = TOP_MARGIN  + 8 * SQUARE_SIZE + FILE_MARGIN

        self.canvas = tk.Canvas(
            parent, width=canvas_w, height=canvas_h,
            highlightthickness=0, bg="#d6d0c4"
        )
        self.canvas.pack()

        LIGHT, DARK = "#f0d9b5", "#b58863"

        self.sq_rects = {}
        for rank in range(8):
            for file in range(8):
                x1 = RANK_MARGIN + file * SQUARE_SIZE
                y1 = TOP_MARGIN  + rank * SQUARE_SIZE
                x2, y2 = x1 + SQUARE_SIZE, y1 + SQUARE_SIZE
                fill = LIGHT if (rank + file) % 2 == 0 else DARK
                rect = self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=fill, outline="", tags="square")
                self.sq_rects[(rank, file)] = rect

        # Rank labels
        for rank in range(8):
            cy = TOP_MARGIN + rank * SQUARE_SIZE + SQUARE_SIZE // 2
            self.canvas.create_text(
                RANK_MARGIN // 2, cy, text=str(8 - rank),
                font=("Arial", 11, "bold"), fill="#333333", anchor="center")

        # File labels
        for file in range(8):
            cx = RANK_MARGIN + file * SQUARE_SIZE + SQUARE_SIZE // 2
            self.canvas.create_text(
                cx, TOP_MARGIN + 8 * SQUARE_SIZE + FILE_MARGIN // 2,
                text="abcdefgh"[file],
                font=("Arial", 11, "bold"), fill="#333333", anchor="center")

        # Piece text items
        self.piece_texts = {}
        for rank in range(8):
            for file in range(8):
                cx = RANK_MARGIN + file * SQUARE_SIZE + SQUARE_SIZE // 2
                cy = TOP_MARGIN  + rank * SQUARE_SIZE + SQUARE_SIZE // 2
                tid = self.canvas.create_text(
                    cx, cy, text="",
                    font=("Arial", 38), anchor="center", tags="piece")
                self.piece_texts[(rank, file)] = tid

        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self._draw_pieces()

    _PIECE_MAP = {
        'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
        'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚'
    }

    def _draw_pieces(self):
        for rank in range(8):
            for file in range(8):
                sq    = chess.square(file, 7 - rank)
                piece = self.board.piece_at(sq)
                sym   = self._PIECE_MAP.get(piece.symbol(), "") if piece else ""
                self.canvas.itemconfig(self.piece_texts[(rank, file)], text=sym)

    def update_board_display(self):
        self._draw_pieces()

    # ------------------------------------------------------------------ #
    #  Canvas click → board coordinates
    # ------------------------------------------------------------------ #
    def _on_canvas_click(self, event):
        rx = event.x - RANK_MARGIN
        ry = event.y - TOP_MARGIN
        if rx < 0 or rx >= 8 * SQUARE_SIZE or ry < 0 or ry >= 8 * SQUARE_SIZE:
            return
        file = int(rx // SQUARE_SIZE)
        rank = int(ry // SQUARE_SIZE)
        self.on_square_click(rank, file)

    # ------------------------------------------------------------------ #
    #  Square interaction
    # ------------------------------------------------------------------ #
    def on_square_click(self, rank, file):
        if self.solved or not self.current_puzzle:
            return

        square = chess.square(file, 7 - rank)

        if self.selected_square is None:
            piece = self.board.piece_at(square)
            if piece and piece.color == self.board.turn:
                self.selected_square = square
                self.highlight_legal_moves(square)
        else:
            move = chess.Move(self.selected_square, square)
            if move in self.board.legal_moves:
                san = self.board.san(move)
                self.board.push(move)
                self.update_board_display()
                self.clear_highlights()

                if san == self.solution:
                    self.feedback_var.set("✅  Correct! Brilliant move!")
                    self.feedback_label.config(fg="#10b981")
                    self.solved = True
                    self._update_pip(solved=True)
                else:
                    self.feedback_var.set("⚠️  Legal, but not the puzzle solution — try again!")
                    self.feedback_label.config(fg="#f59e0b")

                self.selected_square = None
            else:
                piece = self.board.piece_at(square)
                if piece and piece.color == self.board.turn:
                    self.clear_highlights()
                    self.selected_square = square
                    self.highlight_legal_moves(square)
                else:
                    self.clear_highlights()
                    self.selected_square = None

    def highlight_legal_moves(self, from_square):
        self.clear_highlights()
        for move in self.board.legal_moves:
            if move.from_square == from_square:
                to_rank = 7 - chess.square_rank(move.to_square)
                to_file = chess.square_file(move.to_square)
                self.canvas.itemconfig(self.sq_rects[(to_rank, to_file)], fill="#7ec8e3")
                self.highlighted.append((to_rank, to_file))

    def clear_highlights(self):
        LIGHT, DARK = "#f0d9b5", "#b58863"
        for r, f in self.highlighted:
            color = LIGHT if (r + f) % 2 == 0 else DARK
            self.canvas.itemconfig(self.sq_rects[(r, f)], fill=color)
        self.highlighted.clear()

    # ------------------------------------------------------------------ #
    #  Progress pip row (coloured dots for each puzzle)
    # ------------------------------------------------------------------ #
    def _rebuild_pips(self):
        for w in self.pip_labels:
            w.destroy()
        self.pip_labels.clear()
        n = len(self.puzzles)
        for i in range(n):
            dot = tk.Label(self.pip_frame, text="●", font=("Arial", 8),
                           bg="#16213e", fg="#374151", cursor="hand2")
            dot.pack(side="left", padx=1)
            idx = i
            dot.bind("<Button-1>", lambda e, x=idx: self._load_puzzle_at(x))
            self.pip_labels.append(dot)
        self._refresh_pips()

    def _refresh_pips(self):
        for i, dot in enumerate(self.pip_labels):
            if i == self.puzzle_index:
                dot.config(fg="#3b82f6")  # current = blue
            elif i < self.puzzle_index:
                dot.config(fg="#10b981")  # visited = green
            else:
                dot.config(fg="#374151")  # future  = dark grey

    def _update_pip(self, solved=False):
        self._refresh_pips()

    # ------------------------------------------------------------------ #
    #  Puzzle navigation
    # ------------------------------------------------------------------ #
    def _load_puzzle_at(self, index: int):
        if not self.puzzles:
            self.feedback_var.set("❌ No puzzles found – check puzzles.json")
            return

        # Clamp index
        index = max(0, min(index, len(self.puzzles) - 1))
        self.puzzle_index = index

        p = self.puzzles[index]
        self.current_puzzle  = p
        self.board           = chess.Board(p["fen"])
        self.solution        = p["solution"]
        self.motif           = p.get("motif", "tactic")
        self.solved          = False
        self.selected_square = None
        self.highlighted     = []

        # Header update
        num = index + 1
        total = len(self.puzzles)
        self.puzzle_title_var.set(p.get("title", f"Puzzle {num}"))
        self.progress_var.set(f"Puzzle {num} of {total}")
        self.motif_var.set(f"Theme: {self.motif.replace('_', ' ').title()}")
        self.feedback_var.set("Click a piece, then click its destination square")
        self.feedback_label.config(fg="#94a3b8")

        # Rebuild pips on first load; refresh afterwards
        if not self.pip_labels:
            self._rebuild_pips()
        else:
            self._refresh_pips()

        self.hint_text.delete(1.0, tk.END)
        self.ai_status_var.set("")
        self.clear_highlights()
        self.update_board_display()

    def next_puzzle(self):
        self._load_puzzle_at(self.puzzle_index + 1)

    def prev_puzzle(self):
        self._load_puzzle_at(self.puzzle_index - 1)

    def retry_puzzle(self):
        if not self.current_puzzle:
            return
        self.board           = chess.Board(self.current_puzzle["fen"])
        self.solved          = False
        self.selected_square = None
        self.hint_text.delete(1.0, tk.END)
        self.ai_status_var.set("")
        self.feedback_var.set("Retrying — find the best move!")
        self.feedback_label.config(fg="#94a3b8")
        self.clear_highlights()
        self.update_board_display()

    # ------------------------------------------------------------------ #
    #  AI: Hint & Solution (run in background thread to keep UI responsive)
    # ------------------------------------------------------------------ #
    def _set_ai_busy(self, busy: bool, status: str = ""):
        self._ai_busy = busy
        self.ai_status_var.set(status)

    def get_hint(self):
        if self._ai_busy or not self.current_puzzle or self.solved:
            return
        self._set_ai_busy(True, "🤖 AI is thinking…")
        self.hint_text.delete(1.0, tk.END)
        self.hint_text.insert(tk.END, "Contacting Ollama for a hint…\n")

        def _run():
            hint = give_hint(self.board.fen(), self.motif, self.solution)
            self.after(0, self._display_hint, hint)

        threading.Thread(target=_run, daemon=True).start()

    def _display_hint(self, hint: str):
        self._set_ai_busy(False)
        self.hint_text.delete(1.0, tk.END)
        self.hint_text.insert(tk.END, "💡  HINT\n")
        self.hint_text.insert(tk.END, "─" * 40 + "\n\n")
        self.hint_text.insert(tk.END, hint)

    def show_solution(self):
        if self._ai_busy or not self.current_puzzle:
            return

        # Clear any stale feedback immediately
        self.feedback_var.set("📌  Solution revealed — study the position!")
        self.feedback_label.config(fg="#60a5fa")

        # Immediately show the solution move and flip the board
        sol_line  = f"📌  Best Move:  {self.solution}\n"
        self.hint_text.delete(1.0, tk.END)
        self.hint_text.insert(tk.END, sol_line)
        self.hint_text.insert(tk.END, "─" * 40 + "\n\n")

        desc = self.current_puzzle.get("description", "")
        if desc:
            self.hint_text.insert(tk.END, f"📝  Puzzle tip: {desc}\n\n")

        self.hint_text.insert(tk.END, "🤖  Asking AI to explain the idea…\n")

        # Apply the move on the board
        try:
            move_obj = self.board.parse_san(self.solution)
            self.board.push(move_obj)
            self.update_board_display()
            self.solved = True
            self._update_pip(solved=True)
            self.feedback_var.set("✅  Solution applied — study the position!")
            self.feedback_label.config(fg="#10b981")
        except Exception:
            pass

        self._set_ai_busy(True, "🤖 AI is explaining…")
        fen_snap = self.current_puzzle["fen"]   # use original FEN for explanation

        def _run():
            explanation = explain_solution(fen_snap, self.solution, self.motif)
            self.after(0, self._display_explanation, explanation)

        threading.Thread(target=_run, daemon=True).start()

    def _display_explanation(self, explanation: str):
        self._set_ai_busy(False)
        self.hint_text.delete(1.0, tk.END)
        self.hint_text.insert(tk.END, f"📌  Best Move:  {self.solution}\n")
        self.hint_text.insert(tk.END, "─" * 40 + "\n\n")
        desc = self.current_puzzle.get("description", "")
        if desc:
            self.hint_text.insert(tk.END, f"📝  {desc}\n\n")
        self.hint_text.insert(tk.END, "🤖  AI Explanation:\n\n")
        self.hint_text.insert(tk.END, explanation)