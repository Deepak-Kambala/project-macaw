with open("Samsung-TV-Homebrew/analysis/decompressed_main.bin", "rb") as f:
    decomp = f.read()

offset = 0x15c4e0
chunk = decomp[offset - 256 : offset + 256]
pr = "".join(chr(b) if 32 <= b <= 126 else "\n" for b in chunk)
lines = [l.strip() for l in pr.split("\n") if len(l.strip()) >= 2]
print("\n".join(lines))
