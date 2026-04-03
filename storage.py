# storage.py
import json
import os
import chess
from chess_logic import EXAMPLE_FENS, generate_puzzle   # ← This was missing!

PUZZLE_FILE = "puzzles.json"

def load_puzzles() -> list:
    """Load puzzles from JSON file."""
    if os.path.exists(PUZZLE_FILE):
        try:
            with open(PUZZLE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading puzzles.json: {e}")
            return []
    return []

def save_puzzle(puzzle: dict):
    """Save a puzzle to JSON, avoiding duplicates."""
    puzzles = load_puzzles()
    if not any(p.get("fen") == puzzle.get("fen") for p in puzzles):
        puzzles.append(puzzle)
        try:
            with open(PUZZLE_FILE, "w", encoding="utf-8") as f:
                json.dump(puzzles, f, indent=2)
            print(f"✓ Saved puzzle: {puzzle.get('motif')} - {puzzle.get('solution')}")
        except Exception as e:
            print(f"Error saving puzzle: {e}")

def init_if_empty():
    """Create initial puzzles if none exist. Now properly imports generate_puzzle."""
    if load_puzzles():
        print(f"✓ Found {len(load_puzzles())} existing puzzles.")
        return

    print("No puzzles.json found → Creating example tactical puzzles...")

    puzzles_created = 0
    for i, fen in enumerate(EXAMPLE_FENS):
        try:
            board = chess.Board(fen)
            puzzle = generate_puzzle(board)
            if puzzle:
                save_puzzle(puzzle)
                puzzles_created += 1
                print(f"   Created puzzle {puzzles_created}: {puzzle['motif']} → {puzzle['solution']}")
            else:
                print(f"   No tactic found in position {i+1}")
        except Exception as e:
            print(f"   Error with FEN {i+1}: {e}")

    if puzzles_created > 0:
        print(f"✅ Successfully created {puzzles_created} puzzles in puzzles.json")
    else:
        print("⚠️ Could not create any puzzles. Please check chess_logic.py")