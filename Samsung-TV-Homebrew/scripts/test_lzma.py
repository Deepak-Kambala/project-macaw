import lzma
import struct

FIRMWARE_PATH = "Samsung-TV-Homebrew/firmware/T-MXL0MASC.bin"

with open(FIRMWARE_PATH, "rb") as f:
    data = f.read()

# Let's inspect the chunk at 0x3703a0
# 0x3703a0 has 'be ef' at 0x3703a8
marker = 0x3703a8
print("Marker:", data[marker:marker+24].hex(" "))
# What follows 'be ef':
# 5d 00 00 00 04  (5 bytes: LZMA properties: 5d, dict size: 00 00 00 04 or 04 00 00 00?)
# Then uncompressed size (8 bytes in standard lzma)
# Let's check standard lzma format:
# props: 5 bytes
# uncompressed size: 8 bytes (uint64 little endian)
# compressed data: rest
stream_start = marker + 2
props = data[stream_start:stream_start+5]
print("Props:", props.hex(" "))

# Try standard LZMA decompression on that chunk
try:
    # Let's see what happens if we feed it props + uncompressed size (-1 for unknown or 8 bytes)
    # If the format is props (5 bytes) + 8 bytes size:
    hdr = data[stream_start:stream_start+13]
    print("Header candidate:", hdr.hex(" "))
    decomp = lzma.decompress(data[stream_start:stream_start+50000], format=lzma.FORMAT_ALONE)
    print("Decompression SUCCESS! Decompressed size:", len(decomp))
    print("First 128 bytes of decompressed:")
    print(decomp[:128])
except Exception as e:
    print("Standard decompression failed:", e)

    # Let's test raw decompressor with custom properties
    try:
        # If props is 5 bytes: 5d ...
        decompressor = lzma.LZMADecompressor(format=lzma.FORMAT_RAW, filters=[
            {"id": lzma.FILTER_LZMA1, "dict_size": 1 << 22, "lc": 3, "lp": 0, "pb": 2}
        ])
        raw_data = data[stream_start+13:stream_start+20000]
        res = decompressor.decompress(raw_data)
        print("Raw LZMA1 decompression SUCCESS! Decompressed size:", len(res))
        print("First 128 bytes:")
        print(res[:128])
    except Exception as e2:
        print("Raw decompression failed:", e2)
