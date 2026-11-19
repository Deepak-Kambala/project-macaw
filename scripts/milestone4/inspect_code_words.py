import struct

with open("Samsung-TV-Homebrew/analysis/decompressed_main.bin", "rb") as f:
    decomp = f.read()

# Let's inspect the first 128 bytes of decompressed_main.bin
# Hex dump:
# 0x000000: 0f 4d 00 40 63 53 c0 c0 0a 61 fc c6 85 04 8c 66
# 0x000010: c0 e0 0a 41 ec 87 7e 22 0d 41 02 0d 21 06 9c 28
# Let's check 32-bit big-endian words vs little-endian words
print("First 16 words (Big Endian):")
for i in range(0, 64, 4):
    w_be = struct.unpack(">I", decomp[i:i+4])[0]
    op = (w_be >> 26) & 0x3f
    print(f"  [{i:04x}]: {decomp[i:i+4].hex(' ')} (BE 0x{w_be:08x}) op=0x{op:02x}")

print("\nFirst 16 words (Little Endian):")
for i in range(0, 64, 4):
    w_le = struct.unpack("<I", decomp[i:i+4])[0]
    op = (w_le >> 26) & 0x3f
    print(f"  [{i:04x}]: {decomp[i:i+4].hex(' ')} (LE 0x{w_le:08x}) op=0x{op:02x}")
