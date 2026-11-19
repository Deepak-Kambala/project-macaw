import struct

with open("Samsung-TV-Homebrew/firmware/T-MXL0MASC.bin", "rb") as f:
    bootloader = f.read(0x23880)

# In zlib inflate, z_stream structure has:
# next_in, avail_in, total_in, next_out, avail_out, total_out
# next_out is the destination buffer pointer in RAM!
# Let's search bootloader for 32-bit addresses in KSEG0 (0x80000000 - 0x82000000)
# or uncached (0xa0000000)

kseg0_addrs = []
for i in range(0, len(bootloader)-4, 2):
    w_be = struct.unpack(">I", bootloader[i:i+4])[0]
    w_le = struct.unpack("<I", bootloader[i:i+4])[0]
    if 0x80000000 <= w_be <= 0x82000000:
        kseg0_addrs.append((i, "BE", hex(w_be)))
    if 0x80000000 <= w_le <= 0x82000000:
        kseg0_addrs.append((i, "LE", hex(w_le)))

print(f"Total KSEG0 pointers found in bootloader: {len(kseg0_addrs)}")
# Group by address
from collections import Counter
c = Counter([addr for _, _, addr in kseg0_addrs])
for addr, count in c.most_common(15):
    print(f"  {addr}: {count} occurrences")
