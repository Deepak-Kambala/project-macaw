import re

with open("Samsung-TV-Homebrew/analysis/decompressed_main.bin", "rb") as f:
    decomp = f.read()

def find_context(pattern, max_results=10):
    print(f"\n=== Context for pattern: {pattern} ===")
    matches = [m.start() for m in re.finditer(re.escape(pattern), decomp, re.IGNORECASE)]
    for m in matches[:max_results]:
        start = max(0, m - 100)
        end = min(len(decomp), m + len(pattern) + 150)
        sub = decomp[start:end]
        # extract printable
        pr = "".join(chr(b) if 32 <= b <= 126 else "\n" for b in sub)
        cleaned = "\n".join([line.strip() for line in pr.split("\n") if len(line.strip()) >= 3])
        print(f"-- Match at 0x{m:06x} --\n{cleaned}")

find_context(b"USB SW Update")
find_context(b"T-MXL")
find_context(b"MSOS")
find_context(b"Uart Debug Menu")
find_context(b"upgrade")
find_context(b"MApp_FileBrowser")
