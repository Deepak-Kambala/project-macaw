import zlib
import os
import re

FIRMWARE_PATH = "Samsung-TV-Homebrew/firmware/T-MXL0MASC.bin"
OUTPUT_PATH = "Samsung-TV-Homebrew/analysis/decompressed_main.bin"

with open(FIRMWARE_PATH, "rb") as f:
    data = f.read()

# Decompress raw deflate from 0x023880
decomp = zlib.decompress(data[0x023880:], -15)
print(f"Decompressed payload size: {len(decomp)} bytes ({len(decomp)/1024/1024:.2f} MB)")

with open(OUTPUT_PATH, "wb") as f:
    f.write(decomp)

print(f"Saved decompressed payload to {OUTPUT_PATH}")

# Inspect first 256 bytes
print("\nFirst 256 bytes (hex dump):")
for i in range(0, 256, 16):
    line = decomp[i:i+16]
    hex_str = " ".join(f"{b:02x}" for b in line)
    asc_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in line)
    print(f"  0x{i:06x}: {hex_str:<48}  {asc_str}")

# Extract strings
strings = re.findall(rb"[\x20-\x7e]{5,}", decomp)
print(f"\nExtracted {len(strings)} strings from decompressed binary.")

with open("Samsung-TV-Homebrew/analysis/decompressed_strings.txt", "w", encoding="utf-8", errors="ignore") as f:
    for s in strings:
        f.write(s.decode('latin1') + "\n")

# Search for OS, RTOS, kernel, USB, smart, homebrew, loader keywords
keywords = [
    "linux", "u-boot", "ecos", "freertos", "nucleus", "vxworks", "threadx",
    "mstar", "aeon", "macaw", "usb", "upgrade", "firmware", "swu",
    "fat", "ntfs", "mass_storage", "msc", "autorun", "auto_run", "script",
    "sh", "bash", "exec", "system", "app", "application", "launcher", "browser",
    "widget", "smart", "samygo", "game", "hotel", "factory", "debug", "uart"
]

print("\n--- Keyword Scan in Decompressed Binary ---")
for kw in keywords:
    matched = [s.decode('latin1') for s in strings if kw.lower() in s.decode('latin1').lower()]
    if matched:
        print(f"Keyword '{kw}': {len(matched)} matches (e.g. {matched[:3]})")
