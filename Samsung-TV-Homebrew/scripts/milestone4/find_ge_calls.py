import struct

with open("Samsung-TV-Homebrew/analysis/decompressed_main.bin", "rb") as f:
    decomp = f.read()

# String "MDrv_GE_FillRect" is at offset 0x17bd3e
str_off = 0x17bd3e
print(f"String 'MDrv_GE_FillRect' is at offset 0x{str_off:06x} ({str_off})")

# Look at 64 bytes around str_off
print("String bytes:", decomp[str_off:str_off+32])

# In MStar systems, decomp is loaded at KSEG0: 0x80000000 + offset (or similar base)
# Let's search for references to 0x17bd3e or 0x8017bd3e or 0xa017bd3e
# Also check if it's referenced via 16-bit high/low immediates:
# hi = (addr + 0x8000) >> 16
# lo = addr & 0xffff

for base in [0x80000000, 0x00000000, 0xa0000000, 0x80020000]:
    vaddr = base + str_off
    hi = (vaddr >> 16) & 0xffff
    lo = vaddr & 0xffff
    
    # Check 32-bit word
    le32 = struct.pack("<I", vaddr)
    be32 = struct.pack(">I", vaddr)
    
    hits_le = [hex(i) for i in range(0, len(decomp)-4, 2) if decomp[i:i+4] == le32]
    hits_be = [hex(i) for i in range(0, len(decomp)-4, 2) if decomp[i:i+4] == be32]
    
    if hits_le or hits_be:
        print(f"Base 0x{base:08x} (vaddr 0x{vaddr:08x}): LE hits {hits_le}, BE hits {hits_be}")

    # Check for immediate pairs in instructions
    # In OpenRISC: l.movhi rX, hi; l.ori rX, rX, lo
    # In Aeon R2: let's check byte sequences containing hi and lo
    hi_be = struct.pack(">H", hi)
    lo_be = struct.pack(">H", lo)
    hi_le = struct.pack("<H", hi)
    lo_le = struct.pack("<H", lo)
