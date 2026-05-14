from .constants import CHUNK_HEIGHT, CHUNK_WIDTH, TILE
from collections import deque

class Enemy:
    def __init__(self, gy, gx):
        self.gy = gy
        self.gx = gx
        self.activated = False
        self.alive = True

    def update(self, player_gy, player_gx, chunks, occupied_positions):
        """Move one step toward the player using BFS pathfinding."""
        if not self.alive:
            return self.gy, self.gx

        # Activate when the enemy's tile becomes discovered
        if not self.activated:
            cx = self.gx // CHUNK_WIDTH
            cy = self.gy // CHUNK_HEIGHT
            lx = self.gx % CHUNK_WIDTH
            ly = self.gy % CHUNK_HEIGHT
            if (cx, cy) in chunks and chunks[(cx, cy)][ly][lx].get('discovered', False):
                self.activated = True
        if not self.activated:
            return self.gy, self.gx

        # Always use BFS to find the shortest path
        path = self._bfs_path(player_gy, player_gx, chunks, occupied_positions)
        if path and len(path) > 1:
            next_y, next_x = path[1]
            if self._is_passable(next_y, next_x, chunks, occupied_positions):
                return next_y, next_x

        # If no path is found, stay in place
        return self.gy, self.gx

    def _is_passable(self, gy, gx, chunks, occupied):
        cx = gx // CHUNK_WIDTH
        cy = gy // CHUNK_HEIGHT
        lx = gx % CHUNK_WIDTH
        ly = gy % CHUNK_HEIGHT
        if (cx, cy) not in chunks:
            return False
        tile = chunks[(cx, cy)][ly][lx]
        if not TILE[tile['type']]['passable']:
            return False
        if occupied and (gy, gx) in occupied:
            return False
        return True

    def _bfs_path(self, target_gy, target_gx, chunks, occupied, max_dist=20):
        """Breadth‑first search from self to target, up to max_dist steps."""
        start = (self.gy, self.gx)
        goal = (target_gy, target_gx)
        if start == goal:
            return [start]

        visited = {start: None}
        queue = deque([start])

        while queue:
            y, x = queue.popleft()
            if abs(y - self.gy) + abs(x - self.gx) > max_dist:
                continue

            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ny, nx = y + dy, x + dx
                if (ny, nx) in visited:
                    continue
                if not self._is_passable(ny, nx, chunks, occupied):
                    continue
                visited[(ny, nx)] = (y, x)
                if (ny, nx) == goal:
                    # Reconstruct path
                    path = []
                    cur = goal
                    while cur is not None:
                        path.append(cur)
                        cur = visited[cur]
                    path.reverse()
                    return path
                queue.append((ny, nx))
        return None