FIRMWARE_PATH = "Samsung-TV-Homebrew/firmware/T-MXL0MASC.bin"

with open(FIRMWARE_PATH, "rb") as f:
    data = f.read()

def dump(off, sz=64):
    print(f"\n--- Offset 0x{off:x} ({off}) ---")
    chunk = data[off:off+sz]
    for i in range(0, len(chunk), 16):
        line = chunk[i:i+16]
        hex_s = " ".join(f"{b:02x}" for b in line)
        asc_s = "".join(chr(b) if 32 <= b <= 126 else "." for b in line)
        print(f"  0x{off+i:06x}: {hex_s:<48}  {asc_s}")

dump(0x200000, 128)
dump(0x3690a5, 128)
dump(0x3890a5, 128)
dump(0x189125, 128)
