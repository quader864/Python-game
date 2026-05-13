import curses
import random
import keyboard
import time

# ─── Constants ────────────────────────────────────────────────────
CHUNK_HEIGHT = 30   # fixed chunk size (rows)
CHUNK_WIDTH  = 80   # fixed chunk size (columns)

TILE = {
    'wall':   {'char': '#', 'passable': False, 'name': 'Wall'},
    'ground': {'char': '.', 'passable': True,  'name': 'Ground'},
    'reward': {'char': '$', 'passable': True,  'name': 'Reward'},
    'enemy':  {'char': 'E', 'passable': False, 'name': 'Enemy'},
}

COL_WALL         = 1
COL_GROUND       = 2
COL_UNDISCOVERED = 3
COL_REWARD       = 4
COL_ENEMY        = 5
COL_PLAYER       = 6
FLASH_REWARD     = 7
FLASH_ENEMY      = 8

# ─── World generation ─────────────────────────────────────────────
def generate_chunk(cx, cy):
    """Create a new chunk of fixed size."""
    seed = cx * 10000 + cy
    rng = random.Random(seed)

    chunk = [[{'type': 'ground', 'discovered': False} for _ in range(CHUNK_WIDTH)]
             for _ in range(CHUNK_HEIGHT)]

    # Random walls
    for _ in range(8):
        wy = rng.randint(0, CHUNK_HEIGHT - 1)
        wx = rng.randint(0, CHUNK_WIDTH - 1)
        chunk[wy][wx] = {'type': 'wall', 'discovered': False}

    # Random rewards
    for _ in range(5):
        ry = rng.randint(0, CHUNK_HEIGHT - 1)
        rx = rng.randint(0, CHUNK_WIDTH - 1)
        if chunk[ry][rx]['type'] == 'ground':
            chunk[ry][rx] = {'type': 'reward', 'discovered': False}

    # Random enemies
    for _ in range(3):
        ey = rng.randint(0, CHUNK_HEIGHT - 1)
        ex = rng.randint(0, CHUNK_WIDTH - 1)
        if chunk[ey][ex]['type'] == 'ground':
            chunk[ey][ex] = {'type': 'enemy', 'discovered': False}

    return chunk

# ─── Global reveal (across chunks) ────────────────────────────────
def reveal_around_global(chunks, gy, gx, radius):
    """Reveal tiles inside a square of 'radius' around global (gy, gx)."""
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            ny = gy + dy
            nx = gx + dx
            # chunk indices
            cx = nx // CHUNK_WIDTH
            cy = ny // CHUNK_HEIGHT
            lx = nx % CHUNK_WIDTH
            ly = ny % CHUNK_HEIGHT

            if (cx, cy) not in chunks:
                chunks[(cx, cy)] = generate_chunk(cx, cy)
            chunks[(cx, cy)][ly][lx]['discovered'] = True

# ─── Player effect (simplified – no erase) ───────────────────────
def player_effect(stdscr, sy, sx, color_pair, term_h, term_w):
    """Draw expanding rings, then let draw_game clean up."""
    # Flash player
    stdscr.addch(sy, sx, '@', color_pair | curses.A_BOLD)
    stdscr.refresh()
    curses.napms(100)

    for radius in range(1, 4):
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if max(abs(dy), abs(dx)) == radius:
                    ny = sy + dy
                    nx = sx + dx
                    if 0 <= ny < term_h and 0 <= nx < term_w:
                        stdscr.addch(ny, nx, '*', color_pair)
        stdscr.refresh()
        curses.napms(60)

# ─── Drawing the game view ───────────────────────────────────────
def draw_game(stdscr, chunks, player_gy, player_gx, score, lives,
              message, message_timer, term_h, term_w):
    """Render the world centered on the player, filling the terminal."""
    stdscr.clear()

    # Viewport top-left in global coordinates
    view_gy = player_gy - term_h // 2
    view_gx = player_gx - term_w // 2

    for sy in range(term_h - 1):          # leave last line for UI
        for sx in range(term_w):
            gy = view_gy + sy
            gx = view_gx + sx

            # Which chunk and local coords?
            cx = gx // CHUNK_WIDTH
            cy = gy // CHUNK_HEIGHT
            lx = gx % CHUNK_WIDTH
            ly = gy % CHUNK_HEIGHT

            if (cx, cy) in chunks:
                tile = chunks[(cx, cy)][ly][lx]
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
                    stdscr.addch(sy, sx, char, pair)
                else:
                    stdscr.addch(sy, sx, '·', curses.color_pair(COL_UNDISCOVERED))
            else:
                # Unexplored chunk -> undiscovered
                stdscr.addch(sy, sx, '·', curses.color_pair(COL_UNDISCOVERED))

    # Draw player at screen coordinates
    player_sy = player_gy - view_gy
    player_sx = player_gx - view_gx
    if 0 <= player_sy < term_h - 1 and 0 <= player_sx < term_w:
        stdscr.addch(player_sy, player_sx, '@', curses.color_pair(COL_PLAYER) | curses.A_BOLD)

    # UI bar (bottom line)
    ui_y = term_h - 1
    if message_timer > 0 and message:
        stdscr.addstr(ui_y, 0, message[:term_w])
    else:
        status = f"Score: {score}  Lives: {lives}  [WASD] hold for diagonal  [Q] quit"
        status = status[:term_w]
        stdscr.addstr(ui_y, 0, status)

    stdscr.refresh()

