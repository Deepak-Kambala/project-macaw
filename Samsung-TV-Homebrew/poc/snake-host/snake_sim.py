#!/usr/bin/env python3
"""
poc/snake-host/snake_sim.py

Project Macaw — Milestone 5
Host-Side Snake Proof of Concept & Graphics Engine Simulator.

Architecture:
  - AbstractGE: Hardware graphics abstraction simulating MStar Utopia GE APIs
                (MDrv_GE_SetDstBuffer, MDrv_GE_FillRect, MDrv_GE_DrawLine).
  - SnakeGame: Pure game logic decoupled from hardware rendering.
  - RemoteInput: Maps TV keycode enums (KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_ENTER).
  - Comprehensive Unit Test Suite covering all 8 validation criteria.
"""

import sys
import os
import random

# Remote Control Keycode Enums (matching MStar ZUI key definitions)
KEY_UP = 0x01
KEY_DOWN = 0x02
KEY_LEFT = 0x03
KEY_RIGHT = 0x04
KEY_ENTER = 0x05
KEY_EXIT = 0x06

# Colors (32-bit ARGB8888)
COLOR_BLACK = 0xFF000000
COLOR_GREEN = 0xFF00FF00
COLOR_DARKGREEN = 0xFF008800
COLOR_RED = 0xFFFF0000
COLOR_WHITE = 0xFFFFFFFF
COLOR_BORDER = 0xFF444444

class AbstractGE:
    """
    Simulates the MStar Utopia 2D Graphics Engine (GE) hardware block.
    Records rendering operations and maintains a virtual framebuffer.
    """
    def __init__(self, width=1280, height=720):
        self.width = width
        self.height = height
        self.buffer_addr = None
        self.pitch = None
        self.bpp = None
        self.command_log = []
        self.virtual_fb = {} # (x, y) -> color

    def MDrv_GE_SetDstBuffer(self, u32Addr, u32Pitch, u16Width, u16Height, u8Format=0):
        """Simulates MDrv_GE_SetDstBuffer(GE_DstBuffer *pBuf)"""
        self.buffer_addr = u32Addr
        self.pitch = u32Pitch
        self.width = u16Width
        self.height = u16Height
        self.bpp = 4 # ARGB8888
        self.command_log.append(f"SetDstBuffer(addr=0x{u32Addr:08x}, pitch={u32Pitch}, {u16Width}x{u16Height})")
        return 0 # GE_OK

    def MDrv_GE_FillRect(self, x, y, width, height, color):
        """Simulates MDrv_GE_FillRect(GE_Rect *pRect, MS_U32 u32Color)"""
        # Boundary validation matching MStar driver checks
        if x < 0 or y < 0 or x + width > self.width or y + height > self.height:
            self.command_log.append(f"FillRect_FAIL_BOUNDS(x={x}, y={y}, w={width}, h={height})")
            return 1 # GE_FAIL

        self.command_log.append(f"FillRect(x={x}, y={y}, w={width}, h={height}, color=0x{color:08x})")
        for dy in range(height):
            for dx in range(width):
                self.virtual_fb[(x + dx, y + dy)] = color
        return 0 # GE_OK

    def MDrv_GE_DrawLine(self, x1, y1, x2, y2, color):
        """Simulates MDrv_GE_DrawLine(GE_Point *p1, GE_Point *p2, MS_U32 u32Color)"""
        self.command_log.append(f"DrawLine(({x1},{y1}) -> ({x2},{y2}), color=0x{color:08x})")
        return 0 # GE_OK

    def clear_log(self):
        self.command_log.clear()

