import curses
import random

# ─── Tile definitions ──────────────────────────────────────────────
TILE = {
    'wall':   {'char': '#', 'passable': False, 'name': 'Wall'},
    'ground': {'char': '.', 'passable': True,  'name': 'Ground'},
    'reward': {'char': '$', 'passable': True,  'name': 'Reward'},
    'enemy':  {'char': 'E', 'passable': False, 'name': 'Enemy'},
}

# ─── Colour pair IDs ──────────────────────────────────────────────
COL_WALL         = 1
COL_GROUND       = 2
COL_UNDISCOVERED = 3
COL_REWARD       = 4
COL_ENEMY        = 5
COL_PLAYER       = 6
FLASH_REWARD     = 7   # for the ring effect (yellow)
FLASH_ENEMY      = 8   # for the ring effect (red)

# ─── World generation ─────────────────────────────────────────────
def generate_chunk(cx, cy, height, width):
    """Create a deterministic chunk. All tiles start undiscovered."""
    seed = cx * 10000 + cy
    rng = random.Random(seed)

    chunk = [[{'type': 'ground', 'discovered': False} for _ in range(width)]
             for _ in range(height)]

    # Random walls
    for _ in range(8):
        wy = rng.randint(0, height - 1)
        wx = rng.randint(0, width - 1)
        chunk[wy][wx] = {'type': 'wall', 'discovered': False}

    # Random rewards
    for _ in range(5):
        ry = rng.randint(0, height - 1)
        rx = rng.randint(0, width - 1)
        if chunk[ry][rx]['type'] == 'ground':
            chunk[ry][rx] = {'type': 'reward', 'discovered': False}

    # Random enemies
    for _ in range(3):
        ey = rng.randint(0, height - 1)
        ex = rng.randint(0, width - 1)
        if chunk[ey][ex]['type'] == 'ground':
            chunk[ey][ex] = {'type': 'enemy', 'discovered': False}

    return chunk

# ─── Fog of war ───────────────────────────────────────────────────
def reveal_around(chunk, player_y, player_x, radius):
    """Mark tiles within a square radius as discovered."""
    height = len(chunk)
    width = len(chunk[0])
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            ny = player_y + dy
            nx = player_x + dx
            if 0 <= ny < height and 0 <= nx < width:
                chunk[ny][nx]['discovered'] = True

# ─── Player‑centred explosion ring ───────────────────────────────
def player_effect(stdscr, chunk, player_y, player_x, color_pair, height, width):
    """
    An expanding ring of '*' stars around the player,
    while the player symbol briefly changes colour.
    """
    # 1) Flash the player's colour
    stdscr.addch(player_y, player_x, '@', color_pair | curses.A_BOLD)
    stdscr.refresh()
    curses.napms(100)

    # 2) Expanding rings (radii 1 to 3)
    for radius in range(1, 4):
        # Draw the ring
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if max(abs(dy), abs(dx)) == radius:   # square ring
                    ny = player_y + dy
                    nx = player_x + dx
                    if 0 <= ny < height and 0 <= nx < width:
                        stdscr.addch(ny, nx, '*', color_pair)
        stdscr.refresh()
        curses.napms(60)

        # Erase the ring by restoring the map tiles beneath
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if max(abs(dy), abs(dx)) == radius:
                    ny = player_y + dy
                    nx = player_x + dx
                    if 0 <= ny < height and 0 <= nx < width:
                        tile = chunk[ny][nx]
                        if tile['discovered']:
                            char = TILE[tile['type']]['char']
                            if tile['type'] == 'wall':
                                pair = curses.color_pair(COL_WALL)
                            elif tile['type'] == 'ground':
                                pair = curses.color_pair(COL_GROUND)
                            elif tile['type'] == 'reward':
                                pair = curses.color_pair(COL_REWARD)
                            elif tile['type'] == 'enemy':
                                pair = curses.color_pair(COL_ENEMY)
                            else:
                                pair = curses.color_pair(COL_GROUND)
                            stdscr.addch(ny, nx, char, pair)
                        else:
                            stdscr.addch(ny, nx, '·', curses.color_pair(COL_UNDISCOVERED))
        stdscr.refresh()
        curses.napms(30)

    # 3) Restore normal player colour (the next draw_game will handle this)
    stdscr.addch(player_y, player_x, '@', curses.color_pair(COL_PLAYER) | curses.A_BOLD)
    stdscr.refresh()

