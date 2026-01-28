# This files handle physical control of the game.

# It will take a chess move and transform it into physical actions and send it via serial bus

from time import time
import numpy as np
import chess
import serial

# Here is all the object for a* pathfinding algorithm
class Position:
    x: float
    y: float

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __eq__(self, value):
        return self.x == value.x and self.y == value.y

    def __hash__(self):
        return hash((self.x, self.y))
    
class Command:
    position: Position
    magnet_state: bool
    def __init__(self, position: Position = Position(0.0, 0.0), magnet_state: bool = False):
        self.position = position
        self.magnet_state = magnet_state


class Node:

    position: Position
    gCost: float
    hCost: float
    fCost: float
    parent: 'Node'
    neighbors: list['Node']

    def __init__(self, position: Position = Position(0.0, 0.0)):
        self.position = position
        self.gCost = 0.0
        self.hCost = 0.0
        self.fCost = 0.0
        self.parent = None
        self.neighbors = []

    def __eq__(self, value):
        return self.position == value.position

    def __hash__(self):
        # Hash by position so Nodes can live in sets/dicts during pathfinding
        return hash(self.position)


class Grid:   
    nodes: list[list[Node]]
    width: int
    height: int
    obstacle_remove_position: Position

    def __init__(self, width: int, height: int):
        self.obstacle_remove_position = Position(8.5, 4.5)  # Position to remove obstacle for captured pieces
        self.width = width * 2 + 1
        self.height = height * 2 + 1
        # Use half-step coordinates so intermediate nodes land between board squares
        self.nodes = [[Node(Position((x + 1) / 2, (y + 1) / 2)) for x in range(self.width)] for y in range(self.height)]
    
    def get_node(self, position: Position) -> Node:
        if position.x < 0.5 or position.x > self.width/2 or position.y < 0.5 or position.y > self.height/2:
            return None
        return self.nodes[int(position.y*2)-1][int(position.x*2)-1]
    
    def get_neighbors(self, node: Node) -> list[Node]:
        neighbors = []
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
    
    def add_link(self, from_node: Node, to_node: Node):
        from_node.neighbors.append(to_node)

    def initialize_links(self):
        for i in range(self.height):
            for j in range(self.width):
                node = self.nodes[i][j]
                node.neighbors = self.get_neighbors(node)

    def add_obstacle(self, position: Position):
        node = self.get_node(position)
        if node:
            node.neighbors = []  # Remove all neighbors to create an obstacle
    
    def remove_obstacle(self, position: Position):
        node = self.get_node(position)
        if node:
            node.neighbors = self.get_neighbors(node)  # Restore neighbors to remove obstacle

    def heuristic(a: Node, b: Node) -> float:
        return np.sqrt((a.position.x - b.position.x) ** 2 + (a.position.y - b.position.y) ** 2)
    
    def a_star(self, start_pos: Position, end_pos: Position) -> list[Position]:
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
        board = chess.Board(boardState)
        for i in range(8):
            for j in range(8):
                piece = board.piece_at(chess.square(i, j))
                position = Position(i + 1, j + 1)
                if piece is not None:
                    self.add_obstacle(position)
                else:
                    self.remove_obstacle(position)

    def print_grid(self):
        # inverted y-axis for printing
        for i in range(self.height-1, -1, -1):
            row = ""
            for j in range(self.width):
                node = self.nodes[i][j]
                if len(node.neighbors) == 0:
                    row += " X "
                else:
                    row += " . "
            print(row)

    def is_obstacle(self, position: Position) -> bool:
        node = self.get_node(position)
        if node:
            return len(node.neighbors) == 0
        return False


