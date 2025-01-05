import random
import numpy as np
from matplotlib.colors import Colormap
import matplotlib.pyplot as plt

from .utils import grid_bfs

import logging
logger = logging.getLogger('uvicorn')

WIDTH = 500
HEIGHT = 400
GRID_SIZE = 10
ROWS = HEIGHT // GRID_SIZE
COLS = WIDTH // GRID_SIZE
AGENT_RADIUS = 5

RANDOM_SEED = 42


class Agent:
    _instance_count = 0

    def __init__(self, grid_position: tuple[int, int], position: tuple[int, int]):
        self.id = f"agent_{Agent._instance_count}"
        self.grid_position = grid_position  # position on grid
        self.position = position    # absolute pos on canvas
        Agent._instance_count += 1


class Obstacle:
    _instance_count = 0
    def __init__(self, size: tuple[int, int], position: tuple[int, int]):
        self.id = f"obstacle_{Obstacle._instance_count}"
        self.size = size
        self.position = position

        Obstacle._instance_count += 1


class Simulation:
    def __init__(self, num_agents: int, num_obstacles: int, state: bool):
        self.num_agents = num_agents
        self.num_obstacles = num_obstacles
        self.state = state

        self.agents = []
        self.obstacles = []
        self.grid = np.zeros((ROWS, COLS), dtype=np.int8)
        self.grid[14:25, -1] = 1    # exit
        self.path_dir_grid = None

        self.initialize()

    def initialize(self):
        # obstacles
        self.obstacles = self.__get_obstacles()
        # agents
        self.agents = self.__get_agents()
        # delta_v on grid
        self.path_dir_grid = grid_bfs(self.grid)


    def get_path_image(self) -> list[int]:
        assert self.path_dir_grid is not None
        
        # # Calculate and normalize angles
        grid_img = np.arccos(self.path_dir_grid[0] / 
                           np.sqrt(self.path_dir_grid[0]**2 + self.path_dir_grid[1]**2))
        grid_img = grid_img / np.pi
        img_flat = grid_img.flatten()
        # convert to array of colors [hex]
        cmap = plt.cm.viridis
        colors = ['#{:02x}{:02x}{:02x}'.format(
            int(255*r), int(255*g), int(255*b)
        ) for r, g, b, a in [cmap(pixel) for pixel in img_flat]]
        return colors

    def __get_agents(self) -> list[Agent]:
        assert self.obstacles is not None
        agents = []
        grid_cp = self.grid.copy()
        for _ in range(self.num_agents):
            row = random.randint(0, ROWS - 1)
            col = random.randint(0, COLS - 1)
            while grid_cp[row, col] != 0:
                row = random.randint(0, ROWS - 1)
                col = random.randint(0, COLS - 1)
            grid_cp[row, col] = 1
            agents.append(Agent((row, col), 
                                ((row + 0.5) * GRID_SIZE, (col + 0.5) * GRID_SIZE)))
        return agents

    def __get_obstacles(self) -> list[Obstacle]:
        """Generate a list of obstacles.

        Returns:
            list[Obstacle]: A list of obstacles.
        """
        def overlaps(a: Obstacle, b: Obstacle) -> bool:   
            return not (a.position[0] + a.size[0] < b.position[0] or
                        a.position[0] > b.position[0] + b.size[0] or
                        a.position[1] + a.size[1] < b.position[1] or
                        a.position[1] > b.position[1] + b.size[1])
        obstacles = []
        while len(obstacles) < self.num_obstacles:
            size=(random.randint(2, 10) * 10, random.randint(5, 10) * 10)
            obstacle = Obstacle(
                size=size,
                    position=(
                        random.randint(0, (WIDTH - size[0] - 10)//10)*10,
                        random.randint(0, (HEIGHT - size[1])//10)*10,
                    ),
                )
            if not any(overlaps(obstacle, o) for o in obstacles):
                obstacles.append(obstacle)
                grid_pos_y1 = obstacle.position[1]//10
                grid_pos_y2 = grid_pos_y1 + obstacle.size[1]//10

                grid_pos_x1 = obstacle.position[0]//10
                grid_pos_x2 = grid_pos_x1 + obstacle.size[0]//10

                self.grid[grid_pos_y1:grid_pos_y2, grid_pos_x1:grid_pos_x2] = -1


        return obstacles
