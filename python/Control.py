# This files handle physical control of the game.

# It will take a chess move and transform it into physical actions and send it via serial bus

import numpy as np
import chess

# Here is all the object for a* pathfinding algorithm
class Position:
    """Represents a 2D position point with x and y coordinates."""
    x: float
    y: float

    def __init__(self, x: float, y: float):
        """Initialize position with x and y coordinates.
        
        Args:
            x (float): X coordinate value.
            y (float): Y coordinate value.
        
        Return:
            None
        """
        self.x = x
        self.y = y

    def __eq__(self, value):
        """Compare two positions for equality.
        
        Args:
            value (Position): Position to compare with.
        
        Return:
            bool: True if positions are equal, False otherwise.
        """
        return self.x == value.x and self.y == value.y

    def __hash__(self):
        """Return hash of position for use in sets/dicts during pathfinding.
        
        Args:
            None
        
        Return:
            int: Hash value of the position.
        """
        return hash((self.x, self.y))
    
class Command:
    """Represents a movement command with position and magnet state."""
    position: Position
    magnet_state: bool
    
    def __init__(self, position: Position = Position(0.0, 0.0), magnet_state: bool = False):
        """Initialize command with position and magnet state.
        
        Args:
            position (Position): Target position for movement.
            magnet_state (bool): Magnet state (True for on, False for off).
        
        Return:
            None
        """
        self.position = position
        self.magnet_state = magnet_state

class Node:
    """Represents a node in A* pathfinding grid with costs and neighbors."""
    position: Position
    gCost: float
    hCost: float
    fCost: float
    parent: 'Node'
    neighbors: list['Node']

    def __init__(self, position: Position = Position(0.0, 0.0)):
        """Initialize pathfinding node with position and costs.
        
        Args:
            position (Position): Node position on grid.
        
        Return:
            None
        """
        self.position = position
        self.gCost = 0.0
        self.hCost = 0.0
        self.fCost = 0.0
        self.parent = None
        self.neighbors = []

    def __eq__(self, value):
        """Compare nodes by position.
        
        Args:
            value (Node): Node to compare with.
        
        Return:
            bool: True if positions are equal, False otherwise.
        """
        return self.position == value.position

    def __hash__(self):
        """Return hash of node by position for set/dict storage.
        
        Args:
            None
        
        Return:
            int: Hash value of the node's position.
        """
        return hash(self.position)

