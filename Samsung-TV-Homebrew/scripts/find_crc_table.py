import re
with open("Samsung-TV-Homebrew/analysis/decompressed_main.bin", "rb") as f:
    decomp = f.read()

# Polynomial for CRC32: 0xEDB88320 (little endian: 20 83 b8 ed) or 0x04C11DB7
matches_poly1 = [m.start() for m in re.finditer(b"\x20\x83\xb8\xed", decomp)]
matches_poly2 = [m.start() for m in re.finditer(b"\xed\xb8\x83\x20", decomp)]
matches_poly3 = [m.start() for m in re.finditer(b"\x04\xc1\x1d\xb7", decomp)]
matches_poly4 = [m.start() for m in re.finditer(b"\xb7\x1d\xc1\x04", decomp)]

print("CRC32 polynomial matches:")
print("  LE 0xEDB88320:", [hex(m) for m in matches_poly1])
print("  BE 0xEDB88320:", [hex(m) for m in matches_poly2])
print("  BE 0x04C11DB7:", [hex(m) for m in matches_poly3])
print("  LE 0x04C11DB7:", [hex(m) for m in matches_poly4])
