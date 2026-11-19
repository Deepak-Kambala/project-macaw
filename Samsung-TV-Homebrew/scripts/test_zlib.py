import zlib

FIRMWARE_PATH = "Samsung-TV-Homebrew/firmware/T-MXL0MASC.bin"

with open(FIRMWARE_PATH, "rb") as f:
    data = f.read()

# Let's search for zlib headers (0x78 0x01, 0x78 0x9c, 0x78 0xda, 0x78 0x5e, etc.)
# or test raw DEFLATE (wbits = -15) at various offsets, especially around 0x20000 to 0x30000
print("Testing zlib and raw deflate...")

# Let's check from 0x20000 to 0x35000 in 1-byte or 4-byte steps
found = []
for off in range(0x20000, 0x40000):
    # Try zlib (wbits=15)
    try:
        decomp = zlib.decompress(data[off:off+2000000], 15)
        if len(decomp) > 1000:
            found.append(("zlib", off, len(decomp)))
            print(f"ZLIB stream at 0x{off:06x}: decompressed {len(decomp)} bytes")
            break
    except Exception:
        pass

    # Try raw deflate (wbits=-15)
    try:
        decomp = zlib.decompress(data[off:off+2000000], -15)
        if len(decomp) > 1000:
            found.append(("raw deflate", off, len(decomp)))
            print(f"RAW DEFLATE stream at 0x{off:06x}: decompressed {len(decomp)} bytes")
            break
    except Exception:
        pass

if not found:
    print("No immediate zlib/deflate stream found in 0x20000..0x40000")
