import curses
import time
import keyboard
from src.game import run 

class GameMenu:
    """Animated terminal menu for the game."""
    
    def __init__(self):
        self.options = [
            "New Game",
            "Load Game",
            "Options",
            "Credits",
            "Quit"
        ]
        self.selected = 0
        self.running = True
        self.animation_frame = 0
        
        # Color pairs (will be initialized in curses)
        self.COL_MENU_NORMAL = 1
        self.COL_MENU_SELECTED = 2
        self.COL_MENU_TITLE = 3
        self.COL_MENU_DISABLED = 4
        self.COL_MENU_BORDER = 5
        
        # ASCII art title
        self.title = [
    "+==========================================+",
    "|                                          |",
    "|              D U N G E O N               |",
    "|            C R A W L E R                 |",
    "|                                          |",
    "|    A Terminal Roguelike Adventure        |",
    "|                                          |",
    "+==========================================+",
]
        
    def init_colors(self):
        """Initialize color pairs for the menu."""
        curses.start_color()
        curses.init_pair(self.COL_MENU_NORMAL, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(self.COL_MENU_SELECTED, curses.COLOR_BLACK, curses.COLOR_CYAN)
        curses.init_pair(self.COL_MENU_TITLE, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(self.COL_MENU_DISABLED, curses.COLOR_BLACK, curses.COLOR_BLACK)
        curses.init_pair(self.COL_MENU_BORDER, curses.COLOR_CYAN, curses.COLOR_BLACK)
    
    def draw_frame(self, stdscr, h, w):
        """Draw the menu with border and decorations."""
        # Clear screen
        stdscr.clear()
        
        # Use ASCII border characters instead of Unicode (more compatible)
        # Or use addstr for Unicode characters
        border_top_left = '+'
        border_top_right = '+'
        border_bottom_left = '+'
        border_bottom_right = '+'
        border_horizontal = '-'
        border_vertical = '|'
        
        # Draw border
        for y in range(h):
            for x in range(w):
                if y == 0 and x == 0:
                    try:
                        stdscr.addstr(y, x, border_top_left, 
                                    curses.color_pair(self.COL_MENU_BORDER))
                    except curses.error:
                        pass
                elif y == 0 and x == w - 1:
                    try:
                        stdscr.addstr(y, x, border_top_right, 
                                    curses.color_pair(self.COL_MENU_BORDER))
                    except curses.error:
                        pass
                elif y == h - 1 and x == 0:
                    try:
                        stdscr.addstr(y, x, border_bottom_left, 
                                    curses.color_pair(self.COL_MENU_BORDER))
                    except curses.error:
                        pass
                elif y == h - 1 and x == w - 1:
                    try:
                        stdscr.addstr(y, x, border_bottom_right, 
                                    curses.color_pair(self.COL_MENU_BORDER))
                    except curses.error:
                        pass
                elif y == 0 or y == h - 1:
                    try:
                        stdscr.addstr(y, x, border_horizontal, 
                                    curses.color_pair(self.COL_MENU_BORDER))
                    except curses.error:
                        pass
                elif x == 0 or x == w - 1:
                    try:
                        stdscr.addstr(y, x, border_vertical, 
                                    curses.color_pair(self.COL_MENU_BORDER))
                    except curses.error:
                        pass
        
        # Draw title (centered)
        title_y = max(1, h // 2 - len(self.title) - 5)
        for i, line in enumerate(self.title):
            if title_y + i < h - 1:
                x_start = max(0, (w - len(line)) // 2)
                try:
                    stdscr.addstr(title_y + i, x_start, line, 
                                curses.color_pair(self.COL_MENU_TITLE) | curses.A_BOLD)
                except curses.error:
                    pass
        
        # Draw options
        options_y = title_y + len(self.title) + 2
        for i, option in enumerate(self.options):
            if options_y + i >= h - 2:
                break
            
            text = f"  {option}  "
            x_start = (w - len(text)) // 2
            
            if option == "Load Game":
                if i == self.selected:
                    try:
                        stdscr.addstr(options_y + i, x_start, text,
                                    curses.color_pair(self.COL_MENU_DISABLED) | curses.A_BOLD)
                    except curses.error:
                        pass
                else:
                    try:
                        stdscr.addstr(options_y + i, x_start, text,
                                    curses.color_pair(self.COL_MENU_DISABLED))
                    except curses.error:
                        pass
            elif i == self.selected:
                try:
                    stdscr.addstr(options_y + i, x_start, " " * len(text),
                                curses.color_pair(self.COL_MENU_SELECTED))
                    stdscr.addstr(options_y + i, x_start, text,
                                curses.color_pair(self.COL_MENU_SELECTED) | curses.A_BOLD)
                except curses.error:
                    pass
            else:
                try:
                    stdscr.addstr(options_y + i, x_start, text,
                                curses.color_pair(self.COL_MENU_NORMAL))
                except curses.error:
                    pass
        
        # Draw hint at bottom
        hint = "Arrow Keys / W,S: Navigate  Enter: Select  Q: Quit"
        hint_y = h - 2
        hint_x = max(0, (w - len(hint)) // 2)
        try:
            stdscr.addstr(hint_y, hint_x, hint, 
                        curses.color_pair(self.COL_MENU_BORDER) | curses.A_DIM)
        except curses.error:
            pass
        
        stdscr.refresh()
    def run(self, stdscr):
        """Main menu loop."""
        # Setup
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.keypad(True)
        self.init_colors()
        
        h, w = stdscr.getmaxyx()
        last_key_time = 0
        key_delay = 0.15  # Prevent too-fast navigation
        
        while self.running:
            # Handle resize
            c = stdscr.getch()
            if c == curses.KEY_RESIZE:
                h, w = stdscr.getmaxyx()
            
            # Draw current frame
            self.draw_frame(stdscr, h, w)
            
            # Animation (subtle border pulse)
            self.animation_frame += 1
            
            # Handle input with keyboard library for responsiveness
            current_time = time.time()
            
            if current_time - last_key_time > key_delay:
                if keyboard.is_pressed('up') or keyboard.is_pressed('w'):
                    self.selected = (self.selected - 1) % len(self.options)
                    last_key_time = current_time
                elif keyboard.is_pressed('down') or keyboard.is_pressed('s'):
                    self.selected = (self.selected + 1) % len(self.options)
                    last_key_time = current_time
                elif keyboard.is_pressed('enter'):
                    selected_option = self.options[self.selected]
                    if selected_option == "Quit":
                        self.running = False
                        return "quit"
                    elif selected_option == "New Game":
                        self.running = False
                        return "new_game"
                    elif selected_option == "Load Game":
                        # Do nothing for now (disabled)
                        pass
                    elif selected_option == "Options":
                        self.running = False
                        return "options"
                    elif selected_option == "Credits":
                        self.running = False
                        return "credits"
                    last_key_time = current_time
            
            if keyboard.is_pressed('q'):
                self.running = False
                return "quit"
            
            time.sleep(0.03)
        
        return "quit"


class OptionsMenu:
    """Options submenu (placeholder for future settings)."""
    
    def __init__(self):
        self.options = [
            "Game Speed: Normal",
            "Enemy Difficulty: Normal",
            "Color Theme: Classic",
            "Sound: Off",
            "Back to Main Menu"
        ]
        self.selected = 0
        self.running = True
        
    def init_colors(self):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    
    def draw_frame(self, stdscr, h, w):
        stdscr.clear()
        
        title = "OPTIONS"
        title_y = h // 3
        try:
            stdscr.addstr(title_y, (w - len(title)) // 2, title, 
                         curses.color_pair(3) | curses.A_BOLD)
        except curses.error:
            pass
        
        for i, option in enumerate(self.options):
            y = title_y + 3 + i
            if y >= h - 2:
                break
            
            text = f"  {option}  "
            x = (w - len(text)) // 2
            
            if i == self.selected:
                stdscr.addstr(y, x, " " * len(text), curses.color_pair(2))
                stdscr.addstr(y, x, text, curses.color_pair(2) | curses.A_BOLD)
            else:
                stdscr.addstr(y, x, text, curses.color_pair(1))
        
        hint = "↑↓: Navigate  Enter: Select  B: Back"
        try:
            stdscr.addstr(h - 2, (w - len(hint)) // 2, hint, 
                         curses.color_pair(3) | curses.A_DIM)
        except curses.error:
            pass
        
        stdscr.refresh()
    
    def run(self, stdscr):
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.keypad(True)
        self.init_colors()
        
        h, w = stdscr.getmaxyx()
        last_key_time = 0
        key_delay = 0.15
        
        while self.running:
            c = stdscr.getch()
            if c == curses.KEY_RESIZE:
                h, w = stdscr.getmaxyx()
            
            self.draw_frame(stdscr, h, w)
            
            current_time = time.time()
            if current_time - last_key_time > key_delay:
                if keyboard.is_pressed('up') or keyboard.is_pressed('w'):
                    self.selected = (self.selected - 1) % len(self.options)
                    last_key_time = current_time
                elif keyboard.is_pressed('down') or keyboard.is_pressed('s'):
                    self.selected = (self.selected + 1) % len(self.options)
                    last_key_time = current_time
                elif keyboard.is_pressed('enter'):
                    if self.options[self.selected] == "Back to Main Menu":
                        self.running = False
                        return "back"
                    # Other options are placeholders
                    last_key_time = current_time
                elif keyboard.is_pressed('b'):
                    self.running = False
                    return "back"
            
            time.sleep(0.03)
        
        return "back"
class CreditsScreen:
    """Epic cinematic scrolling credits."""
    
    def __init__(self):
        self.credits_text = [
    "",
    "",
    "",
    "DUNGEON CRAWLER",
    "",
    "A Terminal Roguelike Adventure",
    "",
    "",
    "CREATED BY",
    "Quader",
    "",
    "THE SOLO DEVELOPER",
    "No collaborators. No testers.",
    "Just one person, one terminal,",
    "and a dream.",
    "",
    "",
    "INSPIRATION",
    "The Internet Went Down.",
    "",
    "When Iran faced an internet shutdown,",
    "something beautiful was born.",
    "No YouTube. No Google. No distractions.",
    "Just pure, unfiltered creativity.",
    "",
    "They say necessity is the mother of invention.",
    "They're right.",
    "",
    "",
    "DEVELOPMENT TIME",
    "1 Week",
    "",
    "Seven days of focused creation.",
    "No internet meant no Stack Overflow,",
    "no tutorials, no copy-paste.",
    "Every line of code came from the mind.",
    "",
    "",
    "THE HARDEST BATTLE",
    "Making It Responsive",
    "",
    "The terminal had to resize.",
    "The map had to fill the screen.",
    "The curses library fought back.",
    "",
    "But curses lost.",
    "",
    "",
    "SOUNDTRACK",
    "",
    "\"Happy Nation\" by Ace of Base",
    "On repeat. For an entire week.",
    "",
    "A song about a perfect world",
    "playing while building one.",
    "Poetic, isn't it?",
    "",
    "",
    "BEVERAGE OF CHOICE",
    "Tea (But Water Is The King)",
    "",
    "Hot tea for the cold nights.",
    "Water for the marathon sessions.",
    "No coffee needed when you have",
    "determination flowing through your veins.",
    "",
    "",
    "LOCATION",
    "Iran",
    "",
    "The Five Star Country.",
    "Where internet shutdowns create",
    "unexpected masterpieces.",
    "",
    "Home of ancient civilizations,",
    "beautiful poetry,",
    "and now: this game.",
    "",
    "",
    "THE DEVELOPER",
    "Quader",
    "Jobless. Fearless. Focused.",
    "",
    "Former Vibe Coder.",
    "Former Idea Implanter.",
    "Current: Game Developer.",
    "",
    "No resume needed.",
    "The code speaks for itself.",
    "",
    "",
    "THE CODING ENVIRONMENT",
    "A room. A computer. A terminal.",
    "Music playing softly.",
    "No pets. No plants.",
    "Just the sound of keyboard clicks",
    "and Ace of Base on repeat.",
    "",
    "",
    "IN MEMORIAM",
    "The Bugs That Almost Won",
    "The Terminal That Wouldn't Resize",
    "The Hours Lost to Debugging",
    "",
    "Your sacrifice was not in vain.",
    "",
    "",
    "SPECIAL THANKS",
    "",
    "The Internet Shutdown of Iran",
    "Without you, this game wouldn't exist.",
    "",
    "The Python Language",
    "For being beautiful and forgiving.",
    "",
    "The Curses Library",
    "For fighting me until the end.",
    "You lost. Thank you.",
    "",
    "The Keyboard Library",
    "For diagonal movement. Finally.",
    "",
    "",
    "INSPIRED BY",
    "",
    "Blur",
    "For showing what music can be.",
    "",
    "Call of Duty: Black Ops 3",
    "For showing what games can be.",
    "",
    "Two masterpieces.",
    "Two different worlds.",
    "One developer inspired by both.",
    "",
    "",
    "THE CREATIVE PROCESS",
    "",
    "Step 1: Internet goes down.",
    "Step 2: Open terminal.",
    "Step 3: Start typing.",
    "Step 4: Don't stop for a week.",
    "Step 5: Game exists.",
    "",
    "It's that simple.",
    "It's that complicated.",
    "",
    "",
    "FUN FACTS",
    "",
    "This game was built without internet.",
    "No Google. No Stack Overflow.",
    "Every problem solved from memory",
    "and pure logic.",
    "",
    "The responsiveness bug?",
    "Took 3 days to fix.",
    "Worth every second.",
    "",
    "",
    "THE PHILOSOPHY",
    "",
    "A game doesn't need fancy graphics.",
    "It doesn't need multiplayer.",
    "It doesn't need a budget.",
    "",
    "It needs soul.",
    "This game has soul.",
    "",
    "",
    "IRAN",
    "",
    "The Five Star Country.",
    "Rich in history, culture, and resilience.",
    "Where even an internet shutdown",
    "becomes an opportunity.",
    "",
    "This game is proof:",
    "Creativity cannot be blocked.",
    "",
    "",
    "CUTTING ROOM FLOOR",
    "",
    "TCP Multiplayer",
    "So players could explore dungeons",
    "with their friends online.",
    "",
    "Maybe in the sequel.",
    "Maybe when the internet comes back.",
    "",
    "",
    "BEHIND THE SCENES",
    "",
    "Languages: Python 3.13",
    "Libraries: curses, keyboard",
    "Tools: Terminal, Patience, Tea",
    "Days without internet: All of them",
    "Features added: All of them",
    "Bugs fixed: Most of them",
    "Tears shed: Classified",
    "",
    "",
    "WHAT THEY SAID",
    "",
    "\"It works on my machine.\"",
    "  - Quader",
    "",
    "\"The terminal resized.\"",
    "  - Quader (3 days later)",
    "",
    "\"Happy nation, living in a happy nation...\"",
    "  - Ace of Base (on repeat)",
    "",
    "",
    "THE FUTURE",
    "",
    "Dungeon Crawler will grow.",
    "Multiplayer will come.",
    "More dungeons, more enemies,",
    "more adventures await.",
    "",
    "But this first version?",
    "It will always be special.",
    "Born in darkness.",
    "Built without internet.",
    "Made with love.",
    "",
    "",
    "DEDICATED TO",
    "",
    "The people of Iran.",
    "The developers without internet.",
    "The dreamers who create anyway.",
    "",
    "You are the five star people.",
    "",
    "",
    "AND ALSO DEDICATED TO",
    "",
    "Water.",
    "The true king of beverages.",
    "",
    "Tea.",
    "The loyal companion.",
    "",
    "And you.",
    "For playing this game.",
    "For reading this far.",
    "For being part of the story.",
    "",
    "",
    "THANK YOU",
    "",
    "From Quader",
    "From Iran",
    "From a week without internet",
    "",
    "A game was born.",
    "",
    "",
    "Now go explore some dungeons.",
    "",
    "",
    "",
    "",
]
        self.scroll_speed = 0.15  # Seconds between each line scroll
        self.fade_height = 3       # Lines to fade at top and bottom
        
    def init_colors(self):
        """Initialize colors for credits."""
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)      # Normal
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)     # Titles
        curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)       # Names
        curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_BLACK)      # Hidden
        curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)      # Faded
        
    def draw_frame(self, stdscr, h, w, offset):
        """Draw the credits with smooth scrolling."""
        stdscr.clear()
        
        for i, line in enumerate(self.credits_text):
            # Calculate screen position
            screen_y = h - offset + i
            
            # Skip if off screen
            if screen_y < 0 or screen_y >= h:
                continue
            
            # Calculate horizontal center
            x = max(0, (w - len(line)) // 2)
            
            # Determine color based on content
            if line.isupper() and len(line) > 3:
                # Title/header lines
                color = curses.color_pair(2) | curses.A_BOLD
            elif line.startswith("  ") or line.startswith("\t"):
                # Indented lines (names)
                color = curses.color_pair(3)
            else:
                color = curses.color_pair(1)
            
            # Apply fade effect at top and bottom
            if screen_y < self.fade_height:
                # Fading in from bottom
                if screen_y < 0:
                    continue
                if screen_y < 2:
                    color = color | curses.A_DIM
            elif screen_y >= h - self.fade_height:
                # Fading out at top
                if screen_y >= h - 1:
                    continue
                if screen_y >= h - 3:
                    color = color | curses.A_DIM
            
            # Draw the line
            try:
                if x + len(line) <= w:
                    stdscr.addstr(screen_y, x, line, color)
                else:
                    # Truncate if too long
                    stdscr.addstr(screen_y, x, line[:w-x-1], color)
            except curses.error:
                pass
        
        # Draw hint at bottom
        try:
            hint = "Space: Pause | Up/Down: Speed | Enter/Q/Esc: Skip"
            if len(hint) < w:
                stdscr.addstr(h - 1, max(0, w - len(hint) - 1), hint, 
                            curses.color_pair(1) | curses.A_DIM)
        except curses.error:
            pass
        
        stdscr.refresh()
    
    def run(self, stdscr):
        """Run the credits animation."""
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.keypad(True)
        self.init_colors()
        
        h, w = stdscr.getmaxyx()
        
        # Start with text below screen
        offset = 0.0  # Use float for smooth scrolling
        max_offset = len(self.credits_text) + h + 5
        
        last_scroll_time = time.time()
        paused = False
        speed_multiplier = 1.0
        
        while offset < max_offset:
            # Handle resize
            c = stdscr.getch()
            if c == curses.KEY_RESIZE:
                h, w = stdscr.getmaxyx()
            
            # Handle input
            try:
                if keyboard.is_pressed('space'):
                    paused = not paused
                    time.sleep(0.3)  # Debounce
                    last_scroll_time = time.time()
                elif keyboard.is_pressed('up'):
                    speed_multiplier = min(3.0, speed_multiplier + 0.1)
                    last_scroll_time = time.time()
                elif keyboard.is_pressed('down'):
                    speed_multiplier = max(0.1, speed_multiplier - 0.1)
                    last_scroll_time = time.time()
                elif keyboard.is_pressed('enter') or keyboard.is_pressed('q') or \
                     keyboard.is_pressed('b') or keyboard.is_pressed('esc'):
                    # Skip to end with fast animation
                    while offset < max_offset:
                        offset += 2
                        self.draw_frame(stdscr, h, w, int(offset))
                        time.sleep(0.5)
                    time.sleep(0.5)
                    return "back"
            except Exception:
                pass
            
            # Auto-scroll with smooth timing
            current_time = time.time()
            elapsed = current_time - last_scroll_time
            
            if not paused and elapsed >= self.scroll_speed / speed_multiplier:
                # Calculate how many lines to scroll based on elapsed time
                lines_to_scroll = elapsed / (self.scroll_speed / speed_multiplier)
                offset += lines_to_scroll
                last_scroll_time = current_time
            
            # Draw current frame
            self.draw_frame(stdscr, h, w, int(offset))
            
            # Small sleep to prevent CPU spinning
            time.sleep(0.016)  # ~60 FPS
        
        # Final pause at the end
        time.sleep(3)
        
        # Slow fade out
        for fade_step in range(20):
            offset += 0.5
            self.draw_frame(stdscr, h, w, int(offset))
            time.sleep(0.1)
        
        return "back"
def show_menu():
    """Entry point for the menu system."""
    def menu_main(stdscr):
        while True:
            menu = GameMenu()
            result = menu.run(stdscr)
            
            if result == "quit":
                return
            elif result == "new_game":
                try:
                    # Import the game module
                    from src.game import run
                    
                    # End curses temporarily
                    curses.endwin()
                    
                    # Run the game
                    run()
                    
                except SystemExit:
                    # User quit the game normally
                    pass
                except Exception as e:
                    # Show error and wait
                    print(f"Game error: {e}")
                    input("Press Enter to return to menu...")
                finally:
                    # Always restore curses
                    try:
                        stdscr = curses.initscr()
                        curses.curs_set(0)
                        stdscr.nodelay(True)
                        stdscr.keypad(True)
                        
                        # Reinitialize menu colors
                        curses.start_color()
                        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
                        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)
                        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
                        curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_BLACK)
                        curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_BLACK)
                    except Exception:
                        # If curses restoration fails, restart the whole menu
                        pass
            elif result == "options":
                options = OptionsMenu()
                options.run(stdscr)
            elif result == "credits":
                credits = CreditsScreen()
                credits.run(stdscr)
    
    curses.wrapper(menu_main)


if __name__ == "__main__":
    show_menu()