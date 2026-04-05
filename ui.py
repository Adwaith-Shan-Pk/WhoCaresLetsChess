# ui.py
import tkinter as tk
from tkinter import ttk, scrolledtext
import chess
import random
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
        self.geometry("980x700")
        self.resizable(True, True)
        self.minsize(900, 640)

        self.board           = chess.Board()
        self.current_puzzle  = None
        self.solution        = None
        self.motif           = None
        self.solved          = False
        self.selected_square = None
        self.highlighted     = []          # list of (rank, file) currently green

        self.create_widgets()
        init_if_empty()
        self.load_new_puzzle()

    # ------------------------------------------------------------------ #
    #  Widget layout
    # ------------------------------------------------------------------ #
    def create_widgets(self):
        main_frame = ttk.Frame(self, padding=12)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="♟️ Local AI Chess Puzzle Generator",
                  font=("Arial", 16, "bold")).pack(pady=(0, 12))

        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill="both", expand=True)

        # ── Left: chessboard canvas ────────────────────────────────────
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side="left", padx=(0, 20), anchor="n")

        self.board_frame = ttk.Frame(left_frame)
        self.board_frame.pack()
        self.create_chessboard()

        # ── Right: controls + hint panel ──────────────────────────────
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side="right", fill="both", expand=True)

        self.status_label = ttk.Label(
            right_frame, text="Click piece → Click destination",
            font=("Arial", 11))
        self.status_label.pack(anchor="w", pady=5)

        self.feedback = ttk.Label(right_frame, text="", font=("Arial", 11))
        self.feedback.pack(anchor="w", pady=5)

        control_frame = ttk.LabelFrame(right_frame, text=" Controls ", padding=12)
        control_frame.pack(fill="x", pady=10)

        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill="x", pady=10)
        ttk.Button(btn_frame, text="New Puzzle",    command=self.load_new_puzzle).pack(side="left", padx=4, fill="x", expand=True)
        ttk.Button(btn_frame, text="Retry Puzzle",  command=self.retry_puzzle).pack(side="left", padx=4, fill="x", expand=True)
        ttk.Button(btn_frame, text="Get Hint",      command=self.get_hint).pack(side="left", padx=4, fill="x", expand=True)
        ttk.Button(btn_frame, text="Show Solution", command=self.show_solution).pack(side="left", padx=4, fill="x", expand=True)

        hint_frame = ttk.LabelFrame(right_frame, text=" Hint & AI Explanation ", padding=10)
        hint_frame.pack(fill="both", expand=True, pady=10)

        self.hint_text = scrolledtext.ScrolledText(
            hint_frame, height=14, font=("Arial", 10),
            wrap=tk.WORD, background="#f8f9fa")
        self.hint_text.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="Fully local • Click to move • llama3.2:3b",
                  font=("Arial", 9), foreground="gray").pack(pady=(12, 0))

    # ------------------------------------------------------------------ #
    #  Canvas-based chessboard
    # ------------------------------------------------------------------ #
    def create_chessboard(self):
        """Pixel-perfect board: squares + coordinates rendered on one Canvas."""
        canvas_w = RANK_MARGIN + 8 * SQUARE_SIZE
        canvas_h = TOP_MARGIN  + 8 * SQUARE_SIZE + FILE_MARGIN

        self.canvas = tk.Canvas(
            self.board_frame,
            width=canvas_w, height=canvas_h,
            highlightthickness=0, bg="#d6d0c4"
        )
        self.canvas.pack()

        LIGHT, DARK = "#f0d9b5", "#b58863"

        # ── Square rectangles ──────────────────────────────────────────
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

        # ── Rank labels: 8 at top → 1 at bottom ──────────────────────
        for rank in range(8):
            cy = TOP_MARGIN + rank * SQUARE_SIZE + SQUARE_SIZE // 2
            self.canvas.create_text(
                RANK_MARGIN // 2, cy,
                text=str(8 - rank),
                font=("Arial", 11, "bold"), fill="#333333", anchor="center")

        # ── File labels: a … h ────────────────────────────────────────
        for file in range(8):
            cx = RANK_MARGIN + file * SQUARE_SIZE + SQUARE_SIZE // 2
            self.canvas.create_text(
                cx, TOP_MARGIN + 8 * SQUARE_SIZE + FILE_MARGIN // 2,
                text="abcdefgh"[file],
                font=("Arial", 11, "bold"), fill="#333333", anchor="center")

        # ── Piece text items (one per square) ─────────────────────────
        self.piece_texts = {}
        for rank in range(8):
            for file in range(8):
                cx = RANK_MARGIN + file * SQUARE_SIZE + SQUARE_SIZE // 2
                cy = TOP_MARGIN  + rank * SQUARE_SIZE + SQUARE_SIZE // 2
                tid = self.canvas.create_text(
                    cx, cy, text="",
                    font=("Arial", 36), anchor="center", tags="piece")
                self.piece_texts[(rank, file)] = tid

        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self._draw_pieces()

    # ── Piece map ──────────────────────────────────────────────────────
    _PIECE_MAP = {
        'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
        'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚'
    }

    def _draw_pieces(self):
        for rank in range(8):
            for file in range(8):
                sq     = chess.square(file, 7 - rank)
                piece  = self.board.piece_at(sq)
                symbol = self._PIECE_MAP.get(piece.symbol(), "") if piece else ""
                self.canvas.itemconfig(self.piece_texts[(rank, file)], text=symbol)

    def update_board_display(self):
        self._draw_pieces()

    # ── Canvas click → board coordinates ──────────────────────────────
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
                    self.feedback.config(text="✅ Correct! Great job!", foreground="green")
                    self.solved = True
                else:
                    self.feedback.config(text="Legal move, but not the puzzle solution", foreground="orange")

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
                self.canvas.itemconfig(self.sq_rects[(to_rank, to_file)], fill="#90EE90")
                self.highlighted.append((to_rank, to_file))

    def clear_highlights(self):
        LIGHT, DARK = "#f0d9b5", "#b58863"
        for r, f in self.highlighted:
            color = LIGHT if (r + f) % 2 == 0 else DARK
            self.canvas.itemconfig(self.sq_rects[(r, f)], fill=color)
        self.highlighted.clear()

    # ------------------------------------------------------------------ #
    #  Puzzle management
    # ------------------------------------------------------------------ #
    def load_new_puzzle(self):
        puzzles = load_puzzles()
        if not puzzles:
            self.status_label.config(text="No puzzles found. Initializing...", foreground="orange")
            self.feedback.config(text="Creating example puzzles now...", foreground="blue")
            init_if_empty()
            puzzles = load_puzzles()

        if not puzzles:
            self.status_label.config(text="Still no puzzles. Check storage.py", foreground="red")
            return

        self.current_puzzle  = random.choice(puzzles)
        self.board           = chess.Board(self.current_puzzle["fen"])
        self.solution        = self.current_puzzle["solution"]
        self.motif           = self.current_puzzle["motif"]
        self.solved          = False
        self.selected_square = None
        self.highlighted     = []

        self.hint_text.delete(1.0, tk.END)
        self.feedback.config(text=f"Motif: {self.motif.upper()}", foreground="blue")
        self.status_label.config(text="Click piece → Click destination", foreground="black")
        self.update_board_display()

    def retry_puzzle(self):
        if not self.current_puzzle:
            return
        self.board           = chess.Board(self.current_puzzle["fen"])
        self.solved          = False
        self.selected_square = None
        self.hint_text.delete(1.0, tk.END)
        self.feedback.config(text=f"Motif: {self.motif.upper()}", foreground="blue")
        self.status_label.config(text="Try again! Click piece → destination", foreground="black")
        self.clear_highlights()
        self.update_board_display()

    def get_hint(self):
        if not self.current_puzzle or self.solved:
            return
        self.hint_text.delete(1.0, tk.END)
        self.hint_text.insert(tk.END, "🤖 Thinking...\n\n")
        self.update_idletasks()
        hint = give_hint(self.board.fen(), self.motif, self.solution)
        self.hint_text.delete(1.0, tk.END)
        self.hint_text.insert(tk.END, f"💡 HINT:\n\n{hint}")

    def show_solution(self):
        if not self.current_puzzle:
            return
        self.hint_text.delete(1.0, tk.END)
        self.hint_text.insert(tk.END, f"📌 SOLUTION: {self.solution}\n\n")
        self.hint_text.insert(tk.END, "🤖 AI Explanation:\n")
        self.update_idletasks()
        explanation = explain_solution(self.board.fen(), self.solution, self.motif)
        self.hint_text.insert(tk.END, explanation)

        try:
            move_obj = self.board.parse_san(self.solution)
            self.board.push(move_obj)
            self.update_board_display()
            self.solved = True
        except Exception:
            pass