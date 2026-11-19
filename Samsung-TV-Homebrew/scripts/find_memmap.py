import re
import struct

with open("Samsung-TV-Homebrew/analysis/decompressed_main.bin", "rb") as f:
    decomp = f.read()

# Let's search for strings containing base addresses or memory mappings
matches = [m.start() for m in re.finditer(rb"(?:BaseAdd|BaseAddr|MemMap|DRAM|DDR|heap|SRAM|RIU)[^\x00\r\n]{5,100}", decomp)]
print(f"Found {len(matches)} memory-related diagnostic strings:")
for m in matches[:30]:
    s = decomp[m:m+120].split(b"\x00")[0]
    pr = "".join(chr(b) if 32 <= b <= 126 else " " for b in s)
    print(" ", pr)