class Grid:
    """A* pathfinding grid for motion planning on chess board."""
    nodes: list[list[Node]]
    width: int
    height: int
    obstacle_remove_position: Position

    def __init__(self, width: int, height: int):
        """Initialize A* pathfinding grid with nodes.
        
        Args:
            width (int): Grid width in squares.
            height (int): Grid height in squares.
        
        Return:
            None
        """
        self.obstacle_remove_position = Position(0.5, 5.5)  # Position to remove obstacle for captured pieces
        self.width = width * 2 + 1
        self.height = height * 2 + 1
        # Use half-step coordinates so intermediate nodes land between board squares
        self.nodes = [[Node(Position((x + 1) / 2, (y + 1) / 2)) for x in range(self.width)] for y in range(self.height)]
    
    def get_node(self, position: Position) -> Node:
        """Return node at given position, or None if out of bounds.
        
        Args:
            position (Position): Position to retrieve node from.
        
        Return:
            Node: Node at position, or None if invalid.
        """
        if position.x < 0.5 or position.x > self.width/2 or position.y < 0.5 or position.y > self.height/2:
            return None
        return self.nodes[int(position.y*2)-1][int(position.x*2)-1]
    
    def get_neighbors(self, node: Node) -> list[Node]:
        """Get neighboring nodes for pathfinding (4-directional or 8-directional).
        
        Args:
            node (Node): Node to get neighbors for.
        
        Return:
            list[Node]: List of valid neighboring nodes.
        """
        neighbors = []
        if (node.position.x % 1 == 0 and node.position.y % 1 != 0) or (node.position.x % 1 != 0 and node.position.y % 1 == 0):
            # direction without diagonals
            directions = [(-0.5, 0), (0.5, 0), (0, -0.5), (0, 0.5)]
        else:
            # direction with diagonals
            directions = [(-0.5, 0), (0.5, 0), (0, -0.5), (0, 0.5),
                        (-0.5, -0.5), (-0.5, 0.5), (0.5, -0.5), (0.5, 0.5)]

        for direction in directions:
            neighbor_x = node.position.x + direction[0]
            neighbor_y = node.position.y + direction[1]
            neighbor_node = self.get_node(Position(neighbor_x, neighbor_y))
            if neighbor_node is not None:
                neighbors.append(neighbor_node)

        return neighbors

    def initialize_links(self):
        """Set up neighbor relationships for all nodes in grid.
        
        Args:
            None
        
        Return:
            None
        """
        for i in range(self.height):
            for j in range(self.width):
                node = self.nodes[i][j]
                node.neighbors = self.get_neighbors(node)

    def add_obstacle(self, position: Position):
        """Add obstacle by removing all neighbors from node.
        
        Args:
            position (Position): Position to add obstacle at.
        
        Return:
            None
        """
        node = self.get_node(position)
        if node:
            node.neighbors = []  # Remove all neighbors to create an obstacle
    
    def remove_obstacle(self, position: Position):
        """Remove obstacle by restoring neighbors to node.
        
        Args:
            position (Position): Position to remove obstacle from.
        
        Return:
            None
        """
        node = self.get_node(position)
        if node:
            node.neighbors = self.get_neighbors(node)  # Restore neighbors to remove obstacle

    def heuristic(a: Node, b: Node) -> float:
        """Calculate Euclidean heuristic distance between two nodes.
        
        Args:
            a (Node): First node.
            b (Node): Second node.
        
        Return:
            float: Heuristic distance between nodes.
        """
        return np.sqrt((a.position.x - b.position.x) ** 2 + (a.position.y - b.position.y) ** 2)
    
    def a_star(self, start_pos: Position, end_pos: Position) -> list[Position]:
        """Perform A* pathfinding algorithm between start and end positions.
        
        Args:
            start_pos (Position): Starting position.
            end_pos (Position): Ending position.
        
        Return:
            list[Position]: List of positions forming the path, or empty list if no path exists.
        """
        start_node = self.get_node(start_pos)
        end_node = self.get_node(end_pos)

        if start_node is None or end_node is None:
            return []

        # Reset all node states to avoid stale data from previous searches
        for row in self.nodes:
            for node in row:
                node.gCost = float('inf')
                node.hCost = 0.0
                node.fCost = float('inf')
                node.parent = None

        open_set = []
        closed_set = set()

        start_node.gCost = 0.0
        start_node.fCost = Grid.heuristic(start_node, end_node)
        open_set.append(start_node)

        while open_set:
            current_node = min(open_set, key=lambda node: node.fCost)

            if current_node == end_node:
                path = []
                node = current_node
                while node is not None:
                    path.append(node.position)
                    node = node.parent
                return path[::-1]  # Return reversed path

            open_set.remove(current_node)
            closed_set.add(current_node)

            for neighbor in current_node.neighbors:
                if neighbor in closed_set:
                    continue

                tentative_gCost = current_node.gCost + Grid.heuristic(current_node, neighbor)

                if neighbor not in open_set:
                    open_set.append(neighbor)
                elif tentative_gCost >= neighbor.gCost:
                    continue

                neighbor.parent = current_node
                neighbor.gCost = tentative_gCost
                neighbor.hCost = Grid.heuristic(neighbor, end_node)
                neighbor.fCost = neighbor.gCost + neighbor.hCost

        return []  # No path found
    
    def update_obstacles(self, boardState: str):
        """Update obstacles in grid based on current board state.
        
        Args:
            boardState (str): FEN notation of board state.
        
        Return:
            None
        """
        board = chess.Board(boardState)
        for i in range(8):
            for j in range(8):
                piece = board.piece_at(chess.square(i, j))
                position = Position(i + 1, j + 1)
                if piece is not None:
                    self.add_obstacle(position)
                else:
                    self.remove_obstacle(position)

    def is_obstacle(self, position: Position) -> bool:
        """Check if position contains an obstacle.
        
        Args:
            position (Position): Position to check.
        
        Return:
            bool: True if position is an obstacle, False otherwise.
        """
        node = self.get_node(position)
        if node:
            return len(node.neighbors) == 0
        return False

