"""Pygame-based chess UI for CNChess.

Features:
- Draws an 8x8 chess board
- Loads piece images from `python/chess_assets` (PNG/JPG/BMP/GIF)
- Falls back to Unicode chess glyphs when images not found
- Click-to-select and click-to-move pieces (no move legality enforcement)
- Reset and quit controls

Run: `python3 python/UI.py`
"""

import os
import pygame

ROOT = os.path.dirname(__file__)
ASSETS_DIR = os.path.join(ROOT, "chess_assets")

WIDTH = 640
HEIGHT = 640
ROWS = 8
COLUMNS = 8
FPS = 30

LIGHT = (240, 217, 181)
DARK = (181, 136, 99)
HIGHLIGHT = (100, 200, 150, 120)

PIECE_UNICODE = {
	'K': '\u2654', 'Q': '\u2655', 'R': '\u2656', 'B': '\u2657', 'N': '\u2658', 'P': '\u2659',
	'k': '\u265A', 'q': '\u265B', 'r': '\u265C', 'b': '\u265D', 'n': '\u265E', 'p': '\u265F',
}


def scan_assets(path):
	"""Recursively load raster images (PNG/JPG/BMP/GIF) into a dict.

	Returns dict mapping filename stem (lowercase) -> pygame.Surface
	"""
	images = {}
	if not os.path.isdir(path):
		return images
	exts = {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}
	for root, _, files in os.walk(path):
		for f in files:
			name, ext = os.path.splitext(f)
			if ext.lower() not in exts:
				continue
			full = os.path.join(root, f)
			key = name.lower()
			try:
				surf = pygame.image.load(full).convert_alpha()
				images[key] = surf
			except Exception:
				# ignore files pygame can't load
				continue
	return images


def default_board():
	# Uppercase = White, lowercase = Black
	return [
		list('rnbqkbnr'),
		list('pppppppp'),
		list('________'),
		list('________'),
		list('________'),
		list('________'),
		list('PPPPPPPP'),
		list('RNBQKBNR'),
	]


class ChessUI:
	def __init__(self, width=WIDTH, height=HEIGHT):
		pygame.init()
		self.screen = pygame.display.set_mode((width, height))
		pygame.display.set_caption('CNChess')
		self.clock = pygame.time.Clock()
		self.w = width
		self.h = height
		self.square = width // 8

		self.images = scan_assets(ASSETS_DIR)
		# prefer an image named 'board' if present
		self.board_img = self.images['rect-8x8']
		
		self.board = default_board()
		self.selected = None
		self.running = True
		self.font = pygame.font.SysFont(None, int(self.square * 0.8))

	def draw_board(self):
		"""Draw the board from image"""
		#Scaling image before showing it 
		scaled = pygame.transform.smoothscale(self.board_img, (self.w, self.h))
		self.screen.blit(scaled, (0, 0))
		return
			
	def draw_pieces(self):
		for r in range(8):
			for c in range(8):
				p = self.board[r][c]
				if p == '_' or p == '':
					continue
				piece_key = self.piece_key_from_char(p)
				img = None
				if piece_key:
					img = self.get_image_from_piece(piece_key)
				x = c * self.square
				y = r * self.square
				if img is not None:
					scaled = pygame.transform.smoothscale(img, (self.square, self.square))
					self.screen.blit(scaled, (x, y))
			

	def piece_key_from_char(self, ch):
		names = {'k': 'king', 'q': 'queen', 'r': 'rook', 'b': 'bishop', 'n': 'knight', 'p': 'pawn'}

		ch_lower = ch.lower()
		if ch_lower in names:
			color = 'white' if ch.isupper() else 'black'
			return f"{color}-{names[ch_lower]}"
		return None

	def get_image_from_piece(self, piece_key):
		"""Get image path from key in images dictionnary"""

		#Get image previously loaded
		if piece_key in self.images:
			return self.images[piece_key]
		return None

	def coord_from_mouse(self, pos):
		x, y = pos
		c = x // self.square
		r = y // self.square
		if 0 <= r < 8 and 0 <= c < 8:
			return r, c
		return None

	def handle_click(self, pos):
		cell = self.coord_from_mouse(pos)
		if not cell:
			return
		r, c = cell
		if self.selected is None:
			if self.board[r][c] != '_' and self.board[r][c] != '':
				self.selected = (r, c)
		else:
			sr, sc = self.selected
			# move piece (no legality checks)
			self.board[r][c] = self.board[sr][sc]
			self.board[sr][sc] = '_'
			self.selected = None

	def draw_selection(self):
		if self.selected is None:
			return
		r, c = self.selected
		s = pygame.Surface((self.square, self.square), pygame.SRCALPHA)
		s.fill(HIGHLIGHT)
		self.screen.blit(s, (c * self.square, r * self.square))

	def reset(self):
		self.board = default_board()

	def run(self):
		while self.running:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.running = False
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_r:
						self.reset()
					elif event.key == pygame.K_ESCAPE:
						self.running = False
				elif event.type == pygame.MOUSEBUTTONDOWN:
					if event.button == 1:
						self.handle_click(event.pos)

			self.screen.fill((0, 0, 0))
			self.draw_board()
			self.draw_pieces()
			self.draw_selection()
			pygame.display.flip()
			self.clock.tick(FPS)


def main():
	ui = ChessUI()
	ui.run()
	pygame.quit()


if __name__ == '__main__':
	main()
