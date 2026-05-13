🕹️ Curses Chunk Adventure
A terminal-based exploration game built with Python's curses library. Explore a dynamic, chunk-generated world, collect rewards, and avoid enemies — all from the comfort of your command line.

⚠️ Status: Early development — core mechanics implemented, but features and polish are actively being added.

🎮 Gameplay
You control a player character navigating an infinite, chunk-based world. Your goals are simple:

✅ Collect rewards to increase your score

👾 Avoid enemies — contact will hurt or end your run

🧭 Explore new chunks as you move through the world

The game world is divided into chunks, which are generated on the fly as you explore. This allows for a potentially endless map with efficient memory usage.

🕹️ Controls
Key	Action
W / ↑	Move up
S / ↓	Move down
A / ←	Move left
D / →	Move right
Q	Quit game
(Add more keys as needed — e.g., R to restart, P to pause)

🧱 Chunk System
The world is split into fixed-size chunks (e.g., 20x20 tiles)

New chunks are generated when the player approaches their boundaries

Chunks can contain:

Walls / obstacles

Collectible rewards

Enemies with simple AI

Generated chunks are cached; visited chunks remain persistent during a session

🛠️ Installation & Running
Requirements
Python 3.7+

curses (built-in on Linux/macOS; on Windows use windows-curses)

Setup
bash
# Clone the repository
git clone https://github.com/yourusername/your-game-repo.git
cd your-game-repo

# (Optional but recommended) Create a virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install Windows curses if needed (Linux/macOS skip this)
pip install windows-curses
Run the Game
bash
python main.py
(Adjust the entry point file name if needed)

🧪 Current Development Focus
Enemy pathfinding (basic chase behavior)

Score tracking and high scores

Game over / respawn mechanics

More reward types and enemy variations

Save/load world state

Better UI (health bars, score display)

🐛 Known Issues
Enemies may overlap with rewards at chunk borders

Chunk regeneration on revisit can sometimes shift layouts

Terminal resizing can break display — recommended to lock terminal size

🤝 Contributing
This is a personal project, but suggestions and bug reports are welcome. Feel free to open an issue or reach out.

📝 License
(Choose one, e.g., MIT, GPL, or "All rights reserved")
MIT License — see LICENSE file for details.

🙌 Acknowledgments
Python curses documentation and community

Inspiration from classic roguelikes and grid-based exploration games

Happy exploring — and watch your back! 👀