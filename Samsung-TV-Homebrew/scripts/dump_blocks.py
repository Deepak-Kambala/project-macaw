with open("Samsung-TV-Homebrew/analysis/decompressed_main.bin", "rb") as f:
    decomp = f.read()

def print_block(start, end):
    chunk = decomp[start:end]
    pr = "".join(chr(b) if 32 <= b <= 126 else "\n" for b in chunk)
    lines = [l.strip() for l in pr.split("\n") if len(l.strip()) >= 2]
    print("\n".join(lines))

print("=== BLOCK 1 (0x167a00 - 0x167d00) ===")
print_block(0x167a00, 0x167d00)

print("\n=== BLOCK 2 (0x16bb00 - 0x16be00) ===")
print_block(0x16bb00, 0x16be00)