class Control:
    SQUARE_SIZE_MM = 50.8  # Size of a chess square in millimeters
    STEP_ANGLE_DEGREES = 1.8  # Stepper motor step angle in degrees
    PULLEY_DIAMETER = 12.0  # Pulley diameter in millimeters
    SEND_COMMAND_TIMEOUT = 30  # Timeout for sending commands in seconds
    grid: Grid
    mm_per_step: float
    circumference: float
    current_position: Position
    ser: serial.Serial

    def __init__(self):
        self.circumference = np.pi * self.PULLEY_DIAMETER
        self.grid = Grid(8, 8)
        self.grid.initialize_links()
        self.current_position = Position(0, 0)  # Start at home position
        # self.ser = serial.Serial('COM3', 115200, timeout=1)
        # time.sleep(2) # attendre reset Arduino
    
    def update_board_state(self, boardState: str):
        self.grid.update_obstacles(boardState)
    
    def get_path(self, move: chess.Move) -> list[Command]:
        start_x = chess.square_file(move.from_square) + 1
        start_y = chess.square_rank(move.from_square) + 1
        end_x = chess.square_file(move.to_square) + 1
        end_y = chess.square_rank(move.to_square) + 1

        # Pathfinding expects 1-based board coordinates to align with 0.5 grid offsets
        start_pos = Position(start_x, start_y)
        end_pos = Position(end_x, end_y)

        self.grid.remove_obstacle(start_pos)  # Ensure start position is not an obstacle

        path_to_obstacle_removal = []
        if self.grid.is_obstacle(end_pos):
            print("Obstacle detected at end position, planning path to obstacle removal point.")
            self.grid.remove_obstacle(end_pos)
            path_to_obstacle_removal = self.grid.a_star(end_pos, self.grid.obstacle_remove_position)

        path = self.grid.a_star(start_pos, end_pos)
        full_path = path_to_obstacle_removal + path

        # Convert path to commands with magnet states
        commands = []
        for i, pos in enumerate(full_path):
            if i == 0:
                # Turn magnet on at start position
                commands.append(Command(pos, True))
            elif i == len(path_to_obstacle_removal) - 1:
                # Turn magnet off at end position
                commands.append(Command(pos, False))
            else:
                # Keep magnet on during movement
                commands.append(Command(pos, True))
        return commands
    
    def print_path(self, path: list[Command]):
        for cmd in path:
            pos = cmd.position
            print(f"({pos.x}, {pos.y})", end=" -> ")
        print("END")

    def calculate_trajectory(self, path: list[Command]):
        trajectory = []
        path.insert(0, Command(self.current_position, False))  # Start from current position
        for i in range(1, len(path)):
            start = path[i - 1]
            end = path[i]
            delta_x = (end.position.x - start.position.x) * self.SQUARE_SIZE_MM
            delta_y = (end.position.y - start.position.y) * self.SQUARE_SIZE_MM

            pos = Position(delta_x, delta_y)

            trajectory.append(pos)
            self.current_position = end.position
        return trajectory 

    def goHome(self):
        self.ser.write("HOME\n".encode('utf-8'))

    def make_move(self, move:chess.Move): # Execute a chess move physically

        path = self.get_path(move)
        traj = self.calculate_trajectory(path)

        for pos in traj : 
            self.go_to_position(pos)
            
    def go_to_position(self, pos:Position): 

        step_motors = self.convert_to_step(pos)
        self.send_command(step_motors)
        

    def convert_to_step(self, pos:Position) -> tuple:

        rot_step1 = -360 * (pos.x + pos.y) / (self.circumference * np.sqrt(2))
        rot_step2 = -((2*pos.x * 360/(self.circumference*np.sqrt(2))) + rot_step1)
        step_mot1 = rot_step1 / self.STEP_ANGLE_DEGREES
        step_mot2 = rot_step2 / self.STEP_ANGLE_DEGREES

        return (step_mot1, step_mot2)

    def send_command(self, steps: tuple):
        self.ser.write(f"MOVE {int(steps[0])} {int(steps[1])}\n".encode('utf-8'))
        if not self.validate_send_command(steps):
            print("Error: Move command failed.")
            return False
        return True
    
    def validate_send_command(self, steps: tuple) -> bool:
        start_time = time.time()
        while self.ser.in_waiting == 0:
            if time.time() - start_time > self.SEND_COMMAND_TIMEOUT:
                print("Error: No response from motor controller.")
                return False
            pass

        response = self.ser.readline().decode('utf-8').strip()
        if response != "DONE" | response != "HOMED":
            print("Error: Unexpected response from motor controller:", response)
            return False

    def print_trajectory(self, trajectory: list[tuple[float, float]]):
        for step in trajectory:
            print(f"Motor1: {step[0]}, Motor2: {step[1]}")
    
    
    