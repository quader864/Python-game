import curses, time

def main(stdscr):
    stdscr.nodelay(True)
    curses.curs_set(0)
    while True:
        c = stdscr.getch()
        if c == curses.KEY_RESIZE:
            h, w = stdscr.getmaxyx()
            stdscr.clear()
            stdscr.addstr(0, 0, f"{h}x{w}  (resized!)")
            stdscr.refresh()
        elif c == ord('q'):
            break
        time.sleep(0.02)

curses.wrapper(main)