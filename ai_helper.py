# ai_helper.py
import requests
import chess

OLLAMA_URL = "http://localhost:11434/api/generate"

# --------------------------------------------------------------------------- #
# FEN → plain English board description
# This is the KEY fix for hallucinations: we parse the board with python-chess
# and give the AI a simple text description instead of raw FEN.
# --------------------------------------------------------------------------- #
PIECE_NAMES = {
    chess.PAWN:   "Pawn",
    chess.KNIGHT: "Knight",
    chess.BISHOP: "Bishop",
    chess.ROOK:   "Rook",
    chess.QUEEN:  "Queen",
    chess.KING:   "King",
}

def describe_board(fen: str) -> str:
    """Convert a FEN string into a plain-English list of piece positions."""
    board = chess.Board(fen)
    white_pieces = []
    black_pieces = []
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is None:
            continue
        sq_name = chess.square_name(square)   # e.g. "e4"
        name = PIECE_NAMES.get(piece.piece_type, "?")
        if piece.color == chess.WHITE:
            white_pieces.append(f"{name} on {sq_name}")
        else:
            black_pieces.append(f"{name} on {sq_name}")

    side_to_move = "White" if board.turn == chess.WHITE else "Black"
    lines = [
        f"It is {side_to_move}'s turn to move.",
        f"White pieces: {', '.join(white_pieces) if white_pieces else 'none'}.",
        f"Black pieces: {', '.join(black_pieces) if black_pieces else 'none'}.",
    ]
    return "\n".join(lines)


def query_ollama(prompt: str) -> str:
    """Send a prompt to Ollama and return the response text."""
    payload = {
        "model": "mistral",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,   # low = more factual, less creative
            "top_p": 0.9,
        }
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json().get("response", "No response received.")
        else:
            return (
                f"⚠️  Ollama returned HTTP {response.status_code}.\n\n"
                "Try restarting Ollama and make sure the model "
                "'llama3.2:3b' is downloaded:\n"
                "  ollama pull llama3.2:3b"
            )
    except requests.exceptions.ConnectionError:
        return (
            "❌  Ollama is not running.\n\n"
            "Start it with:  ollama serve\n"
            "Then pull the model if needed:  ollama pull llama3.2:3b\n\n"
            "The puzzle hint / solution text above still shows — "
            "AI explanation requires Ollama to be active."
        )
    except requests.exceptions.Timeout:
        return "⏳  Ollama timed out (>60 s). The model may be cold-starting — try again in a moment."
    except Exception as e:
        return f"Unexpected error: {str(e)}"


def give_hint(fen: str, motif: str, solution: str) -> str:
    """
    Give a hint using Minimax to find the best move, then pass that verified
    move to Mistral for a natural-language hint — no hallucinations possible.
    Falls back to a plain text hint if Ollama is unavailable.
    """
    from chess_logic import get_best_move

    board = chess.Board(fen)
    board_desc = describe_board(fen)

    # Use Minimax to find the best move — no guessing
    best_move  = get_best_move(board, depth=4)
    piece      = board.piece_at(best_move.from_square)
    piece_name = PIECE_NAMES.get(piece.piece_type, "piece") if piece else "piece"
    from_sq    = chess.square_name(best_move.from_square)
    color_name = "White" if (piece and piece.color == chess.WHITE) else "Black"
    piece_info = f"The {color_name} {piece_name} currently on {from_sq}"

    # Pass verified move info to Mistral for a natural language hint
    prompt = f"""You are a chess coach giving a ONE-sentence hint to a beginner.

FACTS (do not contradict these):
- {piece_info} is the key piece for this puzzle.
- The tactical theme is: {motif}
- Do NOT reveal where the piece moves to.
- Do NOT mention any other piece as the key mover.

Board for context:
{board_desc}

Write exactly ONE encouraging hint sentence that mentions the piece type and its square ({from_sq}), without revealing the destination.

Hint:"""

    try:
        result = query_ollama(prompt)
        # If query_ollama returned an error string (starts with ❌ or ⚠️), use fallback
        if result.startswith("❌") or result.startswith("⚠️") or result.startswith("⏳"):
            return f"💡 Consider the {piece_name} on {from_sq}!"
        return result
    except Exception:
        return f"💡 Consider the {piece_name} on {from_sq}!"


def explain_solution(fen: str, solution: str, motif: str) -> str:
    board_desc = describe_board(fen)
    prompt = f"""You are a chess tutor explaining a puzzle solution to a beginner.

CURRENT BOARD POSITION (use ONLY these pieces — do not invent any others):
{board_desc}

The correct move is: {solution}
The tactical theme is: {motif}

Your task:
- Explain in 2–3 short sentences why {solution} is the correct move.
- Use the piece names and square coordinates from the board description above.
- Explain what the {motif} achieves (e.g. which pieces are attacked, what material is won).
- Do NOT mention any piece that is not listed above.

Explanation:"""
    return query_ollama(prompt)