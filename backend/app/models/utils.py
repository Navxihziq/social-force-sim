from collections import deque
import numpy as np
import logging

logger = logging.getLogger('uvicorn')

OBSTACLE = -1
EXIT = 1

GRID_SIZE = 10

def grid_bfs(grid: np.ndarray)->np.ndarray:
    """Helper function to find the shortest path from each point to the exit.

    Uses BFS to find shortest paths and updates the grid with direction vectors
    pointing toward the next step along the path to the exit.

    Args:
        grid (np.ndarray): Input grid where -1 represents obstacles, 1 represents exit,
            and 0 represents empty cells.

    Returns:
        np.ndarray: Grid with each cell containing a direction vector (dx, dy) pointing
            to the next step along the shortest path to the exit.
    """
    def bfs(start: tuple[int, int])->np.ndarray:
        """Helper function to perform BFS on the grid.

        Args:
            start (tuple[int, int]): Starting point (y, x); sorry, but normally you index [col, row]
                in a 2-d array.

        Returns:
            np.ndarray: Grid with each cell containing a direction vector (dx, dy) pointing
                to the next step along the shortest path to the exit.
        """
        queue = deque([start])
        visited = np.zeros_like(grid, dtype=np.int8)
        visited[start] = 1
        next_step = np.zeros((2, grid.shape[0], grid.shape[1]), dtype=np.int8) 
        while queue:
            y, x = queue.popleft()
            for dy, dx in [(0, 1), (0, -1), (1, 0), (-1, 0), 
                           (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                nx, ny = x + dx, y + dy
                if (0 <= ny < grid.shape[0]) and (0 <= nx < grid.shape[1]) and \
                    (grid[ny, nx] != OBSTACLE) and (visited[ny, nx] == 0):
                    queue.append((ny, nx))
                    visited[ny, nx] = 1
                    next_step[0, ny, nx] = -dy
                    next_step[1, ny, nx] = -dx
                    if grid[ny, nx] == EXIT:
                        return next_step, (ny, nx)
                    
        return next_step, (-1, -1)
    
    # start from [0, 0]
    direction_grid = np.ones((2, grid.shape[0], grid.shape[1]), dtype=np.int8) * -2
    for i in range(grid.shape[0]):  # col
        for j in range(grid.shape[1]):  # row
            if grid[i, j] == EXIT or grid[i, j] == OBSTACLE or direction_grid[0, i, j] != -2:
                continue
            else:
                next_step, (ny, nx) = bfs((i, j))
                # from (nx, ny) to (i, j)
                if (ny, nx) == (-1, -1):
                    return None
                while (ny, nx) != (i, j):
                    dy, dx = next_step[0, ny, nx], next_step[1, ny, nx]
                    nx, ny = nx + dx, ny + dy
                    direction_grid[:, ny, nx] = (-dy, -dx)
    
    return direction_grid


def distance_to_obstacle(pos: np.ndarray, obstacle) -> float:
    """Helper function to find the distance to the nearest point on the obstacle.

    Args:
        pos (np.ndarray): Position of the grid cell; in (i, j) grid coordinates.
        obstacle (Obstacle): Obstacle to calculate distance to.

    Returns:
        float: Distance to the nearest point on the obstacle in [i, j].
    """
    raw_pos = (pos + 0.5) * GRID_SIZE
    nearest_x = max(obstacle.position[1], 
                    min(obstacle.position[1] + obstacle.size[1], 
                        raw_pos[1]))  # x maps to position[1]
    nearest_y = max(obstacle.position[0], 
                    min(obstacle.position[0] + obstacle.size[0], 
                        raw_pos[0]))  # y maps to position[0]
    
    nearest_point = np.array([nearest_y, nearest_x])  # Swap back to (y,x) order
    d = np.linalg.norm(raw_pos - nearest_point)
    # direction vector
    return d, raw_pos - nearest_point


def wall_distance_grid(grid: np.ndarray)->tuple[np.ndarray, np.ndarray]:
    """Helper function to find the distance to the nearest wall or obstacle.

    Args:
        grid (np.ndarray): Input grid where -1 represents obstacles, 1 represents exit,
            and 0 represents empty cells.
        obstacles (list): List of obstacles.

    Returns:
        tuple[np.ndarray, np.ndarray]: Grid with each cell containing the distance to the nearest wall [left, top, right, bottom] and obstacles.
        and the direction grid.
    """
    distance_grid = np.zeros((4, grid.shape[0], grid.shape[1]))
    direction_grid = np.zeros((4, 2, grid.shape[0], grid.shape[1]))
    # walls
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            # left wall
            d = (j)*10
            if d <= 5:
                d=5
            distance_grid[0, i, j] = d
            direction_grid[0, :, i, j] = np.array([0, 1])
            # top wall
            d = (i)*10
            if d <= 5:
                d=5
            distance_grid[1, i, j] = d
            direction_grid[1, :, i, j] = np.array([1, 0])
            # right wall
            d = (grid.shape[1]-j-1)*10
            if d <= 5:
                d=5
            distance_grid[2, i, j] = d
            direction_grid[2, :, i, j] = np.array([0, -1])
            # bottom wall
            d = (grid.shape[0]-i-1)*10
            if d <= 5:
                d=5
            distance_grid[3, i, j] = d
            direction_grid[3, :, i, j] = np.array([-1, 0])

    return distance_grid, direction_grid


def obstacle_distance_grid(grid: np.ndarray, obstacles: list)->np.ndarray:
    """Helper function to find the distance to the nearest obstacle.

    Args:
        grid (np.ndarray): Input grid where -1 represents obstacles, 1 represents exit,
            and 0 represents empty cells.
        obstacles (list): List of obstacles.

    Returns:
        np.ndarray: Grid with each cell containing the distance to the nearest obstacle.
    """
    distance_grid = np.zeros((len(obstacles), grid.shape[0], grid.shape[1]))
    direction_grid = np.zeros((len(obstacles), 2, grid.shape[0], grid.shape[1]))
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            for k, obstacle in enumerate(obstacles):
                d, direction_vector = distance_to_obstacle(np.array([i, j]), obstacle)
                if d <= 3:
                    d=5
                distance_grid[k, i, j] = d
                direction_grid[k, :, i, j] = direction_vector / d

    return distance_grid, direction_grid


def outofbounds(pos: np.ndarray, grid_shape: tuple[int, int])->bool:
    return pos[0] < 0 or pos[0] >= grid_shape[0] or pos[1] < 0 or pos[1] >= grid_shape[1]