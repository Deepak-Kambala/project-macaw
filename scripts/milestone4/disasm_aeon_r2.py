with open("Samsung-TV-Homebrew/firmware/T-MXL0MASC.bin", "rb") as f:
    data = f.read()

vector_handler = data[0x020280:0x020350]

print("=== Vector Handler at 0x020280 (Raw Dump) ===")
for i in range(0, len(vector_handler), 16):
    chunk = vector_handler[i:i+16]
    hex_str = " ".join(f"{b:02x}" for b in chunk)
    print(f"  {0x020280+i:06x}: {hex_str}")

print("\n=== Parsing 24-bit (3-byte) Store Instructions ===")
# Starting at 0x020284:
# 0c 61 0c -> offset 0x0c, base r1, reg r3
# 0c 81 10 -> offset 0x10, base r1, reg r4
# ...
stores = vector_handler[4:4 + 29*3]
for idx in range(0, len(stores), 3):
    inst = stores[idx:idx+3]
    b0, b1, b2 = inst
    # Let's inspect the bitfields
    # b2 is offset: 0x0c, 0x10, ...
    # b1: high nibble (6, 8, a, c, e, 0, 2, 4...) low nibble is 1 (r1)
    # b0: 0x0c, 0x0d, 0x0e, 0x0f
    reg_id = (b0 & 0x03) * 8 + (b1 >> 5) # let's check mapping
    print(f"  +{idx+4:02x}: {inst.hex(' ')} | b0=0x{b0:02x} b1=0x{b1:02x} b2=0x{b2:02x} (offset={b2})")