class SnakeGame:
    """
    Decoupled Snake Game Engine designed for integration into MStar ZUI.
    Grid size: 32x18 cells (matching 1280x720 display with 30x30px cells and 160px borders).
    """
    DIR_UP = (0, -1)
    DIR_DOWN = (0, 1)
    DIR_LEFT = (-1, 0)
    DIR_RIGHT = (1, 0)

    OPPOSITE_DIR = {
        DIR_UP: DIR_DOWN,
        DIR_DOWN: DIR_UP,
        DIR_LEFT: DIR_RIGHT,
        DIR_RIGHT: DIR_LEFT,
    }

    def __init__(self, ge: AbstractGE, grid_w=32, grid_h=18, cell_size=20, offset_x=320, offset_y=180):
        self.ge = ge
        self.grid_w = grid_w
        self.grid_h = grid_h
        self.cell_size = cell_size
        self.offset_x = offset_x
        self.offset_y = offset_y
        
        self.reset()

    def reset(self):
        mid_x = self.grid_w // 2
        mid_y = self.grid_h // 2
        # Initial snake: 3 segments moving right
        self.snake = [(mid_x, mid_y), (mid_x - 1, mid_y), (mid_x - 2, mid_y)]
        self.direction = self.DIR_RIGHT
        self.next_direction = self.DIR_RIGHT
        self.score = 0
        self.game_over = False
        self.paused = False
        self.food = None
        self._spawn_food()

    def _spawn_food(self):
        available = [(x, y) for x in range(self.grid_w) for y in range(self.grid_h) if (x, y) not in self.snake]
        if available:
            self.food = random.choice(available)
        else:
            self.food = (-1, -1) # Win condition

    def handle_input(self, keycode):
        """Processes remote control D-pad and action events."""
        if self.game_over:
            if keycode == KEY_ENTER:
                self.reset()
                return True
            return False

        if keycode == KEY_UP and self.direction != self.DIR_DOWN:
            self.next_direction = self.DIR_UP
            return True
        elif keycode == KEY_DOWN and self.direction != self.DIR_UP:
            self.next_direction = self.DIR_DOWN
            return True
        elif keycode == KEY_LEFT and self.direction != self.DIR_RIGHT:
            self.next_direction = self.DIR_LEFT
            return True
        elif keycode == KEY_RIGHT and self.direction != self.DIR_LEFT:
            self.next_direction = self.DIR_RIGHT
            return True
        elif keycode == KEY_ENTER:
            self.paused = not self.paused
            return True
        return False

    def step(self):
        """Timer tick: updates game state and generates GE rendering calls."""
        if self.game_over or self.paused:
            return False

        self.direction = self.next_direction
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        # 1. Wall collision check
        if not (0 <= new_head[0] < self.grid_w and 0 <= new_head[1] < self.grid_h):
            self.game_over = True
            return False

        # 2. Self collision check
        if new_head in self.snake[:-1]:
            self.game_over = True
            return False

        # 3. Movement & growth
        self.snake.insert(0, new_head)
        if new_head == self.food:
            self.score += 10
            self._spawn_food()
        else:
            # Remove tail if not eating
            self.snake.pop()

        return True

    def render(self):
        """Issues hardware accelerated GE draw calls to update display."""
        # 1. Clear background playfield
        px_w = self.grid_w * self.cell_size
        px_h = self.grid_h * self.cell_size
        self.ge.MDrv_GE_FillRect(self.offset_x, self.offset_y, px_w, px_h, COLOR_BLACK)

        # 2. Draw border
        self.ge.MDrv_GE_DrawLine(self.offset_x, self.offset_y, self.offset_x + px_w, self.offset_y, COLOR_BORDER)
        self.ge.MDrv_GE_DrawLine(self.offset_x, self.offset_y + px_h, self.offset_x + px_w, self.offset_y + px_h, COLOR_BORDER)
        self.ge.MDrv_GE_DrawLine(self.offset_x, self.offset_y, self.offset_x, self.offset_y + px_h, COLOR_BORDER)
        self.ge.MDrv_GE_DrawLine(self.offset_x + px_w, self.offset_y, self.offset_x + px_w, self.offset_y + px_h, COLOR_BORDER)

        # 3. Draw food
        if self.food and self.food != (-1, -1):
            fx = self.offset_x + self.food[0] * self.cell_size
            fy = self.offset_y + self.food[1] * self.cell_size
            self.ge.MDrv_GE_FillRect(fx + 2, fy + 2, self.cell_size - 4, self.cell_size - 4, COLOR_RED)

        # 4. Draw snake segments
        for i, (sx, sy) in enumerate(self.snake):
            color = COLOR_GREEN if i == 0 else COLOR_DARKGREEN
            bx = self.offset_x + sx * self.cell_size
            by = self.offset_y + sy * self.cell_size
            self.ge.MDrv_GE_FillRect(bx + 1, by + 1, self.cell_size - 2, self.cell_size - 2, color)

