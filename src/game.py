import curses
import random
import keyboard
import time
from .constants import CHUNK_HEIGHT, CHUNK_WIDTH, TILE
from .bot import Enemy
from . import config

SCROLL_MARGIN = 3

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
    for _ in range(config.ENEMY_SPAWN_COUNT):
        ey = rng.randint(0, CHUNK_HEIGHT - 1)
        ex = rng.randint(0, CHUNK_WIDTH - 1)
        if chunk[ey][ex]['type'] == 'ground':
            chunk[ey][ex] = {'type': 'enemy', 'discovered': False}
    return chunk

# ─── Convert static enemy tiles into dynamic Enemy objects ──────
def spawn_enemies_from_chunk(chunks, enemies, cx, cy):
    """Replace enemy tiles with ground and create Enemy objects."""
    if (cx, cy) not in chunks:
        return
    chunk = chunks[(cx, cy)]
    for ly in range(CHUNK_HEIGHT):
        for lx in range(CHUNK_WIDTH):
            if chunk[ly][lx]['type'] == 'enemy':
                chunk[ly][lx] = {'type': 'ground', 'discovered': False}
                gy = cy * CHUNK_HEIGHT + ly
                gx = cx * CHUNK_WIDTH + lx
                enemies.append(Enemy(gy, gx))

# ─── Reveal around a global position ────────────────────────────
def reveal_around_global(chunks, enemies, gy, gx, radius):
    """Mark tiles as discovered, generate new chunks, spawn enemies."""
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
                spawn_enemies_from_chunk(chunks, enemies, cx, cy)
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

def draw_game(stdscr, chunks, enemies, player_gy, player_gx, view_gy, view_gx,
              score, lives, message, message_timer, term_h, term_w,
              debug_info=None):
    stdscr.clear()
    real_h, real_w = stdscr.getmaxyx()

    for sy in range(real_h - 1):
        for sx in range(real_w):
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
                    if 0 <= sy < real_h - 1 and 0 <= sx < real_w:
                        stdscr.addch(sy, sx, char, pair)
                else:
                    if 0 <= sy < real_h - 1 and 0 <= sx < real_w:
                        stdscr.addch(sy, sx, '·', curses.color_pair(COL_UNDISCOVERED))
            else:
                if 0 <= sy < real_h - 1 and 0 <= sx < real_w:
                    stdscr.addch(sy, sx, '·', curses.color_pair(COL_UNDISCOVERED))

    # ── Draw enemies (dynamic) ──────────────────────────────────
        # ── Draw enemies (only if their current tile is discovered) ──
    for enemy in enemies:
        if enemy.alive:
            ecx = enemy.gx // CHUNK_WIDTH
            ecy = enemy.gy // CHUNK_HEIGHT
            elx = enemy.gx % CHUNK_WIDTH
            ely = enemy.gy % CHUNK_HEIGHT
            if ((ecx, ecy) in chunks and 
                chunks[(ecx, ecy)][ely][elx].get('discovered', False)):
                esy = enemy.gy - view_gy
                esx = enemy.gx - view_gx
                if 0 <= esy < real_h - 1 and 0 <= esx < real_w:
                    stdscr.addch(esy, esx, 'E', 
                                 curses.color_pair(COL_ENEMY) | curses.A_BOLD)

    # ── Draw player ─────────────────────────────────────────────
    player_sy = player_gy - view_gy
    player_sx = player_gx - view_gx
    if 0 <= player_sy < real_h - 1 and 0 <= player_sx < real_w:
        stdscr.addch(player_sy, player_sx, '@', curses.color_pair(COL_PLAYER) | curses.A_BOLD)

    # UI bar
    ui_y = real_h - 1
    if debug_info is not None:
        line = debug_info[:real_w-1].ljust(real_w - 1)
    elif message_timer > 0 and message:
        line = message[:real_w-1].ljust(real_w - 1)
    else:
        status = f"Score: {score}  Lives: {lives}  [WASD] hold for diagonal  [Q] quit"
        line = status[:real_w-1].ljust(real_w - 1)

    try:
        stdscr.addstr(ui_y, 0, line)
    except curses.error:
        try:
            stdscr.addstr(ui_y, 0, line[:real_w-1])
        except:
            pass

    stdscr.refresh()

