import os
import re

FIRMWARE_PATH = "Samsung-TV-Homebrew/firmware/T-MXL0MASC.bin"

with open(FIRMWARE_PATH, "rb") as f:
    data = f.read()

# Extract all ASCII strings of length >= 4
strings_all = re.findall(rb"[\x20-\x7e]{4,}", data)
print(f"Total ASCII strings found: {len(strings_all)}")

# Save all strings to analysis/strings.txt
os.makedirs("Samsung-TV-Homebrew/analysis", exist_ok=True)
with open("Samsung-TV-Homebrew/analysis/strings.txt", "w", encoding="utf-8", errors="ignore") as f:
    for s in strings_all:
        f.write(s.decode('latin1') + "\n")

# Look at strings specifically in the first 0x30000 bytes
strings_header = re.finditer(rb"[\x20-\x7e]{4,}", data[:0x30000])
print("\n--- Strings in first 0x30000 bytes ---")
for m in strings_header:
    print(f"0x{m.start():06x}: {m.group().decode('latin1')}")

