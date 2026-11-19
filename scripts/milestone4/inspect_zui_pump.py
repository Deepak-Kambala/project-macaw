with open("Samsung-TV-Homebrew/analysis/decompressed_main.bin", "rb") as f:
    decomp = f.read()

import re

# Find strings that mention ZUI, window, message, or key
zui_strings = [s for s in re.findall(rb"[\x20-\x7e]{5,}", decomp) if any(k in s.lower() for k in [b"zui", b"hwnd", b"u8winprocid", b"msg", b"focus", b"keypad", b"remote"])]
print(f"Total ZUI-related strings: {len(zui_strings)}")
for s in zui_strings[:35]:
    print(" ", s.decode('latin1'))
