import re

with open("Samsung-TV-Homebrew/analysis/decompressed_main.bin", "rb") as f:
    decomp = f.read()

# Let's search for IR / Remote control strings
patterns = [b"ir", b"remote", b"key", b"rc5", b"nec", b"samsung", b"uart", b"service"]

for p in [b"IR_", b"msIR", b"MDrv_IR", b"Remote", b"Key", b"UART", b"Service", b"Debug"]:
    matches = [m.start() for m in re.finditer(re.escape(p), decomp)]
    print(f"Pattern {p}: {len(matches)} matches")
    for m in matches[:5]:
        sub = decomp[max(0, m-40):min(len(decomp), m+len(p)+60)]
        pr = "".join(chr(b) if 32 <= b <= 126 else " " for b in sub)
        print(f"  [0x{m:06x}]: {pr.strip()}")
