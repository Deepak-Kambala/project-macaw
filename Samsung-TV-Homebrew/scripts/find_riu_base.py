import struct
import re

with open("Samsung-TV-Homebrew/analysis/decompressed_main.bin", "rb") as f:
    decomp = f.read()

# Let's search for typical MStar RIU base addresses:
# 0x1f000000, 0x1f200000, 0xbf000000, 0xbf200000, 0xa0000000, 0x80000000
for addr in [0x1f000000, 0x1f200000, 0xbf000000, 0xbf200000, 0x80000000, 0xa0000000, 0x40000000]:
    b_le = struct.pack("<I", addr)
    b_be = struct.pack(">I", addr)
    hits_le = [hex(m.start()) for m in re.finditer(re.escape(b_le), decomp)]
    hits_be = [hex(m.start()) for m in re.finditer(re.escape(b_be), decomp)]
    print(f"Address 0x{addr:08x}: LE hits = {len(hits_le)} {hits_le[:3]}, BE hits = {len(hits_be)} {hits_be[:3]}")

# Also check OpenRISC instructions: l.movhi rX, 0x1f20 or 0xbf20
# In OpenRISC: l.movhi opcode is 0x06 (bits 31:26), bits 25:21 are rD, bits 15:0 are immediate
# Opcode: (0x06 << 26) | (rD << 21) | imm16
# Let's search for movhi with immediate 0x1f00, 0x1f20, 0xbf00, 0xbf20
for imm in [0x1f00, 0x1f20, 0xbf00, 0xbf20, 0x8000, 0xa000]:
    count_be = 0
    count_le = 0
    for rD in range(32):
        word_be = struct.pack(">I", (0x06 << 26) | (rD << 21) | imm)
        word_le = struct.pack("<I", (0x06 << 26) | (rD << 21) | imm)
        count_be += decomp.count(word_be)
        count_le += decomp.count(word_le)
    print(f"l.movhi rX, 0x{imm:04x}: BE = {count_be}, LE = {count_le}")
