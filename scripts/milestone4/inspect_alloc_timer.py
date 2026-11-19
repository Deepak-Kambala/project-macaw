import re

with open("Samsung-TV-Homebrew/analysis/decompressed_main.bin", "rb") as f:
    decomp = f.read()

alloc_patterns = [
    b"malloc", b"free", b"MsOS_AllocateMemory", b"MsOS_FreeMemory",
    b"msAPI_Memory_Allocate", b"msAPI_Memory_Free", b"heap",
    b"timer", b"timerCB", b"msAPI_Timer", b"MDrv_Timer"
]

print("=== Memory Allocation & Timer Functions in Main Binary ===")
for p in alloc_patterns:
    matches = [m.start() for m in re.finditer(re.escape(p), decomp, re.IGNORECASE)]
    print(f"Pattern '{p.decode()}': {len(matches)} matches")
    for m in matches[:3]:
        sub = decomp[max(0, m-30):min(len(decomp), m+len(p)+40)]
        pr = "".join(chr(b) if 32 <= b <= 126 else " " for b in sub)
        print(f"  [0x{m:06x}]: {pr.strip()}")
