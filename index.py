import time
import random
import curses
import hashlib
stdscr = curses.initscr()
curses.noecho()
curses.cbreak()
stdscr.keypad(True)
seed=time.time()
chunk_x=0
chunk_y=0
hashedseed=int(hashlib.md5(f"{seed},{chunk_x},{chunk_y}".encode()).hexdigest()[:16], 16)
print(hashedseed)
maxl=curses.LINES-1
maxc=curses.COLS-1
world= []
rng=hashedseed
rng.choice(['.', '#', '"', '~'])

def init():
    for i in range(0,maxl):
        world.append([])
        for l in range(0,maxc):
            world[i].append('*')

def draw():
    for i in range(0,maxl):
        for l in range(0,maxc):
            stdscr.addch(i,l,world[i][l])
              
stdscr.refresh()

init()
draw()
stdscr.refresh()
stdscr.getkey()