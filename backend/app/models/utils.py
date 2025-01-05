from collections import deque
import numpy as np

import logging
logger = logging.getLogger('uvicorn')

OBSTACLE = -1
EXIT = 1

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