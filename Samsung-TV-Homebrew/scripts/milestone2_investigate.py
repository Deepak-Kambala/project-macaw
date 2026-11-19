import re
import struct

with open("Samsung-TV-Homebrew/analysis/decompressed_main.bin", "rb") as f:
    decomp = f.read()

def search_patterns(patterns, title):
    print(f"\n==================== {title} ====================")
    for p in patterns:
        matches = [m.start() for m in re.finditer(p, decomp, re.IGNORECASE)]
        print(f"\n--- Pattern: {p.decode('latin1', errors='ignore')} ({len(matches)} matches) ---")
        for m in matches[:10]:
            start = max(0, m - 60)
            end = min(len(decomp), m + len(p) + 80)
            sub = decomp[start:end]
            pr = "".join(chr(b) if 32 <= b <= 126 else "\n" for b in sub)
            lines = [l.strip() for l in pr.split("\n") if len(l.strip()) >= 3]
            print(f"  [0x{m:06x}]: " + " | ".join(lines))

# 1. RAM / MIU / Memory Map
search_patterns([b"MIU", b"DRAM", b"DDR", b"heap", b"mmap", b"u32RiuBaseAdd"], "Memory Map & RAM")

# 2. Graphics (GOP, GE, OSD, Canvas, Framebuffer, Blit)
search_patterns([b"GOP", b"MDrv_GE", b"MApi_GOP", b"MDrv_GOP", b"OSD", b"Canvas", b"BitBlt"], "Graphics & Display APIs")

# 3. Remote Control (IR, Keypad, Key code)
search_patterns([b"KEY_", b"MDrv_IR", b"IR_KEY", b"msKeypad", b"u8KeyCode"], "Remote Control & Input")

# 4. Bootloader / Recovery / Fallback
search_patterns([b"recovery", b"fallback", b"backup", b"dual", b"boot_mode", b"emergency", b"force"], "Recovery / Fallback")
