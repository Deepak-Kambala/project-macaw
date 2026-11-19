import struct

FIRMWARE_PATH = "Samsung-TV-Homebrew/firmware/T-MXL0MASC.bin"

with open(FIRMWARE_PATH, "rb") as f:
    data = f.read()

# Let's inspect the chunk at 0x20000
# 020000: 80 00 02 00 00 00 20 00 a5 90 36 00 25 91 18 00
# 020010: 00 00 00 00 79 4e a3 4b 00 00 00 00 00 00 00 00
# Let's unpack these values
# 80 00 02 00 -> 0x00020080 ? or 0x80000200?
# Notice 0x020180 is where the code starts!
# Let's check little endian vs big endian unpack:
w1_le = struct.unpack("<IIII", data[0x20000:0x20010])
w1_be = struct.unpack(">IIII", data[0x20000:0x20010])
print(f"0x20000 Little-Endian: {[hex(x) for x in w1_le]}")
print(f"0x20000 Big-Endian:    {[hex(x) for x in w1_be]}")

# Look at 0x21180:
# 78 56 aa 55 00 00 00 00 00 00 00 00 b9 14 00 00
# 10 4c 02 00 01 00 01 00 01 00 01 00 62 08 54 2d
# 4d 58 4c 30 4d 41 53 43 2d 31 30 34 30 2e 30 00
w2_le = struct.unpack("<IIII", data[0x21180:0x21190])
print(f"\n0x21180 Little-Endian: {[hex(x) for x in w2_le]}")
print("String at 0x2119e:", data[0x2119e:0x211b0])

# Notice 0x55aa5678 (magic)!
# 0xb9140000? or 0x000014b9 (5305)?
# What about 0x024c10?
# What about 0x1690a5? (at 0x211ca: be ad de a5 90 16 00)
# Notice 0xdeadbe.. and then a5 90 16 00 -> 0x001690a5 ?
# Wait! Let's check 0x20008: a5 90 36 00 -> 0x003690a5 !
# Wait! 0x3690a5 + something?
# File size is 0x3ac1e4 (3850724)!
# What is 0x3ac1e4 - 0x3690a5? 0x4313f!
