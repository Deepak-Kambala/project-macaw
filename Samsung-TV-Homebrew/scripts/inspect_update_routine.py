with open("Samsung-TV-Homebrew/analysis/decompressed_main.bin", "rb") as f:
    decomp = f.read()

idx = decomp.find(b"CRC32 Integrity Check pass !!")
print(f"String at offset: 0x{idx:06x} ({idx})")

# Let's inspect 512 bytes before and after this string in decomp
# to see all adjacent strings and error messages
chunk = decomp[idx-300:idx+300]
pr = "".join(chr(b) if 32 <= b <= 126 else "\n" for b in chunk)
lines = [l.strip() for l in pr.split("\n") if len(l.strip()) >= 3]
print("\nSurrounding strings:")
for l in lines:
    print(" ", l)