# ─── Main game logic ─────────────────────────────────────────────
def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.clear()

    # Initialise colours
    curses.start_color()
    curses.init_pair(COL_WALL,         curses.COLOR_WHITE,   curses.COLOR_BLACK)
    curses.init_pair(COL_GROUND,       curses.COLOR_GREEN,   curses.COLOR_BLACK)
    curses.init_pair(COL_UNDISCOVERED, curses.COLOR_BLACK,   curses.COLOR_BLACK)
    curses.init_pair(COL_REWARD,       curses.COLOR_YELLOW,  curses.COLOR_BLACK)
    curses.init_pair(COL_ENEMY,        curses.COLOR_RED,     curses.COLOR_BLACK)
    curses.init_pair(COL_PLAYER,       curses.COLOR_CYAN,    curses.COLOR_BLACK)
    curses.init_pair(FLASH_REWARD,     curses.COLOR_YELLOW,  curses.COLOR_YELLOW)
    curses.init_pair(FLASH_ENEMY,      curses.COLOR_RED,     curses.COLOR_RED)

    # Terminal size (will be updated on resize)
    term_h, term_w = stdscr.getmaxyx()

    # Game state
    chunks = {}
    player_gy = CHUNK_HEIGHT // 2   # start in centre of chunk (0,0)
    player_gx = CHUNK_WIDTH // 2

    # Create initial chunk and safe area
    initial_chunk = generate_chunk(0, 0)
    chunks[(0, 0)] = initial_chunk
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            ny = player_gy + dy
            nx = player_gx + dx
            cx = nx // CHUNK_WIDTH
            cy = ny // CHUNK_HEIGHT
            lx = nx % CHUNK_WIDTH
            ly = ny % CHUNK_HEIGHT
            if (cx, cy) not in chunks:
                chunks[(cx, cy)] = generate_chunk(cx, cy)
            chunks[(cx, cy)][ly][lx] = {'type': 'ground', 'discovered': False}

    reveal_around_global(chunks, player_gy, player_gx, 5)

    score = 0
    lives = 3
    message = ""
    message_timer = 0

    move_delay = 0.08
    last_move_time = 0

    while lives > 0:
        # ── Resize handling ──
        if curses.is_term_resized(term_h, term_w):
            term_h, term_w = stdscr.getmaxyx()
            curses.resize_term(term_h, term_w)
            stdscr.clear()

        # Compute player screen position for the effect function
        view_gy = player_gy - term_h // 2
        view_gx = player_gx - term_w // 2
        player_sy = player_gy - view_gy
        player_sx = player_gx - view_gx

        # Draw
        draw_game(stdscr, chunks, player_gy, player_gx, score, lives,
                  message, message_timer, term_h, term_w)

        # Message timer
        if message_timer > 0:
            message_timer -= 1
            if message_timer == 0:
                message = ""

        # ── Input ──
        if keyboard.is_pressed('q'):
            break

        dy, dx = 0, 0
        if keyboard.is_pressed('w'): dy -= 1
        if keyboard.is_pressed('s'): dy += 1
        if keyboard.is_pressed('a'): dx -= 1
        if keyboard.is_pressed('d'): dx += 1

        if dy == 0 and dx == 0:
            time.sleep(0.02)
            continue

        # Movement cooldown
        now = time.time()
        if now - last_move_time < move_delay:
            time.sleep(0.01)
            continue
        last_move_time = now

        # Attempt move
        new_gy = player_gy + dy
        new_gx = player_gx + dx

        # Ensure destination chunk exists
        new_cx = new_gx // CHUNK_WIDTH
        new_cy = new_gy // CHUNK_HEIGHT
        if (new_cx, new_cy) not in chunks:
            chunks[(new_cx, new_cy)] = generate_chunk(new_cx, new_cy)

        lx = new_gx % CHUNK_WIDTH
        ly = new_gy % CHUNK_HEIGHT
        target_tile = chunks[(new_cx, new_cy)][ly][lx]
        tile_type = target_tile['type']

        if TILE[tile_type]['passable']:
            # Move
            player_gy, player_gx = new_gy, new_gx

            if tile_type == 'reward':
                score += 10
                target_tile['type'] = 'ground'
                target_tile['discovered'] = True
                message = "Reward collected! +10"
                message_timer = 5
                player_effect(stdscr, player_sy, player_sx,
                              curses.color_pair(FLASH_REWARD), term_h, term_w)
                draw_game(stdscr, chunks, player_gy, player_gx, score, lives,
                          message, message_timer, term_h, term_w)
        else:
            if tile_type == 'enemy':
                lives -= 1
                target_tile['type'] = 'ground'
                target_tile['discovered'] = True
                message = "Enemy hit! -1 life"
                message_timer = 5
                player_effect(stdscr, player_sy, player_sx,
                              curses.color_pair(FLASH_ENEMY), term_h, term_w)
                draw_game(stdscr, chunks, player_gy, player_gx, score, lives,
                          message, message_timer, term_h, term_w)

        # Reveal around new position
        reveal_around_global(chunks, player_gy, player_gx, 5)

        time.sleep(0.01)

    # ─── Game Over / Quit ────────────────────────────────────────
    stdscr.clear()
    if lives <= 0:
        msg = f"GAME OVER! Final score: {score}  Press any key to exit"
    else:
        msg = f"You quit. Final score: {score}  Press any key to exit"
    stdscr.addstr(term_h // 2, (term_w - len(msg)) // 2, msg)
    stdscr.refresh()
    keyboard.read_key(suppress=True)

if __name__ == "__main__":
    curses.wrapper(main)