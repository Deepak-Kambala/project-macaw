import lzma
import struct
import re

FIRMWARE_PATH = "Samsung-TV-Homebrew/firmware/T-MXL0MASC.bin"

with open(FIRMWARE_PATH, "rb") as f:
    data = f.read()

# Scan for b"\x5d\x00\x00\x00\x04"
matches = [m.start() for m in re.finditer(b"\x5d\x00\x00\x00\x04", data)]
print(f"Total candidate LZMA headers found: {len(matches)}")

successful_chunks = []

for idx in matches:
    # Check if preceded by b"\xbe\xef" or similar
    prefix = data[max(0, idx-4):idx].hex(" ")
    stream = data[idx:min(len(data), idx + 2000000)] # up to 2MB slice
    try:
        # Check header
        hdr = stream[:13]
        uncomp_size = struct.unpack("<Q", hdr[5:13])[0]
        # Only try if uncomp_size is reasonable (< 64MB)
        if 0 < uncomp_size < 64 * 1024 * 1024:
            decomp = lzma.decompress(stream, format=lzma.FORMAT_ALONE)
            successful_chunks.append((idx, prefix, len(decomp), uncomp_size))
            print(f"Match at 0x{idx:06x} (prefix: {prefix}): uncomp_size={uncomp_size} -> decompressed={len(decomp)} bytes")
    except Exception as e:
        # Might be partial or raw
        pass

print(f"\nTotal successfully decompressed LZMA chunks: {len(successful_chunks)}")
