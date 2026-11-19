"""
poc/snake-host/mock_ge.py

Host-side mock 2D Graphics Engine (MockGE).
Provides an abstract drawing surface with pixel framebuffer representation,
clipping boundaries, and frame export capabilities (PPM image / ASCII).

Note: This is a host-side mock for algorithm and rendering validation.
It does NOT claim ABI equivalence with MStar Utopia's internal driver structures.
"""

import os

class MockGE:
    def __init__(self, width=640, height=360, default_bg=0xFF000000):
        self.width = width
        self.height = height
        self.default_bg = default_bg
        self.clip_rect = (0, 0, width, height)
        # Store pixels as a flat list of 32-bit ARGB integers: 0xAARRGGBB
        self.pixels = [default_bg] * (width * height)
        self.op_history = []

    def set_clip_window(self, x, y, w, h):
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(self.width, x + w)
        y2 = min(self.height, y + h)
        self.clip_rect = (x1, y1, max(0, x2 - x1), max(0, y2 - y1))
        self.op_history.append(("SET_CLIP", self.clip_rect))

    def clear(self, color=None):
        c = self.default_bg if color is None else color
        self.pixels = [c] * (self.width * self.height)
        self.op_history.append(("CLEAR", c))

    def draw_rect(self, x, y, w, h, color):
        """Fills a solid rectangle clipped to the active clip window."""
        cx, cy, cw, ch = self.clip_rect
        rx1 = max(x, cx)
        ry1 = max(y, cy)
        rx2 = min(x + w, cx + cw)
        ry2 = min(y + h, cy + ch)

        if rx1 >= rx2 or ry1 >= ry2:
            return # Fully clipped

        for py in range(ry1, ry2):
            row_start = py * self.width
            for px in range(rx1, rx2):
                self.pixels[row_start + px] = color

        self.op_history.append(("DRAW_RECT", x, y, w, h, color))

    def draw_line(self, x1, y1, x2, y2, color):
        """Bresenham's line algorithm with clipping."""
        cx, cy, cw, ch = self.clip_rect
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        cur_x, cur_y = x1, y1
        while True:
            if cx <= cur_x < cx + cw and cy <= cur_y < cy + ch:
                if 0 <= cur_x < self.width and 0 <= cur_y < self.height:
                    self.pixels[cur_y * self.width + cur_x] = color

            if cur_x == x2 and cur_y == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                cur_x += sx
            if e2 < dx:
                err += dx
                cur_y += sy

        self.op_history.append(("DRAW_LINE", x1, y1, x2, y2, color))

    def get_pixel(self, x, y) -> int:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.pixels[y * self.width + x]
        return 0

    def export_ppm(self, filepath: str):
        """Exports the active framebuffer to a standard binary PPM (P6) image."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "wb") as f:
            header = f"P6\n{self.width} {self.height}\n255\n".encode("ascii")
            f.write(header)
            # Write RGB bytes (stripping Alpha)
            rgb_bytes = bytearray(self.width * self.height * 3)
            idx = 0
            for p in self.pixels:
                rgb_bytes[idx] = (p >> 16) & 0xFF     # R
                rgb_bytes[idx + 1] = (p >> 8) & 0xFF  # G
                rgb_bytes[idx + 2] = p & 0xFF         # B
                idx += 3
            f.write(rgb_bytes)

    def render_ascii_subgrid(self, start_x, start_y, w, h, step=1) -> str:
        """Renders an ASCII text visualization of a region of the framebuffer."""
        lines = []
        for y in range(start_y, start_y + h, step):
            row = []
            for x in range(start_x, start_x + w, step):
                p = self.get_pixel(x, y)
                if p == 0xFFFF0000:   # Red (Food)
                    row.append("*")
                elif p == 0xFF00FF00: # Green (Head)
                    row.append("@")
                elif p == 0xFF008800: # Dark Green (Body)
                    row.append("o")
                elif p == 0xFF444444: # Border
                    row.append("#")
                else:
                    row.append(" ")
            lines.append("".join(row))
        return "\n".join(lines)
