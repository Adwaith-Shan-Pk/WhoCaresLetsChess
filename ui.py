# ui.py
import tkinter as tk
from tkinter import ttk, scrolledtext
import chess
import random
from chess_logic import generate_puzzle
from ai_helper import give_hint, explain_solution
from storage import load_puzzles, init_if_empty

class ChessUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("♟️ Local AI Chess Puzzle Generator")
        self.geometry("920x680")
        self.resizable(True, True)
        self.minsize(850, 620)

        self.board = chess.Board()
        self.current_puzzle = None
        self.solution = None
        self.motif = None
        self.solved = False
        self.selected_square = None
        self.highlighted = []

        self.create_widgets()
        init_if_empty()
        self.load_new_puzzle()

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding=12)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="♟️ Local AI Chess Puzzle Generator",
                  font=("Arial", 16, "bold")).pack(pady=(0, 12))

        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill="both", expand=True)

        # Left: Chessboard (your perfect size)
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side="left", padx=(0, 20))

        self.board_frame = ttk.Frame(left_frame)
        self.board_frame.pack()
        self.squares = [[None for _ in range(8)] for _ in range(8)]
        self.create_chessboard()

        # Right: Controls
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side="right", fill="both", expand=True)

        self.status_label = ttk.Label(right_frame, text="Click piece → Click destination", font=("Arial", 11))
        self.status_label.pack(anchor="w", pady=5)

        self.feedback = ttk.Label(right_frame, text="", font=("Arial", 11))
        self.feedback.pack(anchor="w", pady=5)

        control_frame = ttk.LabelFrame(right_frame, text=" Controls ", padding=12)
        control_frame.pack(fill="x", pady=10)

        # Action buttons
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill="x", pady=10)

        ttk.Button(btn_frame, text="New Puzzle", command=self.load_new_puzzle).pack(side="left", padx=4, fill="x", expand=True)
        ttk.Button(btn_frame, text="Retry Puzzle", command=self.retry_puzzle).pack(side="left", padx=4, fill="x", expand=True)
        ttk.Button(btn_frame, text="Get Hint", command=self.get_hint).pack(side="left", padx=4, fill="x", expand=True)
        ttk.Button(btn_frame, text="Show Solution", command=self.show_solution).pack(side="left", padx=4, fill="x", expand=True)

        # Hint area
        hint_frame = ttk.LabelFrame(right_frame, text=" Hint & AI Explanation ", padding=10)
        hint_frame.pack(fill="both", expand=True, pady=10)

        self.hint_text = scrolledtext.ScrolledText(
            hint_frame, height=14, font=("Arial", 10), wrap=tk.WORD, background="#f8f9fa"
        )
        self.hint_text.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="Fully local • Click to move • llama3.2:3b",
                  font=("Arial", 9), foreground="gray").pack(pady=(12, 0))

    def create_chessboard(self):
        """Your perfect board dimensions"""
        piece_map = {
            'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
            'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚'
        }
        colors = ["#f0d9b5", "#b58863"]

        for rank in range(8):
            for file in range(8):
                square = chess.square(file, 7 - rank)
                piece = self.board.piece_at(square)
                symbol = piece_map.get(piece.symbol(), " ") if piece else " "

                bg = colors[(rank + file) % 2]
                lbl = tk.Label(
                    self.board_frame,
                    text=symbol,
                    font=("Arial", 32),
                    width=2,
                    height=1,
                    bg=bg,
                    relief="solid",
                    borderwidth=1
                )
                lbl.grid(row=rank, column=file, padx=1, pady=1)
                lbl.bind("<Button-1>", lambda e, r=rank, f=file: self.on_square_click(r, f))
                self.squares[rank][file] = lbl

    def update_board_display(self):
        piece_map = {
            'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
            'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚'
        }
        for rank in range(8):
            for file in range(8):
                square = chess.square(file, 7 - rank)
                piece = self.board.piece_at(square)
                symbol = piece_map.get(piece.symbol(), " ") if piece else " "
                self.squares[rank][file].config(text=symbol)

    def on_square_click(self, rank, file):
        if self.solved or not self.current_puzzle:
            return

        square = chess.square(file, 7 - rank)

        if self.selected_square is None:
            # Select piece
            piece = self.board.piece_at(square)
            if piece and piece.color == self.board.turn:
                self.selected_square = square
                self.highlight_legal_moves(square)
        else:
            # Try move
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
                # Reselect another piece
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
                self.squares[to_rank][to_file].config(bg="#90EE90")
                self.highlighted.append((to_rank, to_file))

    def clear_highlights(self):
        colors = ["#f0d9b5", "#b58863"]
        for r, f in self.highlighted:
            self.squares[r][f].config(bg=colors[(r + f) % 2])
        self.highlighted.clear()

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

        self.current_puzzle = random.choice(puzzles)
        self.board = chess.Board(self.current_puzzle["fen"])
        self.solution = self.current_puzzle["solution"]
        self.motif = self.current_puzzle["motif"]
        self.solved = False
        self.selected_square = None

        self.hint_text.delete(1.0, tk.END)
        self.feedback.config(text=f"Motif: {self.motif.upper()}", foreground="blue")
        self.status_label.config(text="Click piece → Click destination", foreground="black")

        self.update_board_display()

    def retry_puzzle(self):
        """Retry the same puzzle"""
        if not self.current_puzzle:
            return
        self.board = chess.Board(self.current_puzzle["fen"])
        self.solved = False
        self.selected_square = None
        self.hint_text.delete(1.0, tk.END)
        self.feedback.config(text=f"Motif: {self.motif.upper()}", foreground="blue")
        self.status_label.config(text="Try again! Click piece → destination", foreground="black")
        self.update_board_display()

    def get_hint(self):
        if not self.current_puzzle or self.solved:
            return
        self.hint_text.delete(1.0, tk.END)
        self.hint_text.insert(tk.END, "🤖 Thinking...\n\n")
        self.update_idletasks()
        hint = give_hint(self.board.fen(), self.motif)
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
        except:
            pass