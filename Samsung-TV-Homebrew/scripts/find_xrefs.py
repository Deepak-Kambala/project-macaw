import struct

with open("Samsung-TV-Homebrew/analysis/decompressed_main.bin", "rb") as f:
    decomp = f.read()

# Address of "T-MXL0MASC.BIN" in decomp is 0x15c4e0
# Let's search for references to 0x15c4e0 or its offset in RAM.
# Where is decomp loaded in RAM?
# Earlier we saw in decompressed binary:
# [MST Macaw12 Utopia Version[12.1.%d]
# and in bootloader:
# 0x020000 has 80 00 02 00 -> 0x00020080 or 0x80020000?
# In MStar Aeon / OpenRISC:
# KSEG0 is 0x80000000 (cached) or 0xA0000000 (uncached) or 0x00000000.
# Let's search for 0x15c4e0 or (base + 0x15c4e0) across 32-bit words.

for base in [0x00000000, 0x80000000, 0xa0000000, 0x00020000, 0x80020000]:
    target = base + 0x15c4e0
    target_bytes_be = struct.pack(">I", target)
    target_bytes_le = struct.pack("<I", target)
    
    hits_be = [i for i in range(0, len(decomp)-4, 4) if decomp[i:i+4] == target_bytes_be]
    hits_le = [i for i in range(0, len(decomp)-4, 4) if decomp[i:i+4] == target_bytes_le]
    
    if hits_be:
        print(f"Base {hex(base)}: Big-Endian hits at {[hex(h) for h in hits_be]}")
    if hits_le:
        print(f"Base {hex(base)}: Little-Endian hits at {[hex(h) for h in hits_le]}")
