#!/usr/bin/env python3
"""
poc/snake-host/integration_demo.py

Project Macaw — Milestone 6: Host-Side Snake & Mock GE Integration Demo.

Demonstrates end-to-end integration:
  1. Snake Game Logic running on host.
  2. Abstract Graphics Interface translating game state to GE drawing calls.
  3. MockGE executing drawing primitives into a host framebuffer.
  4. Framebuffer exported to PPM image and rendered as ASCII visualization.
  5. Cross-checks with Aeon R2 emulator scoring subroutine.
"""

import sys
import os

sys.path.append(os.path.dirname(__file__))
from mock_ge import MockGE
from snake_sim import (
    SnakeGame, KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_ENTER,
    COLOR_BLACK, COLOR_GREEN, COLOR_DARKGREEN, COLOR_RED, COLOR_BORDER
)

# Also import emulator runner for hybrid verification
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../aeon-r2-emulator')))
from runner import EmulatorRunner

class MockGEAdapter:
    """Adapts MockGE to the AbstractGE interface expected by SnakeGame."""
    def __init__(self, mock_ge: MockGE):
        self.mock = mock_ge

    def MDrv_GE_SetDstBuffer(self, u32Addr, u32Pitch, u16Width, u16Height, u8Format=0):
        self.mock.clear(COLOR_BLACK)
        return 0

    def MDrv_GE_FillRect(self, x, y, width, height, color):
        self.mock.draw_rect(x, y, width, height, color)
        return 0

    def MDrv_GE_DrawLine(self, x1, y1, x2, y2, color):
        self.mock.draw_line(x1, y1, x2, y2, color)
        return 0

def run_integration_demo():
    print("==================================================================")
    print(" Project Macaw: Snake & Mock GE End-to-End Integration Demo       ")
    print("==================================================================")

    # 1. Initialize MockGE (640x360 for crisp rendering)
    ge = MockGE(width=640, height=360)
    adapter = MockGEAdapter(ge)

    # 2. Initialize SnakeGame (20x15 cells, 16px cell size, centered)
    # Total playfield = 320x240 pixels. Offset = (160, 60)
    cell_size = 16
    grid_w = 20
    grid_h = 15
    offset_x = 160
    offset_y = 60

    game = SnakeGame(adapter, grid_w=grid_w, grid_h=grid_h, cell_size=cell_size, offset_x=offset_x, offset_y=offset_y)

    print("\n--- Phase 1: Initial Game State Setup ---")
    game.render()
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../analysis/milestone6'))
    os.makedirs(output_dir, exist_ok=True)

    ppm_frame0 = os.path.join(output_dir, "snake_frame0_init.ppm")
    ge.export_ppm(ppm_frame0)
    print(f"Initial frame rendered and exported to:\n  {ppm_frame0}")
    print("\nASCII Visualization (Playfield Region):")
    ascii_view = ge.render_ascii_subgrid(offset_x, offset_y, grid_w * cell_size, grid_h * cell_size, step=cell_size)
    print(ascii_view)

    print("\n--- Phase 2: Simulating 5 Movement Ticks & Steering ---")
    moves = [
        ("Step 1 (Continue Right)", None),
        ("Step 2 (Steer UP)", KEY_UP),
        ("Step 3 (Continue UP)", None),
        ("Step 4 (Steer LEFT)", KEY_LEFT),
        ("Step 5 (Continue LEFT)", None)
    ]

    for desc, key in moves:
        if key:
            game.handle_input(key)
        game.step()
        game.render()
        print(f"  {desc:30s} | Head={game.snake[0]}, Len={len(game.snake)}, Score={game.score}")

    ppm_frame5 = os.path.join(output_dir, "snake_frame5_moved.ppm")
    ge.export_ppm(ppm_frame5)
    print(f"\nFinal frame exported to:\n  {ppm_frame5}")
    print("\nASCII Visualization after movement:")
    ascii_view_moved = ge.render_ascii_subgrid(offset_x, offset_y, grid_w * cell_size, grid_h * cell_size, step=cell_size)
    print(ascii_view_moved)

    print("\n--- Phase 3: Cross-Checking Score with Aeon R2 Emulator ---")
    # Execute the 31-byte score calculator program in the Aeon R2 emulator
    runner = EmulatorRunner()
    code = bytes([
        0xFC, 0x21, 0xFF, 0xF0, 0x0D, 0x21, 0x0C, 0x0D, 0x41, 0x08,
        0x99, 0x4A, 0x8C, 0x64, 0x8C, 0x6A, 0x1C, 0x63, 0x05,
        0x0D, 0x41, 0x0A, 0x0D, 0x21, 0x0E, 0xFC, 0x21, 0x00, 0x10, 0x85, 0x29
    ])
    runner.load_program(code, 0x0000)
    # Pass snake head_x and food_x as arguments to emulator
    head_x, head_y = game.snake[0]
    food_x, food_y = game.food if game.food else (0, 0)
    runner.cpu.regs.write(3, head_x)
    runner.cpu.regs.write(4, food_x)
    res = runner.run(max_steps=50)

    print(f"Emulator Arguments: r3 (head_x)={head_x}, r4 (food_x)={food_x}")
    print(f"Emulator Executed: {res['steps_executed']} instructions, Halted: {res['halted']}")
    print(f"Emulator Computed Value in r3: {res['registers']['r3']} (Expected: {head_x + food_x + 15})")

    print("\n--- Integration Architecture Boundaries ---")
    print("  1. Snake Game Logic:         RUNNING ON HOST (Python)")
    print("  2. Graphics Acceleration:    RUNNING ON HOST (MockGE virtual framebuffer)")
    print("  3. Aeon R2 Instructions:     EXECUTED IN HOST EMULATOR (cpu.py)")
    print("  4. Actual TV Firmware:       READ-ONLY / UNMODIFIED (Physical flash untouched)")

    print("\nIntegration Demo Completed Successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(run_integration_demo())
