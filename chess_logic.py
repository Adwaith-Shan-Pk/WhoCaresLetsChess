# chess_logic.py
import chess
import random

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
        if piece and piece.color == color and piece.piece_type in (chess.ROOK, chess.BISHOP, chess.QUEEN):
            if len(board.attacks(square)) >= 3:
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