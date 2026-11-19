import binascii
import struct

with open("Samsung-TV-Homebrew/firmware/T-MXL0MASC.bin", "rb") as f:
    data = f.read()

# At 0x20014: 79 4e a3 4b -> uint32 is 0x4ba34e79 (LE) or 0x794ea34b (BE)
target_le = 0x4ba34e79
target_be = 0x794ea34b

# At 0x20000:
# [0] = 0x00020080
# [1] = 0x00200000 (2MB)
# [2] = 0x003690a5 (size?)
# [3] = 0x00189125
# Let's test CRC32 of data[0x20000 + 0x80 : 0x20000 + 0x3690a5] or similar slices!

test_ranges = [
    (0x20080, 0x20000 + 0x3690a5),
    (0x20000, 0x20000 + 0x3690a5),
    (0x20020, 0x20000 + 0x3690a5),
    (0x23880, 0x31c776),
    (0x00000, len(data)),
]

for s, e in test_ranges:
    chunk = data[s:e]
    crc = binascii.crc32(chunk) & 0xffffffff
    print(f"Range [{hex(s)} : {hex(e)}] (len {len(chunk)}): CRC = 0x{crc:08x}")
    if crc in (target_le, target_be):
        print(f"MATCH! Range [{hex(s)} : {hex(e)}] matches CRC at 0x20014!")
