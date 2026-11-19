#!/usr/bin/env python3
"""
poc/snake-host/tests/test_mock_ge.py

Automated unit tests for MockGE graphics engine.
Tests clearing, rectangle filling, line drawing, clipping bounds, and PPM export.
"""

import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from mock_ge import MockGE

class TestMockGE(unittest.TestCase):
    def setUp(self):
        self.ge = MockGE(width=100, height=100, default_bg=0xFF000000)

    def test_clear_framebuffer(self):
        self.ge.clear(0xFF112233)
        self.assertEqual(self.ge.get_pixel(0, 0), 0xFF112233)
        self.assertEqual(self.ge.get_pixel(50, 50), 0xFF112233)
        self.assertEqual(self.ge.get_pixel(99, 99), 0xFF112233)

    def test_draw_rect(self):
        self.ge.clear(0xFF000000)
        self.ge.draw_rect(10, 10, 20, 20, 0xFFFF0000)
        # Check inside rectangle
        self.assertEqual(self.ge.get_pixel(10, 10), 0xFFFF0000)
        self.assertEqual(self.ge.get_pixel(29, 29), 0xFFFF0000)
        # Check outside rectangle
        self.assertEqual(self.ge.get_pixel(9, 9), 0xFF000000)
        self.assertEqual(self.ge.get_pixel(30, 30), 0xFF000000)

    def test_clipping_bounds(self):
        self.ge.clear(0xFF000000)
        self.ge.set_clip_window(20, 20, 30, 30) # Clip rect: [20..50, 20..50]
        # Draw rect from (10, 10) with size (50, 50) -> should only fill inside clip rect
        self.ge.draw_rect(10, 10, 50, 50, 0xFF00FF00)
        # Inside clip: (25, 25)
        self.assertEqual(self.ge.get_pixel(25, 25), 0xFF00FF00)
        # Outside clip: (15, 15) should be black
        self.assertEqual(self.ge.get_pixel(15, 15), 0xFF000000)

    def test_draw_line(self):
        self.ge.clear(0xFF000000)
        self.ge.draw_line(0, 0, 10, 0, 0xFFFFFFFF) # Horizontal line y=0, x=0..10
        for x in range(11):
            self.assertEqual(self.ge.get_pixel(x, 0), 0xFFFFFFFF)
        self.assertEqual(self.ge.get_pixel(0, 1), 0xFF000000)

    def test_export_ppm(self):
        test_path = "/tmp/test_export.ppm"
        self.ge.clear(0xFF55AAFF)
        self.ge.export_ppm(test_path)
        self.assertTrue(os.path.exists(test_path))
        self.assertEqual(os.path.getsize(test_path), len("P6\n100 100\n255\n") + 100 * 100 * 3)
        os.remove(test_path)

if __name__ == "__main__":
    unittest.main()
