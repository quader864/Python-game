import curses
import random
import keyboard
import time

# ─── Constants ───────────────────────────────────────────────────
CHUNK_HEIGHT = 15   # tiles per chunk (rows)
CHUNK_WIDTH  = 30   # tiles per chunk (columns)
SCROLL_MARGIN = 3    # how close to screen edge before camera moves

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
    """Create a deterministic chunk of fixed size."""
    seed = cx * 10000 + cy
    rng = random.Random(seed)
    chunk = [[{'type': 'ground', 'discovered': False} for _ in range(CHUNK_WIDTH)]
             for _ in range(CHUNK_HEIGHT)]
    for _ in range(8):
        wy = rng.randint(0, CHUNK_HEIGHT - 1)
        wx = rng.randint(0, CHUNK_WIDTH - 1)
        chunk[wy][wx] = {'type': 'wall', 'discovered': False}
    for _ in range(5):
        ry = rng.randint(0, CHUNK_HEIGHT - 1)
        rx = rng.randint(0, CHUNK_WIDTH - 1)
        if chunk[ry][rx]['type'] == 'ground':
            chunk[ry][rx] = {'type': 'reward', 'discovered': False}
    for _ in range(3):
        ey = rng.randint(0, CHUNK_HEIGHT - 1)
        ex = rng.randint(0, CHUNK_WIDTH - 1)
        if chunk[ey][ex]['type'] == 'ground':
            chunk[ey][ex] = {'type': 'enemy', 'discovered': False}
    return chunk

# ─── Reveal around a global position ────────────────────────────
def reveal_around_global(chunks, gy, gx, radius):
    """Mark tiles within a square radius as discovered, generating chunks if needed."""
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            ny = gy + dy
            nx = gx + dx
            cx = nx // CHUNK_WIDTH
            cy = ny // CHUNK_HEIGHT
            lx = nx % CHUNK_WIDTH
            ly = ny % CHUNK_HEIGHT
            if (cx, cy) not in chunks:
                chunks[(cx, cy)] = generate_chunk(cx, cy)
            chunks[(cx, cy)][ly][lx]['discovered'] = True

# ─── Player effect (ring animation) ─────────────────────────────
def player_effect(stdscr, sy, sx, color_pair, term_h, term_w):
    stdscr.addch(sy, sx, '@', color_pair | curses.A_BOLD)
    stdscr.refresh()
    curses.napms(100)
    for radius in range(1, 4):
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if max(abs(dy), abs(dx)) == radius:
                    ny = sy + dy
                    nx = sx + dx
                    if 0 <= ny < term_h - 1 and 0 <= nx < term_w:
                        stdscr.addch(ny, nx, '*', color_pair)
        stdscr.refresh()
        curses.napms(60)

# ─── Drawing the game world ──────────────────────────────────────
def draw_game(stdscr, chunks, player_gy, player_gx, view_gy, view_gx,
              score, lives, message, message_timer, term_h, term_w,
              debug_info=None):
    stdscr.clear()
    for sy in range(term_h - 1):          # leave last line for UI
        for sx in range(term_w):
            gy = view_gy + sy
            gx = view_gx + sx
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
                stdscr.addch(sy, sx, '·', curses.color_pair(COL_UNDISCOVERED))
    # Player
    player_sy = player_gy - view_gy
    player_sx = player_gx - view_gx
    if 0 <= player_sy < term_h - 1 and 0 <= player_sx < term_w:
        stdscr.addch(player_sy, player_sx, '@', curses.color_pair(COL_PLAYER) | curses.A_BOLD)
    # UI bar (bottom line)
    ui_y = term_h - 1
    if debug_info is not None:
        stdscr.addstr(ui_y, 0, debug_info[:term_w])
    elif message_timer > 0 and message:
        stdscr.addstr(ui_y, 0, message[:term_w])
    else:
        status = f"Score: {score}  Lives: {lives}  [WASD] hold for diagonal  [Q] quit"
        stdscr.addstr(ui_y, 0, status[:term_w])
    stdscr.refresh()

