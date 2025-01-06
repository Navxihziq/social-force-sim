import random
import numpy as np
import matplotlib.pyplot as plt

from .utils import grid_bfs, wall_distance_grid, obstacle_distance_grid, outofbounds

import logging
logger = logging.getLogger('uvicorn')

WIDTH = 500
HEIGHT = 400
GRID_SIZE = 10
ROWS = HEIGHT // GRID_SIZE
COLS = WIDTH // GRID_SIZE
AGENT_RADIUS = 5

RANDOM_SEED = 42


L_SCALE = 8e-2  # grid unit to metric unit [meter]
DELTA_T = 0.005  # time step [second]

A = 2 / L_SCALE
B = -0.3 / L_SCALE


class Agent:
    _instance_count = 0

    def __init__(self, grid_position: np.ndarray, position: np.ndarray):
        """Initialize an agent.

        Args:
            grid_position (np.array[int, int]): position on grid; (row, col)
            position (np.array[int, int]): absolute pos on canvas; (x, y)
        """
        self.id = f"agent_{Agent._instance_count}"
        self.grid_position = np.array(grid_position, dtype=np.int32)  # position on grid
        self.position = np.array(position, dtype=np.float32)    # absolute pos on canvas
        Agent._instance_count += 1

        self.exited = False

        # length measures are all in grid units
        self.r = 0.4 / L_SCALE
        self.m = 60 # [kg]

        self.v_des = np.array([1.4/L_SCALE, 1.4/L_SCALE], dtype=np.float32)
        self.v_t = np.array([0.0, 0.0], dtype=np.float32)

    def fij(self, agent_j):
        d_ij = np.linalg.norm(self.position - agent_j.position)
        if d_ij < 1:
            d_ij = 1
        return A * np.exp((d_ij - (self.r + agent_j.r)) / B) * (self.position - agent_j.position) / d_ij

    def fiw(self, wall_distance_grid: np.ndarray, 
            wall_direction_grid: np.ndarray,
            obstacle_distance_grid: np.ndarray,
            obstacle_direction_grid: np.ndarray) -> np.ndarray:
        """Calculate the force exerted by walls and obstacles on an agent.

        Args:
            wall_distance_grid (np.ndarray): distance to walls. shape: (4, grid.shape[0], grid.shape[1])
            wall_direction_grid (np.ndarray): direction to walls. shape: (4, 2, grid.shape[0], grid.shape[1])
            obstacle_distance_grid (np.ndarray): distance to obstacles. shape: (4, grid.shape[0], grid.shape[1])
            obstacle_direction_grid (np.ndarray): direction to obstacles. shape: (4, 2, grid.shape[0], grid.shape[1])

        Returns:
            np.ndarray: force exerted by walls and obstacles on an agent. shape: (2,)
        """
        i, j = self.grid_position
        f_iwalls = (A * np.exp((wall_distance_grid[:, i, j] - self.r) / B))
        f_iwalls = f_iwalls[:, np.newaxis] * wall_direction_grid[:, :, i, j] # shape: (4, 2)
        f_iwalls = f_iwalls.sum(axis=0) # shape: (2,)

        f_iobstacles = (A * np.exp((obstacle_distance_grid[:, i, j] - self.r) / B))
        # shape: (obstacles, 2)
        f_iobstacles = f_iobstacles[:, np.newaxis] * obstacle_direction_grid[:, :, i, j] 
        f_iobstacles = f_iobstacles.sum(axis=0) # shape: (2,)

        return f_iwalls + f_iobstacles


    def step(self, nearest_neighbors: list, 
             path_dir_grid: np.ndarray,
             wall_distance_grid: np.ndarray, 
             wall_direction_grid: np.ndarray,
             obstacle_distance_grid: np.ndarray,
             obstacle_direction_grid: np.ndarray):
        i, j = self.grid_position
        f_des = self.v_des * path_dir_grid[:, i, j]
        fij_sum = np.array([0.0, 0.0])
        for agent_j in nearest_neighbors:
            fij_sum += self.fij(agent_j)

        fiw_sum = self.fiw(wall_distance_grid, 
                           wall_direction_grid, 
                           obstacle_distance_grid, 
                           obstacle_direction_grid)
        
        f_sum = f_des + fij_sum + fiw_sum

        new_pos = self.position + self.v_t * DELTA_T
        new_grid_pos = new_pos // GRID_SIZE

        if outofbounds(new_grid_pos, path_dir_grid.shape[1:]):
            # snap to the nearest boundary
            new_grid_pos[0] = np.clip(new_grid_pos[0], 0, path_dir_grid.shape[1] - 1)
            new_grid_pos[1] = np.clip(new_grid_pos[1], 0, path_dir_grid.shape[2] - 1)
            new_pos = (new_grid_pos + 0.5) * GRID_SIZE

        new_v_t = self.v_t + (f_sum/self.m) * DELTA_T

        self.position = new_pos
        self.grid_position = np.array(new_grid_pos, dtype=np.int32)
        self.v_t = new_v_t


class Obstacle:
    _instance_count = 0
    def __init__(self, size: tuple[int, int], position: tuple[int, int]):
        self.id = f"obstacle_{Obstacle._instance_count}"
        self.size = size
        self.position = position
        self.centroid = (position[0] + size[0]//2, position[1] + size[1]//2)
        self.x0 = position[0]
        self.y0 = position[1]
        self.x1 = position[0] + size[0]
        self.y1 = position[1] + size[1]

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

        self.wall_distance_grid = None
        self.wall_direction_grid = None
        self.obstacle_distance_grid = None
        self.obstacle_direction_grid = None
        self.initialize()

    def initialize(self):
        # obstacles
        self.obstacles = self.__get_obstacles()
        # agents
        self.agents = self.__get_agents()
        # delta_v on grid
        self.path_dir_grid = grid_bfs(self.grid)
        # another grid for distance to walls and obstacles
        self.wall_distance_grid, self.wall_direction_grid = wall_distance_grid(self.grid)
        self.obstacle_distance_grid, self.obstacle_direction_grid = obstacle_distance_grid(self.grid, self.obstacles)
        logger.info(f"direction_grid: {self.obstacle_direction_grid[0,:, 0, 0]}")
    
    def step(self):
        for i in range(len(self.agents)):
            # note: please first convert all grid units to metric units
            agent = self.agents[i]
            if agent.exited:
                continue

            agent.step(self.agents, 
                       self.path_dir_grid,
                       self.wall_distance_grid, 
                       self.wall_direction_grid, 
                       self.obstacle_distance_grid, 
                       self.obstacle_direction_grid)
            
            if self.grid[int(self.agents[i].grid_position[0]), 
                         int(self.agents[i].grid_position[1])] == 1:
                self.agents[i].exited = True


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
            agents.append(Agent(np.array([row, col]), 
                                np.array([(row + 0.5) * GRID_SIZE, (col + 0.5) * GRID_SIZE])))
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
            size=(random.randint(7, 17) * 10, random.randint(7, 17) * 10)
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
