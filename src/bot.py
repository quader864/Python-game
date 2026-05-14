from .constants import CHUNK_HEIGHT, CHUNK_WIDTH, TILE
from collections import deque

class Enemy:
    def __init__(self, gy, gx):
        self.gy = gy
        self.gx = gx
        self.activated = False
        self.alive = True

    def update(self, player_gy, player_gx, chunks, occupied_positions):
        """Try to move one step toward the player; return (new_gy, new_gx)."""
        if not self.alive:
            return self.gy, self.gx

        # Always check if we've been revealed for the first time
        if not self.activated:
            cx = self.gx // CHUNK_WIDTH
            cy = self.gy // CHUNK_HEIGHT
            lx = self.gx % CHUNK_WIDTH
            ly = self.gy % CHUNK_HEIGHT
            if (cx, cy) in chunks and chunks[(cx, cy)][ly][lx].get('discovered', False):
                self.activated = True

        if not self.activated:
            return self.gy, self.gx   # still hidden, don't move

        # --- 1. Try simple greedy move (old behaviour) ---
        dy = (player_gy > self.gy) - (player_gy < self.gy)
        dx = (player_gx > self.gx) - (player_gx < self.gx)

        # Try primary axis (vertical first, then horizontal)
        if dy != 0:
            cand_y, cand_x = self.gy + dy, self.gx
            if self._is_passable(cand_y, cand_x, chunks, occupied_positions):
                return cand_y, cand_x
        if dx != 0:
            cand_y, cand_x = self.gy, self.gx + dx
            if self._is_passable(cand_y, cand_x, chunks, occupied_positions):
                return cand_y, cand_x

        # Fallback: try the other vertical direction
        for alt_dy in (-1, 1):
            if alt_dy == dy:
                continue
            cand_y, cand_x = self.gy + alt_dy, self.gx
            if self._is_passable(cand_y, cand_x, chunks, occupied_positions):
                return cand_y, cand_x

        # --- 2. Greedy move failed → use BFS pathfinding ---
        path = self._bfs_path(player_gy, player_gx, chunks, occupied_positions)
        if path and len(path) > 1:
            # path[0] is current position, path[1] is the next step
            next_y, next_x = path[1]
            if self._is_passable(next_y, next_x, chunks, occupied_positions):
                return next_y, next_x

        # If nothing works, stay put
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
        """Return a list of (y,x) positions from self to target, or None."""
        start = (self.gy, self.gx)
        goal = (target_gy, target_gx)
        if start == goal:
            return [start]

        visited = {start: None}   # pos -> parent
        queue = deque([start])

        while queue:
            y, x = queue.popleft()

            # Stop if we've moved too far from start (performance limit)
            if abs(y - self.gy) + abs(x - self.gx) > max_dist:
                continue

            for dy, dx in [(-1,0),(1,0),(0,-1),(0,1)]:
                ny, nx = y + dy, x + dx
                if (ny, nx) in visited:
                    continue
                if not self._is_passable(ny, nx, chunks, occupied):
                    continue
                visited[(ny, nx)] = (y, x)
                if (ny, nx) == goal:
                    # reconstruct path
                    path = []
                    cur = goal
                    while cur is not None:
                        path.append(cur)
                        cur = visited[cur]
                    path.reverse()
                    return path
                queue.append((ny, nx))

        # No path found within search radius
        return None