# ─── Drawing the game view ───────────────────────────────────────
def draw_game(stdscr, chunk, player_y, player_x, score, lives, chunk_coords,
              message, message_timer, height, width):
    """Draw the current chunk, player, and UI."""
    stdscr.clear()

    # Draw map
    for y in range(height):
        for x in range(width):
            tile = chunk[y][x]
            if not tile['discovered']:
                stdscr.addch(y, x, '·', curses.color_pair(COL_UNDISCOVERED))
            else:
                ttype = tile['type']
                char = TILE[ttype]['char']
                if ttype == 'wall':
                    stdscr.addch(y, x, char, curses.color_pair(COL_WALL))
                elif ttype == 'ground':
                    stdscr.addch(y, x, char, curses.color_pair(COL_GROUND))
                elif ttype == 'reward':
                    stdscr.addch(y, x, char, curses.color_pair(COL_REWARD))
                elif ttype == 'enemy':
                    stdscr.addch(y, x, char, curses.color_pair(COL_ENEMY))

    # Draw player
    stdscr.addch(player_y, player_x, '@', curses.color_pair(COL_PLAYER) | curses.A_BOLD)

    # Draw UI bar (bottom line)
    ui_y = height
    if message_timer > 0 and message:
        stdscr.addstr(ui_y, 0, message)
    else:
        cx, cy = chunk_coords
        status = f"Score: {score}  Lives: {lives}  Chunk: ({cx},{cy})  [WASD] move  [Q] quit"
        stdscr.addstr(ui_y, 0, status)

    stdscr.refresh()

