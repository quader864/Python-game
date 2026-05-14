# constants.py
CHUNK_HEIGHT = 15
CHUNK_WIDTH  = 30

TILE = {
    'wall':   {'char': '#', 'passable': False},
    'ground': {'char': '.', 'passable': True},
    'reward': {'char': '$', 'passable': True},
    'enemy':  {'char': 'E', 'passable': False},   # still used for generation
}