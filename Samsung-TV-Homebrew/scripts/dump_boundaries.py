FIRMWARE_PATH = "Samsung-TV-Homebrew/firmware/T-MXL0MASC.bin"

with open(FIRMWARE_PATH, "rb") as f:
    data = f.read()

def dump_region(offset, length):
    print(f"\n--- Dump from 0x{offset:06x} ({length} bytes) ---")
    chunk = data[offset:offset + length]
    for i in range(0, len(chunk), 16):
        line = chunk[i:i+16]
        hex_str = " ".join(f"{b:02x}" for b in line)
        ascii_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in line)
        print(f"  {offset + i:06x}: {hex_str:<48}  {ascii_str}")

# Dump 0x0000 to 0x0200
dump_region(0x0000, 0x180)
# Dump 0xffd0 to 0x10050 (around 64KB boundary)
dump_region(0xffd0, 0x80)
# Dump 0x1ffd0 to 0x20050 (around 128KB boundary)
dump_region(0x1ffd0, 0x80)
# Dump 0x20000 to 0x20200
dump_region(0x20000, 0x200)
# Dump 0x21150 to 0x21300 (around T-MXL0MASC)
dump_region(0x21150, 0x100)
