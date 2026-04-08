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
    Give a hint by pre-parsing the solution move so the AI knows EXACTLY
    which piece is involved — eliminating wrong-piece hallucinations.
    """
    board = chess.Board(fen)
    board_desc = describe_board(fen)

    # Parse the solution to find the moving piece and its current square
    try:
        move = board.parse_san(solution)
        piece = board.piece_at(move.from_square)
        piece_name = PIECE_NAMES.get(piece.piece_type, "piece") if piece else "piece"
        from_sq   = chess.square_name(move.from_square)
        color_name = "White" if (piece and piece.color == chess.WHITE) else "Black"
        piece_info = f"The {color_name} {piece_name} currently on {from_sq}"
    except Exception:
        piece_info = "A key piece on the board"

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
    return query_ollama(prompt)


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