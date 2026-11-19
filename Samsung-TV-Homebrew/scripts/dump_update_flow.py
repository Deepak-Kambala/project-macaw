with open("Samsung-TV-Homebrew/analysis/decompressed_main.bin", "rb") as f:
    decomp = f.read()

start = 0x16af00
end = 0x16b300
chunk = decomp[start:end]
pr = "".join(chr(b) if 32 <= b <= 126 else "\n" for b in chunk)
lines = [l.strip() for l in pr.split("\n") if len(l.strip()) >= 2]
print("\n".join(lines))
