with open("Samsung-TV-Homebrew/analysis/decompressed_main.bin", "rb") as f:
    decomp = f.read()

import re

# Look for GDI, Window, Draw, Rect, Paint, Blt functions
gdi_matches = [m.start() for m in re.finditer(rb"(?:_APIgdi|GDI|Draw|Fill|Rect|Paint|Canvas|Bitmap|Font)[^\x00\r\n]{4,60}", decomp)]
print(f"Total GDI matches: {len(gdi_matches)}")
unique_gdi = sorted(list(set([decomp[m:m+80].split(b"\x00")[0].decode('latin1', errors='ignore') for m in gdi_matches])))
for s in unique_gdi[:35]:
    print(" ", s)
