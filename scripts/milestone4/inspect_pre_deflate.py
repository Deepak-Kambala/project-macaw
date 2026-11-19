with open("Samsung-TV-Homebrew/firmware/T-MXL0MASC.bin", "rb") as f:
    f.seek(0x023700)
    data = f.read(0x180)

print("=== Bytes before 0x023880 in T-MXL0MASC.bin ===")
for i in range(0, len(data), 16):
    chunk = data[i:i+16]
    hex_str = " ".join(f"{b:02x}" for b in chunk)
    asc_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
    print(f"  0x{0x023700+i:06x}: {hex_str} | {asc_str}")
