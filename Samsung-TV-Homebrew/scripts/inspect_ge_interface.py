import re

with open("Samsung-TV-Homebrew/analysis/decompressed_main.bin", "rb") as f:
    decomp = f.read()

ge_strings = [
    b"MDrv_GE_BitBltEX",
    b"MDrv_GE_FillRect",
    b"MDrv_GE_DrawLine",
    b"MDrv_GE_SetDstBuffer",
    b"MDrv_GE_SetSrcBuffer",
    b"MDrv_GE_Chip_Proprity_Init"
]

print("=== MStar GE Graphics Engine Strings in Decompressed Main ===")
for s in ge_strings:
    idx = decomp.find(s)
    print(f"String '{s.decode()}' found at: 0x{idx:06x} ({idx})")

# Look at the string block at 0x17bd35
start = 0x17bd00
end = 0x17be50
chunk = decomp[start:end]
pr = "".join(chr(b) if 32 <= b <= 126 else "\n" for b in chunk)
lines = [l.strip() for l in pr.split("\n") if len(l.strip()) >= 3]
print("\nSurrounding strings:")
for l in lines:
    print(" ", l)
