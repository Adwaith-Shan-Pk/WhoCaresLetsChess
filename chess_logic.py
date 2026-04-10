# chess_logic.py
import chess
import random

# ---------------------------------------------------------------------------#
# Piece values (centipawns)
# ---------------------------------------------------------------------------#
PIECE_VALUES = {
    chess.PAWN:   100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK:   500,
    chess.QUEEN:  900,
    chess.KING:   20000,
}

# ---------------------------------------------------------------------------#
# Piece-Square Tables (PST) — from White's perspective, a1=index 0, h8=index 63
# Source: Chess Programming Wiki (public domain)
# ---------------------------------------------------------------------------#
PAWN_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0,
]

KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]

BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]

ROOK_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0,
]

QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
]

KING_TABLE = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20,
]

_PST = {
    chess.PAWN:   PAWN_TABLE,
    chess.KNIGHT: KNIGHT_TABLE,
    chess.BISHOP: BISHOP_TABLE,
    chess.ROOK:   ROOK_TABLE,
    chess.QUEEN:  QUEEN_TABLE,
    chess.KING:   KING_TABLE,
}

# ---------------------------------------------------------------------------#
# Evaluation
# ---------------------------------------------------------------------------#
def evaluate(board: chess.Board) -> int:
    """Static evaluation in centipawns (positive = good for White)."""
    if board.is_checkmate():
        # The side to move is checkmated — that's bad for them
        return -99999 if board.turn == chess.BLACK else 99999
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is None:
            continue
        value = PIECE_VALUES.get(piece.piece_type, 0)
        pst   = _PST.get(piece.piece_type, [0] * 64)
        # White: read PST from a1 upward (square index matches a1=0)
        # Black: mirror vertically (63 - square)
        if piece.color == chess.WHITE:
            positional = pst[square]
            score += value + positional
        else:
            positional = pst[63 - square]
            score -= value + positional
    return score

# ---------------------------------------------------------------------------#
# Minimax with Alpha-Beta pruning
# ---------------------------------------------------------------------------#
def minimax(board: chess.Board, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
    """
    Minimax with alpha-beta pruning.
    White = maximizing player, Black = minimizing player.
    """
    if depth == 0 or board.is_game_over():
        return evaluate(board)

    if maximizing:
        best = float('-inf')
        for move in board.legal_moves:
            board.push(move)
            score = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            best = max(best, score)
            alpha = max(alpha, best)
            if beta <= alpha:
                break   # β cut-off
        return best
    else:
        best = float('inf')
        for move in board.legal_moves:
            board.push(move)
            score = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            best = min(best, score)
            beta = min(beta, best)
            if beta <= alpha:
                break   # α cut-off
        return best

# ---------------------------------------------------------------------------#
# Public API: get the best move for the current position
# ---------------------------------------------------------------------------#
def get_best_move(board: chess.Board, depth: int = 4) -> chess.Move:
    """
    Return the best legal move according to Minimax at the given depth.
    White maximises, Black minimises — always from White's perspective.
    """
    best_move  = None
    best_score = float('-inf') if board.turn == chess.WHITE else float('inf')

    for move in board.legal_moves:
        board.push(move)
        score = minimax(board, depth - 1, float('-inf'), float('inf'),
                        board.turn == chess.WHITE)
        board.pop()

        if board.turn == chess.WHITE:
            if score > best_score:
                best_score = score
                best_move  = move
        else:
            if score < best_score:
                best_score = score
                best_move  = move

    # Fallback: return any legal move (should never be needed)
    if best_move is None and any(True for _ in board.legal_moves):
        best_move = next(iter(board.legal_moves))

    return best_move

# Classic book-style tactical positions (real puzzles from chess literature)
EXAMPLE_FENS = [
    # 1. Famous Ruy Lopez pin (Bb5)
    "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1",
    # 2. Knight fork opportunity
    "r1bqkb1r/pppp1ppp/2n2n2/4p3/4P3/2N2N2/PPPP1PPP/R1BQKB1R w KQkq - 0 1",
    # 3. Classic queen skewer / pin
    "rnbqkbnr/ppp2ppp/8/3p4/3P4/8/PPP2PPP/RNBQKBNR w KQkq - 0 1",
    # 4. Back-rank mate threat
    "r3k2r/ppp2ppp/8/8/8/8/PPP2PPP/R3K2R w KQkq - 0 1",
    # 5. Beautiful knight fork
    "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/2N2N2/PPPP1PPP/R1BQKB1R w KQkq - 0 1",
    # 6. Absolute pin on knight
    "r1bqkbnr/ppp2ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1",
    # 7. Skewer on the 7th rank
    "r4rk1/ppp2ppp/8/8/8/8/PPP2PPP/R3K2R w KQkq - 0 1",
    # 8. Classic back-rank combination
    "4r1k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1"
]

def detect_fork(board: chess.Board) -> bool:
    color = not board.turn
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.color == color and piece.piece_type == chess.KNIGHT:
            attacks = board.attacks(square)
            valuable = sum(1 for t in attacks if (p := board.piece_at(t)) and p.color != color and p.piece_type in (chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT))
            if valuable >= 2:
                return True
    return False

def detect_pin(board: chess.Board) -> bool:
    return any(board.is_pinned(board.turn, sq) for sq in chess.SQUARES)

def detect_skewer(board: chess.Board) -> bool:
    color = not board.turn
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        # Only long-range pieces (Queen, Rook, Bishop) can perform a skewer
        if piece and piece.color == color and piece.piece_type in (chess.ROOK, chess.BISHOP, chess.QUEEN):
            attacks = list(board.attacks(square))
            
            # A skewer requires at least two pieces on the same line of attack
            # We filter for enemy pieces specifically
            targets = [board.piece_at(t) for t in attacks if board.piece_at(t) and board.piece_at(t).color != color]
            
            # If we are attacking 2+ pieces on one line, it's likely a tactical motif
            if len(targets) >= 2:
                # Optional: Ensure the first target is more valuable than the second
                # (This is the definition of a skewer vs a pin)
                return True
    return False

def detect_back_rank_mate(board: chess.Board) -> bool:
    if not board.is_check():
        return False
    king = board.king(board.turn)
    if king is None:
        return False
    rank = chess.square_rank(king)
    return (board.turn == chess.WHITE and rank == 0) or (board.turn == chess.BLACK and rank == 7)

def generate_puzzle(board: chess.Board) -> dict | None:
    original_fen = board.fen()
    tactical_moves = []
    for move in list(board.legal_moves):
        board.push(move)
        motif = None
        if detect_fork(board):
            motif = "fork"
        elif detect_pin(board):
            motif = "pin"
        elif detect_skewer(board):
            motif = "skewer"
        elif detect_back_rank_mate(board):
            motif = "back_rank_mate"
        board.pop()
        if motif:
            tactical_moves.append({"move": move, "san": board.san(move), "motif": motif})
    if not tactical_moves:
        return None
    chosen = random.choice(tactical_moves)
    return {"fen": original_fen, "solution": chosen["san"], "motif": chosen["motif"]}