# ─── Main game logic ─────────────────────────────────────────────
def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)
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
    enemies = []                # dynamic enemies list
    enemy_move_delay = config.ENEMY_MOVE_DELAY    # seconds between enemy moves
    last_enemy_move_time = 0

    player_cx, player_cy = 0, 0
    player_lx = CHUNK_WIDTH // 2
    player_ly = CHUNK_HEIGHT // 2
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

    # Spawn dynamic enemies from the initial chunk
    spawn_enemies_from_chunk(chunks, enemies, 0, 0)

    # Initial camera
    view_gy = player_gy - term_h // 2
    view_gx = player_gx - term_w // 2

    reveal_around_global(chunks, enemies, player_gy, player_gx, 5)

    score, lives = 0, 3
    message, message_timer = "", 0
    move_delay = 0.08
    last_move_time = 0
    DEBUG = False

    while lives > 0:
        # Resize handling
        c = stdscr.getch()
        if c == curses.KEY_RESIZE:
            term_h, term_w = stdscr.getmaxyx()
            stdscr.clear()
            psx = player_gx - view_gx
            psy = player_gy - view_gy
            if psx < 0 or psx >= term_w or psy < 0 or psy >= term_h - 1:
                view_gy = player_gy - min(psy, max(0, (term_h - 2) - SCROLL_MARGIN))
                view_gx = player_gx - min(psx, max(0, term_w - 1 - SCROLL_MARGIN))

        # Edge scrolling
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

        # Debug info
        debug_info = None
        if DEBUG:
            debug_info = (f"TERM:{term_h}x{term_w}  "
                          f"VIEW:{view_gy},{view_gx}  "
                          f"PL_SCR:{psy},{psx}")

        draw_game(stdscr, chunks, enemies, player_gy, player_gx, view_gy, view_gx,
                  score, lives, message, message_timer, term_h, term_w,
                  debug_info)
        term_h, term_w = stdscr.getmaxyx()

        if message_timer > 0:
            message_timer -= 1
            if message_timer == 0:
                message = ""

        # Quit check
                # ── Input (keyboard library for simultaneous keys) ─────
        try:
            if keyboard.is_pressed('q'):
                break
        except Exception:
            break

        dy, dx = 0, 0
        if keyboard.is_pressed('w'): dy -= 1
        if keyboard.is_pressed('s'): dy += 1
        if keyboard.is_pressed('a'): dx -= 1
        if keyboard.is_pressed('d'): dx += 1

        # ── Player movement (only if a key is pressed and delay passed) ──
        if dy != 0 or dx != 0:
            now = time.time()
            if now - last_move_time >= move_delay:
                last_move_time = now

                new_gy = player_gy + dy
                new_gx = player_gx + dx
                dest_cx = new_gx // CHUNK_WIDTH
                dest_cy = new_gy // CHUNK_HEIGHT
                dest_lx = new_gx % CHUNK_WIDTH
                dest_ly = new_gy % CHUNK_HEIGHT

                if (dest_cx, dest_cy) not in chunks:
                    chunks[(dest_cx, dest_cy)] = generate_chunk(dest_cx, dest_cy)
                    spawn_enemies_from_chunk(chunks, enemies, dest_cx, dest_cy)
                    chunks[(dest_cx, dest_cy)][dest_ly][dest_lx] = {'type': 'ground', 'discovered': False}

                target_tile = chunks[(dest_cx, dest_cy)][dest_ly][dest_lx]
                tile_type = target_tile['type']

                if TILE[tile_type]['passable']:
                    player_gy, player_gx = new_gy, new_gx
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

        # ── Reveal area always (even when idle, to light up new chunks) ──
        reveal_around_global(chunks, enemies, player_gy, player_gx, 5)

        # ── Enemy movement (runs every tick, independently of player) ──
        now = time.time()
        if now - last_enemy_move_time >= enemy_move_delay:
            occupied_set = {(e.gy, e.gx) for e in enemies if e.alive}
            player_hit_this_tick = False

            for enemy in enemies:
                if not enemy.alive:
                    continue
                # Remove self from occupied so it can move
                occupied_set.discard((enemy.gy, enemy.gx))
                new_gy, new_gx = enemy.update(player_gy, player_gx, chunks, occupied_set)

                if new_gy == player_gy and new_gx == player_gx:
                    if not player_hit_this_tick:
                        lives -= 1
                        player_hit_this_tick = True
                    enemy.alive = False
                    message = "Enemy hit! -1 life"
                    message_timer = 5
                    psy2 = player_gy - view_gy
                    psx2 = player_gx - view_gx
                    if 0 <= psy2 < term_h - 1 and 0 <= psx2 < term_w:
                        player_effect(stdscr, psy2, psx2,
                                      curses.color_pair(FLASH_ENEMY), term_h, term_w)
                else:
                    enemy.gy, enemy.gx = new_gy, new_gx
                    occupied_set.add((new_gy, new_gx))

            last_enemy_move_time = now

        time.sleep(0.01)

    # ─── Game Over / Quit ────────────────────────────────────────
    try:
        stdscr.clear()
        if lives <= 0:
            msg = f"GAME OVER! Final score: {score}  Press any key to exit"
        else:
            msg = f"You quit. Final score: {score}  Press any key to exit"
        h, w = stdscr.getmaxyx()
        msg = msg[:w-1] if w > 1 else msg
        y = max(0, h // 2)
        x = max(0, (w - len(msg)) // 2)
        if h > 0 and w > 0:
            try:
                stdscr.addstr(y, x, msg)
            except curses.error:
                for i, ch in enumerate(msg):
                    try:
                        if x + i < w:
                            stdscr.addch(y, x + i, ch)
                    except curses.error:
                        pass
        stdscr.refresh()
        time.sleep(0.5)
        keyboard.read_key(suppress=True)
    except:
        pass
    finally:
        pass
    return score

def run():
    try:
        curses.wrapper(main)
    except curses.error:
        pass
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Game crashed: {e}")
        input("Press Enter to continue...")

if __name__ == "__main__":
    run()