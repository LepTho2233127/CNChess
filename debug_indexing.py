#!/usr/bin/env python3
"""
Debug script to compare camera square indexing with chess library indexing.
"""
import chess

def print_chess_indexing():
    """Print how python-chess indexes squares (0-63)"""
    print("=" * 60)
    print("CHESS LIBRARY INDEXING (python-chess)")
    print("=" * 60)
    board = chess.Board()
    print("Board FEN:", board.fen())
    print("\nSquare Index Mapping (0-indexed):")
    print("  Rank 8 (top):    56  57  58  59  60  61  62  63")
    print("  Rank 7:          48  49  50  51  52  53  54  55")
    print("  Rank 6:          40  41  42  43  44  45  46  47")
    print("  Rank 5:          32  33  34  35  36  37  38  39")
    print("  Rank 4:          24  25  26  27  28  29  30  31")
    print("  Rank 3:          16  17  18  19  20  21  22  23")
    print("  Rank 2:           8   9  10  11  12  13  14  15")
    print("  Rank 1 (bottom):  0   1   2   3   4   5   6   7")
    print("  Files:            a   b   c   d   e   f   g   h")
    print("\nNotation lookup:")
    print(f"  a1 (bottom-left) = square {chess.A1}")
    print(f"  h1 (bottom-right) = square {chess.H1}")
    print(f"  a8 (top-left) = square {chess.A8}")
    print(f"  h8 (top-right) = square {chess.H8}")
    print(f"  e2 (white pawn starting position) = square {chess.E2}")

def print_camera_indexing():
    """Print how camera detects squares based on ChessBoardSquares logic"""
    print("\n" + "=" * 60)
    print("CAMERA DETECTION INDEXING")
    print("=" * 60)
    print("Board iteration (from Cam.py ChessBoardSquares.get_all_squares_warped):")
    print("for i in range(ROWS - 1, -1, -1):  # iterates 7, 6, 5, ..., 0")
    print("  for j in range(COLS):  # iterates 0, 1, 2, ..., 7")
    print("\nResulting square indices in detection order:")
    square_idx = 0
    for i in range(7, -1, -1):
        print(f"  i={i}:", end="")
        for j in range(8):
            print(f"{square_idx:3d}", end=" ")
            square_idx += 1
        print()
    print("\nThis means:")
    print("  Squares 0-7:    first detected (top of warped image)")
    print("  Squares 56-63:  last detected (bottom of warped image)")

def test_indexing_match():
    """Test if a known move matches between systems"""
    print("\n" + "=" * 60)
    print("MOVE DETECTION TEST")
    print("=" * 60)
    board = chess.Board()
    print("Starting position:")
    print(board)
    
    # White pawn e2 -> e4 is a common opening move
    # e2 = square 12 (chess indexing)
    # e4 = square 28 (chess indexing)
    print(f"\nCommon move: e2-e4 (pawn push)")
    print(f"  Chess indexing: {chess.E2} -> {chess.E4}")
    
    # If camera indexes top-to-bottom, e4 would be:
    # e4 is at rank 4, file e (column 4)
    # In camera indexing (top-to-bottom): rank 8 = rows 0, rank 1 = rows 56
    # So rank 4 = rows 24, file e (col 4) = 24
    camera_e2_guess = 52  # (8-2)*8 + 4 = 52 (if using rank inversion)
    camera_e4_guess = 36  # (8-4)*8 + 4 = 36 (if using rank inversion)
    
    print(f"  Camera indexing (if top-to-bottom): ~{camera_e2_guess} -> ~{camera_e4_guess}")
    print(f"\n  >> If your move detection shows wrong end squares,")
    print(f"     check if there's a rank/file inversion needed!")

if __name__ == "__main__":
    print_chess_indexing()
    print_camera_indexing()
    test_indexing_match()
    
    print("\n" + "=" * 60)
    print("ACTION ITEMS:")
    print("=" * 60)
    print("1. Make a known move (e.g., e2->e4) and note what camera reports")
    print("2. Compare against chess library indices above")
    print("3. If off by a pattern (e.g., always inverted rank), add a")
    print("   conversion function to Cam.py's detect_move()")
