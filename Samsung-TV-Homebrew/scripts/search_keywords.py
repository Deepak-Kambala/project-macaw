import re

FIRMWARE_PATH = "Samsung-TV-Homebrew/firmware/T-MXL0MASC.bin"

with open(FIRMWARE_PATH, "rb") as f:
    data = f.read()

# Let's search for case-insensitive keywords in strings
keywords = [
    "macaw", "aeon", "mstar", "openrisc", "or1k", "or32", "mxl", "samsung",
    "uboot", "u-boot", "linux", "rtos", "ecos", "freertos", "nucleus",
    "upgrade", "usb", "swu", "image", "bin", "flash", "partition", "fat",
    "chunk", "crc", "compress", "zlib", "deflate", "lzma", "msd", "mst",
    "boot", "version", "t-mxl", "1040"
]

with open("Samsung-TV-Homebrew/analysis/strings.txt", "r", encoding="utf-8", errors="ignore") as f:
    lines = [line.strip() for line in f if line.strip()]

print(f"Total lines in strings.txt: {len(lines)}")

matches = {}
for kw in keywords:
    kw_lower = kw.lower()
    matched = [l for l in lines if kw_lower in l.lower()]
    if matched:
        matches[kw] = matched

for kw, items in matches.items():
    print(f"\n=== Matches for '{kw}' ({len(items)}) ===")
    for item in items[:15]:
        print(f"  {item}")
    if len(items) > 15:
        print(f"  ... and {len(items) - 15} more")