# ─── Main game logic ─────────────────────────────────────────────
def main(stdscr):
    # Curses setup
    curses.curs_set(0)
    stdscr.nodelay(0)
    stdscr.clear()

    # Initialise colour pairs
    curses.start_color()
    curses.init_pair(COL_WALL,         curses.COLOR_WHITE,   curses.COLOR_BLACK)
    curses.init_pair(COL_GROUND,       curses.COLOR_GREEN,   curses.COLOR_BLACK)
    curses.init_pair(COL_UNDISCOVERED, curses.COLOR_BLACK,   curses.COLOR_BLACK)  # almost invisible
    curses.init_pair(COL_REWARD,       curses.COLOR_YELLOW,  curses.COLOR_BLACK)
    curses.init_pair(COL_ENEMY,        curses.COLOR_RED,     curses.COLOR_BLACK)
    curses.init_pair(COL_PLAYER,       curses.COLOR_CYAN,    curses.COLOR_BLACK)
    curses.init_pair(FLASH_REWARD,     curses.COLOR_YELLOW,  curses.COLOR_YELLOW)  # solid yellow
    curses.init_pair(FLASH_ENEMY,      curses.COLOR_RED,     curses.COLOR_RED)     # solid red

    max_y, max_x = stdscr.getmaxyx()
    MAP_HEIGHT = max_y - 1
    MAP_WIDTH = max_x
    VIEW_RADIUS = 5

    # Chunk storage
    chunks = {}
    player_cx, player_cy = 0, 0
    player_ly = MAP_HEIGHT // 2
    player_lx = MAP_WIDTH // 2

    # Initial chunk
    initial_chunk = generate_chunk(0, 0, MAP_HEIGHT, MAP_WIDTH)
    chunks[(0, 0)] = initial_chunk

    # Create a safe starting area (3x3 ground, still undiscovered until revealed)
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            ny = player_ly + dy
            nx = player_lx + dx
            if 0 <= ny < MAP_HEIGHT and 0 <= nx < MAP_WIDTH:
                initial_chunk[ny][nx] = {'type': 'ground', 'discovered': False}

    # Reveal initial area
    reveal_around(initial_chunk, player_ly, player_lx, VIEW_RADIUS)

    score = 0
    lives = 3
    message = ""
    message_timer = 0

    # Main loop
    while lives > 0:
        current_chunk = chunks[(player_cx, player_cy)]
        draw_game(stdscr, current_chunk, player_ly, player_lx, score, lives,
                  (player_cx, player_cy), message, message_timer,
                  MAP_HEIGHT, MAP_WIDTH)

        # Message timer countdown
        if message_timer > 0:
            message_timer -= 1
            if message_timer == 0:
                message = ""

        key = stdscr.getch()
        new_ly, new_lx = player_ly, player_lx

        if key in (ord('w'), ord('W')):
            new_ly -= 1
        elif key in (ord('s'), ord('S')):
            new_ly += 1
        elif key in (ord('a'), ord('A')):
            new_lx -= 1
        elif key in (ord('d'), ord('D')):
            new_lx += 1
        elif key in (ord('q'), ord('Q')):
            break

        # Wrap across chunk borders
        new_cx, new_cy = player_cx, player_cy
        if new_lx < 0:
            new_cx -= 1
            new_lx = MAP_WIDTH - 1
        elif new_lx >= MAP_WIDTH:
            new_cx += 1
            new_lx = 0

        if new_ly < 0:
            new_cy -= 1
            new_ly = MAP_HEIGHT - 1
        elif new_ly >= MAP_HEIGHT:
            new_cy += 1
            new_ly = 0

        target_coords = (new_cx, new_cy)

        # Generate chunk if missing
        if target_coords not in chunks:
            chunks[target_coords] = generate_chunk(new_cx, new_cy, MAP_HEIGHT, MAP_WIDTH)
            # Make the entry tile safe
            chunks[target_coords][new_ly][new_lx] = {'type': 'ground', 'discovered': False}

        target_tile = chunks[target_coords][new_ly][new_lx]
        tile_type = target_tile['type']

        if TILE[tile_type]['passable']:
            # Move player
            player_cx, player_cy = new_cx, new_cy
            player_ly, player_lx = new_ly, new_lx

            if tile_type == 'reward':
                score += 10
                target_tile['type'] = 'ground'
                target_tile['discovered'] = True
                message = "Reward collected! +10"
                message_timer = 5
                player_effect(stdscr, chunks[(player_cx, player_cy)],
                              player_ly, player_lx,
                              curses.color_pair(FLASH_REWARD),
                              MAP_HEIGHT, MAP_WIDTH)
                # Redraw after effect to clear rings properly
                draw_game(stdscr, chunks[(player_cx, player_cy)],
                          player_ly, player_lx, score, lives,
                          (player_cx, player_cy), message, message_timer,
                          MAP_HEIGHT, MAP_WIDTH)
        else:
            if tile_type == 'enemy':
                lives -= 1
                target_tile['type'] = 'ground'
                target_tile['discovered'] = True
                message = "Enemy hit! -1 life"
                message_timer = 5
                player_effect(stdscr, chunks[(player_cx, player_cy)],
                              player_ly, player_lx,
                              curses.color_pair(FLASH_ENEMY),
                              MAP_HEIGHT, MAP_WIDTH)
                draw_game(stdscr, chunks[(player_cx, player_cy)],
                          player_ly, player_lx, score, lives,
                          (player_cx, player_cy), message, message_timer,
                          MAP_HEIGHT, MAP_WIDTH)
            # Player does not move

        # Reveal around new position
        current_chunk = chunks[(player_cx, player_cy)]
        reveal_around(current_chunk, player_ly, player_lx, VIEW_RADIUS)

    # ─── Game Over / Quit ────────────────────────────────────────
    stdscr.clear()
    if lives <= 0:
        msg = f"GAME OVER! Final score: {score}  Press any key to exit"
    else:
        msg = f"You quit. Final score: {score}  Press any key to exit"
    stdscr.addstr(max_y // 2, max_x // 2 - len(msg) // 2, msg)
    stdscr.refresh()
    stdscr.getch()

if __name__ == "__main__":
    curses.wrapper(main)