class Control:
    """Physical control system for chess board movement and pathfinding."""
    grid: Grid

    def __init__(self):
        """Initialize control system with 8x8 grid for pathfinding.
        
        Args:
            None
        
        Return:
            None
        """
        self.grid = Grid(8, 8)
        self.grid.initialize_links()

    def update_board_state(self, boardState: str):
        """Update grid obstacles from board state.
        
        Args:
            boardState (str): FEN notation of board state.
        
        Return:
            None
        """
        self.grid.update_obstacles(boardState)
    
    def get_path(self, move: chess.Move, board: chess.Board) -> list[Command]:
        """Generate movement commands for a chess move using pathfinding.
        
        Args:
            move (chess.Move): Chess move to generate path for.
            board (chess.Board): Current board state.
        
        Return:
            list[Command]: List of commands with positions and magnet states to execute move.
        """
        start_x = chess.square_file(move.from_square) + 1
        start_y = chess.square_rank(move.from_square) + 1
        end_x = chess.square_file(move.to_square) + 1
        end_y = chess.square_rank(move.to_square) + 1

        # Pathfinding expects 1-based board coordinates to align with 0.5 grid offsets
        start_pos = Position(start_x, start_y)
        end_pos = Position(end_x, end_y)

        path_to_obstacle_removal = []
        if board.is_capture(move):
            if board.is_en_passant(move): # Handle en passant by adding an additional command to remove the captured pawn
                # For en passant, also need to remove obstacle at captured pawn's position
                print("En passant capture detected, planning path to captured pawn removal point.")
                captured_pawn_square = chess.square(chess.square_file(move.to_square), chess.square_rank(move.from_square))
                captured_pawn_pos = Position(chess.square_file(captured_pawn_square) + 1, chess.square_rank(captured_pawn_square) + 1)
                
                self.grid.remove_obstacle(captured_pawn_pos)
                path_to_obstacle_removal = self.grid.a_star(captured_pawn_pos, self.grid.obstacle_remove_position)
            else:
                print("Obstacle detected at end position, planning path to obstacle removal point.")
                self.grid.remove_obstacle(end_pos)
                path_to_obstacle_removal = self.grid.a_star(end_pos, self.grid.obstacle_remove_position)
        self.grid.remove_obstacle(start_pos)  # Ensure start position is not an obstacle
        path = self.grid.a_star(start_pos, end_pos)
        full_path = path_to_obstacle_removal + path


        # Convert path to commands with magnet states
        commands = []
        for i, pos in enumerate(full_path):
            if i == 0:
                # Turn magnet on at start position
                commands.append(Command(pos, True))
            elif i == len(path_to_obstacle_removal) - 1 or i == len(full_path) - 1:
                # Turn magnet off at end position
                commands.append(Command(pos, False))
            else:
                # Keep magnet on during movement
                commands.append(Command(pos, True))
            
        
        # Handle castling by adding additional commands for rook movement
        if board.is_castling(move):
            # Update obstacle before calculating rook path to ensure it accounts for king's new position
            self.grid.add_obstacle(end_pos)  # Temporarily add obstacle back to calculate rook path correctly

            # Handle castling by moving the king first, then the rook
            if board.turn == chess.WHITE:
                if board.is_kingside_castling(move):
                    commands = commands + self.get_path(chess.Move.from_uci("h1f1"), board)
                else:
                    commands = commands + self.get_path(chess.Move.from_uci("a1d1"), board)
            else:
                if board.is_kingside_castling(move):
                    commands = commands + self.get_path(chess.Move.from_uci("h8f8"), board)
                else:
                    commands = commands + self.get_path(chess.Move.from_uci("a8d8"), board)

        output = self.optimize_path(commands)

        return output
    

    def optimize_path(self, path: list[Command]) -> list[Command]:
        """Remove unnecessary waypoints from path by eliminating collinear points.
        
        Args:
            path (list[Command]): Input path with all waypoints.
        
        Return:
            list[Command]: Optimized path with collinear points removed.
        """
        if not path:
            return []
        
        optimized_path = [path[0]]
        for i in range(1, len(path) - 1):
            prev_cmd = optimized_path[-1]
            curr_cmd = path[i]
            next_cmd = path[i + 1]

            vec1 = (curr_cmd.position.x - prev_cmd.position.x, curr_cmd.position.y - prev_cmd.position.y)
            vec2 = (next_cmd.position.x - curr_cmd.position.x, next_cmd.position.y - curr_cmd.position.y)

            # Check if the direction is the same (collinear)
            if vec1[0] * vec2[1] != vec1[1] * vec2[0] or curr_cmd.magnet_state != prev_cmd.magnet_state:
                optimized_path.append(curr_cmd)

        optimized_path.append(path[-1])  # Always include the last command
        return optimized_path

    def print_path(self, path: list[Command]):
        """Print path waypoints for debugging purposes.
        
        Args:
            path (list[Command]): Path to print.
        
        Return:
            None
        """
        for cmd in path:
            pos = cmd.position
            print(f"({pos.x}, {pos.y})", end=" -> ")
        print("END")    
    