# ─── Main game logic ─────────────────────────────────────────────
def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)          # getch() non‑blocking
    stdscr.keypad(True)           # so we get KEY_RESIZE
    curses.start_color()
    curses.init_pair(COL_WALL,         curses.COLOR_WHITE,   curses.COLOR_BLACK)
    curses.init_pair(COL_GROUND,       curses.COLOR_GREEN,   curses.COLOR_BLACK)
    curses.init_pair(COL_UNDISCOVERED, curses.COLOR_BLACK,   curses.COLOR_BLACK)
    curses.init_pair(COL_REWARD,       curses.COLOR_YELLOW,  curses.COLOR_BLACK)
    curses.init_pair(COL_ENEMY,        curses.COLOR_RED,     curses.COLOR_BLACK)
    curses.init_pair(COL_PLAYER,       curses.COLOR_CYAN,    curses.COLOR_BLACK)
    curses.init_pair(FLASH_REWARD,     curses.COLOR_YELLOW,  curses.COLOR_YELLOW)
    curses.init_pair(FLASH_ENEMY,      curses.COLOR_RED,     curses.COLOR_RED)

    term_h, term_w = stdscr.getmaxyx()

    # World state
    chunks = {}
    player_cx, player_cy = 0, 0
    player_lx = CHUNK_WIDTH // 2
    player_ly = CHUNK_HEIGHT // 2
    # Global coordinates
    player_gx = player_cx * CHUNK_WIDTH + player_lx
    player_gy = player_cy * CHUNK_HEIGHT + player_ly

    # Create starting chunk and safe zone
    chunks[(0, 0)] = generate_chunk(0, 0)
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            ny = player_ly + dy
            nx = player_lx + dx
            if 0 <= ny < CHUNK_HEIGHT and 0 <= nx < CHUNK_WIDTH:
                chunks[(0, 0)][ny][nx] = {'type': 'ground', 'discovered': False}

    # Initial camera: centre player on screen
    view_gy = player_gy - term_h // 2
    view_gx = player_gx - term_w // 2

    reveal_around_global(chunks, player_gy, player_gx, 5)

    score, lives = 0, 3
    message, message_timer = "", 0
    move_delay = 0.08
    last_move_time = 0
    DEBUG = False   # set True to see debug info on UI line

    while lives > 0:
        # ── Let curses process its own resize event ─────────────
        c = stdscr.getch()
        if c == curses.KEY_RESIZE:
            term_h, term_w = stdscr.getmaxyx()
            stdscr.clear()
            # Keep player visible if they would be off‑screen
            psx = player_gx - view_gx
            psy = player_gy - view_gy
            if psx < 0 or psx >= term_w or psy < 0 or psy >= term_h - 1:
                view_gy = player_gy - min(psy, max(0, (term_h - 2) - SCROLL_MARGIN))
                view_gx = player_gx - min(psx, max(0, term_w - 1 - SCROLL_MARGIN))

        # ── Edge‑scrolling camera ───────────────────────────────
        psx = player_gx - view_gx
        psy = player_gy - view_gy
        if psx > term_w - 1 - SCROLL_MARGIN:
            view_gx = player_gx - (term_w - 1 - SCROLL_MARGIN)
        elif psx < SCROLL_MARGIN:
            view_gx = player_gx - SCROLL_MARGIN
        if psy > term_h - 2 - SCROLL_MARGIN:
            view_gy = player_gy - (term_h - 2 - SCROLL_MARGIN)
        elif psy < SCROLL_MARGIN:
            view_gy = player_gy - SCROLL_MARGIN

        # ── Debug info (if enabled) ────────────────────────────
        if DEBUG:
            debug_info = (f"TERM:{term_h}x{term_w}  "
                          f"VIEW:{view_gy},{view_gx}  "
                          f"PL_SCR:{psy},{psx}")
        else:
            debug_info = None

        draw_game(stdscr, chunks, player_gy, player_gx, view_gy, view_gx,
                  score, lives, message, message_timer, term_h, term_w,
                  debug_info)

        if message_timer > 0:
            message_timer -= 1
            if message_timer == 0:
                message = ""

        # ── Input (keyboard library for simultaneous keys) ─────
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

        now = time.time()
        if now - last_move_time < move_delay:
            time.sleep(0.01)
            continue
        last_move_time = now

        # ── Movement ───────────────────────────────────────────
        new_gy = player_gy + dy
        new_gx = player_gx + dx
        dest_cx = new_gx // CHUNK_WIDTH
        dest_cy = new_gy // CHUNK_HEIGHT
        dest_lx = new_gx % CHUNK_WIDTH
        dest_ly = new_gy % CHUNK_HEIGHT

        if (dest_cx, dest_cy) not in chunks:
            chunks[(dest_cx, dest_cy)] = generate_chunk(dest_cx, dest_cy)
            chunks[(dest_cx, dest_cy)][dest_ly][dest_lx] = {'type': 'ground', 'discovered': False}

        target_tile = chunks[(dest_cx, dest_cy)][dest_ly][dest_lx]
        tile_type = target_tile['type']

        if TILE[tile_type]['passable']:
            player_gy, player_gx = new_gy, new_gx
            player_cx = player_gx // CHUNK_WIDTH
            player_cy = player_gy // CHUNK_HEIGHT
            player_lx = player_gx % CHUNK_WIDTH
            player_ly = player_gy % CHUNK_HEIGHT
            if tile_type == 'reward':
                score += 10
                target_tile['type'] = 'ground'
                target_tile['discovered'] = True
                message = "Reward collected! +10"
                message_timer = 5
                psy2 = player_gy - view_gy
                psx2 = player_gx - view_gx
                if 0 <= psy2 < term_h - 1 and 0 <= psx2 < term_w:
                    player_effect(stdscr, psy2, psx2,
                                  curses.color_pair(FLASH_REWARD), term_h, term_w)
                draw_game(stdscr, chunks, player_gy, player_gx, view_gy, view_gx,
                          score, lives, message, message_timer, term_h, term_w)
        else:
            if tile_type == 'enemy':
                lives -= 1
                target_tile['type'] = 'ground'
                target_tile['discovered'] = True
                message = "Enemy hit! -1 life"
                message_timer = 5
                psy2 = player_gy - view_gy
                psx2 = player_gx - view_gx
                if 0 <= psy2 < term_h - 1 and 0 <= psx2 < term_w:
                    player_effect(stdscr, psy2, psx2,
                                  curses.color_pair(FLASH_ENEMY), term_h, term_w)
                draw_game(stdscr, chunks, player_gy, player_gx, view_gy, view_gx,
                          score, lives, message, message_timer, term_h, term_w)

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