def run_tests():
    """Runs tests for all 8 mandatory criteria and returns report."""
    results = []
    
    ge = AbstractGE(1280, 720)
    ge.MDrv_GE_SetDstBuffer(0x8C000000, 1280 * 4, 1280, 720)
    
    # Criterion 1: Initial Game State
    game = SnakeGame(ge, grid_w=20, grid_h=20)
    c1 = (len(game.snake) == 3 and not game.game_over and game.score == 0 and game.direction == game.DIR_RIGHT)
    results.append(("Criterion 1: Initial Game State Setup", c1, f"Snake len={len(game.snake)}, Over={game.game_over}, Score={game.score}"))

    # Criterion 2: Direction Changes
    game.handle_input(KEY_UP)
    game.step()
    c2 = (game.direction == game.DIR_UP and game.snake[0][1] < game.snake[1][1])
    results.append(("Criterion 2: Valid Direction Changes", c2, f"Dir={game.direction}, Head={game.snake[0]}"))

    # Criterion 3: Rejection of Immediate Reverse Movement
    game.handle_input(KEY_DOWN) # Immediate reverse should be rejected
    game.step()
    c3 = (game.direction == game.DIR_UP) # Still moving UP
    results.append(("Criterion 3: Rejection of Immediate 180-deg Reverse", c3, f"Dir after illegal DOWN={game.direction}"))

    # Criterion 4: Food Consumption
    game.food = (game.snake[0][0], game.snake[0][1] - 1) # Place food directly ahead
    old_score = game.score
    game.step() # Move onto food
    c4 = (game.score == old_score + 10)
    results.append(("Criterion 4: Food Consumption & Score Increment", c4, f"Score changed from {old_score} to {game.score}"))

    # Criterion 5: Snake Growth
    # After eating, length should have increased to 4
    c5 = (len(game.snake) == 4)
    results.append(("Criterion 5: Snake Body Growth", c5, f"Snake length after eating = {len(game.snake)}"))

    # Criterion 6: Wall Collision
    # Steer towards wall and verify game over
    wall_game = SnakeGame(ge, grid_w=10, grid_h=10)
    # Move right to wall x=9
    for _ in range(10):
        wall_game.step()
    c6 = (wall_game.game_over is True)
    results.append(("Criterion 6: Wall Collision Detection", c6, f"Wall collision Game Over={wall_game.game_over}"))

    # Criterion 7: Self Collision
    self_game = SnakeGame(ge, grid_w=10, grid_h=10)
    # Grow snake so it can hit itself (length >= 5)
    self_game.snake = [(5, 5), (5, 6), (4, 6), (4, 5), (4, 4)]
    self_game.direction = self_game.DIR_DOWN
    self_game.handle_input(KEY_LEFT)
    self_game.step() # Head moves into body at (4, 5)
    c7 = (self_game.game_over is True)
    results.append(("Criterion 7: Self Collision Detection", c7, f"Self collision Game Over={self_game.game_over}"))

    # Criterion 8: Timer-Driven Movement & Rendering Command Generation
    ge.clear_log()
    render_game = SnakeGame(ge, grid_w=10, grid_h=10)
    render_game.step()
    render_game.render()
    fill_calls = [cmd for cmd in ge.command_log if cmd.startswith("FillRect")]
    draw_calls = [cmd for cmd in ge.command_log if cmd.startswith("DrawLine")]
    c8 = (len(fill_calls) >= 5 and len(draw_calls) == 4) # 1 background + 1 food + 3 snake segments + 4 borders
    results.append(("Criterion 8: Timer Tick & GE Rendering Commands", c8, f"GE FillRect calls={len(fill_calls)}, DrawLine calls={len(draw_calls)}"))

    return results

def main():
    print("==================================================================")
    print(" Project Macaw: Host-Side Snake PoC & Graphics Simulator         ")
    print("==================================================================")
    
    results = run_tests()
    all_passed = True
    output_lines = []
    
    print("\n--- Test Suite Execution Results ---")
    for name, passed, details in results:
        status_str = "[PASS]" if passed else "[FAIL]"
        if not passed: all_passed = False
        line = f"  {status_str} {name:50s} | {details}"
        print(line)
        output_lines.append(line)
        
    summary = f"\nOverall Result: {'ALL 8 CRITERIA PASSED' if all_passed else 'SOME TESTS FAILED'}\n"
    print(summary)
    output_lines.append(summary)
    
    # Save log to poc/snake-host/test_results.txt
    log_path = "poc/snake-host/test_results.txt"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "w") as f:
        f.write("\n".join(output_lines))
    print(f"Test results saved to {log_path}")

if __name__ == "__main__":
    main()
