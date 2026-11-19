import struct

FIRMWARE_PATH = "Samsung-TV-Homebrew/firmware/T-MXL0MASC.bin"

with open(FIRMWARE_PATH, "rb") as f:
    data = f.read()

print(f"File size: {len(data)} (0x{len(data):x})")

# Let's search for magic numbers or header patterns across the entire file
# Check occurrences of 55 aa, MSVC, dead, etc.
def find_all(sub, b):
    pos = 0
    res = []
    while True:
        idx = b.find(sub, pos)
        if idx == -1:
            break
        res.append(idx)
        pos = idx + len(sub)
    return res

print("\nOccurrences of 0x55aa (or b'\\x55\\xaa' / b'\\xaa\\x55'):")
for idx in find_all(b"\x55\xaa", data)[:10]:
    print(f"  0x{idx:06x}: {data[idx:idx+16].hex(' ')}")
for idx in find_all(b"\xaa\x55", data)[:10]:
    print(f"  0x{idx:06x}: {data[idx:idx+16].hex(' ')}")

print("\nOccurrences of b'MSVC':")
for idx in find_all(b"MSVC", data):
    print(f"  0x{idx:06x}: {data[idx:idx+32]}")

print("\nOccurrences of b'dead' (case-insensitive):")
for idx in find_all(b"\xde\xad", data)[:10]:
    print(f"  0x{idx:06x}: {data[idx:idx+16].hex(' ')}")
for idx in find_all(b"\xad\xde", data)[:10]:
    print(f"  0x{idx:06x}: {data[idx:idx+16].hex(' ')}")
