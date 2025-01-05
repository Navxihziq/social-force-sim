import random
import numpy as np
from numba import prange
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


A = 20
B = -0.09

L_SCALE = 8e-2


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
        self.v = np.array([0.0, 0.0], dtype=np.float32)
        self.dv = np.array([1, 1], dtype=np.float32)/L_SCALE
        self.m = 60 # [kg]



class Obstacle:
    _instance_count = 0
    def __init__(self, size: tuple[int, int], position: tuple[int, int]):
        self.id = f"obstacle_{Obstacle._instance_count}"
        self.size = size
        self.position = position
        self.centroid = (position[0] + size[0]//2, position[1] + size[1]//2)

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
        self.path_dir_grid = grid_bfs(self.grid) * 1.4

    
    def step(self):
        for i in range(len(self.agents)):
            # note: please first convert all grid units to metric units
            agent = self.agents[i]
            # desired 
            d_v_desired = self.path_dir_grid[:, agent.grid_position[0], agent.grid_position[1]] * agent.dv

            # TODO: kd-tree: find top 8 nearest neighbors
            fij_sum = np.array([0.0, 0.0])
            for j in range(len(self.agents)):
                if i==j:
                    continue
                agent_j = self.agents[j]
                if agent_j.exited:
                    continue

                d_ij = np.linalg.norm(np.array(agent.position) - np.array(agent_j.position))
                if d_ij >= 1.4 / L_SCALE:
                    continue

                if d_ij < 0.1 / L_SCALE:
                    d_ij = 0.5 / L_SCALE
                fij = A * np.exp((d_ij - (agent.r + agent_j.r)) / B)
                fij_sum += fij * (agent.position - agent_j.position) /(d_ij)
            # fiw
            # walls
            def fi_walls(agent: Agent)->np.ndarray:
                THRESHOLD = 60/L_SCALE
                fiw_sum = np.array([0.0, 0.0])
                # left wall
                d = agent.position[1]
                if d < THRESHOLD:
                    fi_w = A * np.exp((d-agent.r) / B)
                    fiw_sum[1] += fi_w
                # right wall
                d = (WIDTH - agent.position[1])
                if d < THRESHOLD:
                    fi_w = A * np.exp((d-agent.r) / B)
                    fiw_sum[1] -= fi_w
                # top wall
                d = agent.position[0]
                if d < THRESHOLD:
                    fi_w = A * np.exp((d-agent.r) / B)
                    fiw_sum[0] += fi_w
                # bottom wall
                d = (HEIGHT - agent.position[0])
                if d < THRESHOLD:
                    fi_w = A * np.exp((d-agent.r) / B)
                    fiw_sum[0] -= fi_w

                return fiw_sum
            
            fiw_sum = fi_walls(agent)
            # fi_obstacles
            def fi_obstacles(agent: Agent)->np.ndarray:
                """Calculate the force exerted by obstacles on an agent.
                  
                  The distance is calculated from the centroid of the obstacle.
                """
                fi_o_sum = np.array([0.0, 0.0])
                for obstacle in self.obstacles:
                    # Find closest corner point of obstacle
                    corners = [
                        (obstacle.position[0], obstacle.position[1]),  
                        # top-left
                        (obstacle.position[0] + obstacle.size[0], obstacle.position[1]),
                        # top-right 
                        (obstacle.position[0], obstacle.position[1] + obstacle.size[1]),
                        # bottom-left
                        (obstacle.position[0] + obstacle.size[0], 
                         obstacle.position[1] + obstacle.size[1])
                        # bottom-right
                    ]
                    d = min(np.linalg.norm(agent.position - np.array(corner)) 
                            for corner in corners)
                    if d < 120/L_SCALE:
                        fi_o = A * np.exp((d-agent.r) / B)
                        fi_o_sum += fi_o * (agent.position - obstacle.centroid) / d
                return fi_o_sum
            
            fio_sum = fi_obstacles(agent)
            fiw_sum += fio_sum

            f_sum = fij_sum + fiw_sum
            d_v_f = f_sum / agent.m
            d_v = d_v_desired + d_v_f

            agent.v = agent.v + d_v

            # Calculate new position first without modifying agent state
            new_position = agent.position + agent.v
            new_grid_position = new_position // GRID_SIZE

            # bounds correction
            if new_grid_position[0] < 0 or new_grid_position[0] >= ROWS or \
               new_grid_position[1] < 0 or new_grid_position[1] >= COLS:
                new_grid_position = np.array([
                    int(max(0, min(new_grid_position[0], ROWS-1))),
                    int(max(0, min(new_grid_position[1], COLS-1)))
                ])
                new_position = np.floor((new_grid_position + 0.5) * GRID_SIZE)
            
            # exit check
            if self.grid[int(new_grid_position[0]), int(new_grid_position[1])] == 1:
                agent.exited = True
                logger.info(f"agent {agent.id} exited")
                continue

            exit_count = sum(agent.exited for agent in self.agents)
            if exit_count == len(self.agents):
                self.state = False
                return

            agent.grid_position = new_grid_position.astype(np.int32)
            agent.position = new_position.astype(np.int32)


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
