import binascii
import struct

FIRMWARE_PATH = "Samsung-TV-Homebrew/firmware/T-MXL0MASC.bin"

with open(FIRMWARE_PATH, "rb") as f:
    data = f.read()

total_len = len(data)
print(f"Total file length: {total_len} (0x{total_len:x})")

trailer = data[-32:]
print("Last 32 bytes of file:")
for i in range(0, len(trailer), 16):
    print(" ", trailer[i:i+16].hex(" "))

# Unpack words in the last 16 bytes
last_16 = data[-16:]
# 0b00 beef 0000 0000 0000 3a6f 5510 85b5
w_le = struct.unpack("<IIII", last_16)
w_be = struct.unpack(">IIII", last_16)
print("Last 16 bytes as LE uint32:", [hex(w) for w in w_le])
print("Last 16 bytes as BE uint32:", [hex(w) for w in w_be])

# Let's test standard CRC32 (IEEE 802.3) on data excluding the last 4, 8, 12, 16, 20 bytes
for exclude in range(0, 36, 4):
    sub = data[:-exclude] if exclude > 0 else data
    crc = binascii.crc32(sub) & 0xffffffff
    print(f"CRC32(data[:-{exclude:02d}]): 0x{crc:08x} (LE: {struct.pack('<I', crc).hex(' ')}, BE: {struct.pack('>I', crc).hex(' ')})")

# Also check from 0x10000 or 0x20000 or 0x21180 to end
for start in [0x100, 0x10000, 0x20000, 0x21180]:
    for exclude in [0, 4, 8, 12, 16]:
        sub = data[start:-exclude] if exclude > 0 else data[start:]
        crc = binascii.crc32(sub) & 0xffffffff
        crc_le = struct.pack("<I", crc)
        crc_be = struct.pack(">I", crc)
        if crc_le in data[-64:] or crc_be in data[-64:]:
            print(f"MATCH FOUND! Start {hex(start)}, exclude {exclude}: CRC32 = 0x{crc:08x}")
