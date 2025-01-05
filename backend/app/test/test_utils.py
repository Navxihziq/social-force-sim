import numpy as np
from app.models.utils import grid_bfs
from app.models.sim import Simulation

def test_bfs_with_obstacles_and_exits():
    # Test case 1: Simple path to exit
    grid1 = np.array([
        [0, 0, 1],
        [0, -1, 0],
        [0, 0, 0]
    ])
    path1 = grid_bfs(grid1)
    assert path1 is not None
    assert path1[0, 0] == (1, 0)  # Should reach the exit

    # Test case 2: No path to exit
    grid2 = np.array([
        [0, -1, 1],
        [0, 0, 0],
        [0, -1, 0]
    ])
    path2 = grid_bfs(grid2)
    assert path2 is None  # Should return None when no path exists

    # Test case 3: Multiple possible paths to exits
    grid3 = np.array([
        [1, 0, 1],
        [0, 0, 0],
        [0, 0, 1]
    ])
    path3 = grid_bfs(grid3)
    assert path3 is not None
    assert path3[1, 0] == (0, -1)  # Should reach any exit

