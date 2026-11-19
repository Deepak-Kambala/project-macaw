FIRMWARE_PATH = "Samsung-TV-Homebrew/firmware/T-MXL0MASC.bin"

with open(FIRMWARE_PATH, "rb") as f:
    data = f.read()

# Let's inspect 0x20000 to 0x22000 in detail
chunk = data[0x20000:0x22000]

print("--- Scanning non-zero 16-byte lines in 0x20000..0x22000 ---")
for offset in range(0x20000, 0x22000, 16):
    line = data[offset:offset+16]
    if any(b != 0 for b in line):
        hex_str = " ".join(f"{b:02x}" for b in line)
        ascii_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in line)
        print(f"0x{offset:06x}: {hex_str} | {ascii_str}")
