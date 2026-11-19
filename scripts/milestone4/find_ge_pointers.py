import struct

with open("Samsung-TV-Homebrew/analysis/decompressed_main.bin", "rb") as f:
    decomp = f.read()

# Let's search for occurrences of string offset 0x17bd3e (or vaddr 0x8017bd3e, 0x0017bd3e, 0x17bd3e)
# Also look around the string table for GE functions
# Look at 0x17bd12 to 0x17be00:
# Strings:
# MDrv_GE_Chip_Proprity_Init
# MDrv_GE_BitBltEX
# MDrv_GE_FillRect
# MDrv_GE_DrawLine
# MDrv_GE_SetDstBuffer
# MDrv_GE_SetSrcBuffer
# MDrv_GE_SetYUVMode
# MDrv_GE_SetClipWindow

# Let's find any pointer tables in decomp that point into 0x17bxxx
for off in range(0, len(decomp)-4, 4):
    val_le = struct.unpack("<I", decomp[off:off+4])[0]
    val_be = struct.unpack(">I", decomp[off:off+4])[0]
    
    # Check if value points to MDrv_GE_FillRect (0x17bd3e or 0x8017bd3e)
    if val_be in (0x17bd3e, 0x8017bd3e, 0xa017bd3e):
        print(f"Pointer to 'MDrv_GE_FillRect' (BE) at 0x{off:06x}: 0x{val_be:08x}")
    if val_le in (0x17bd3e, 0x8017bd3e, 0xa017bd3e):
        print(f"Pointer to 'MDrv_GE_FillRect' (LE) at 0x{off:06x}: 0x{val_le:08x}")

# Let's search for GE initialization strings and functions
for s in [b"GE init", b"MDrv_GE_Init", b"MApi_GE", b"drvGE", b"msAPI_GE"]:
    pos = 0
    while True:
        idx = decomp.find(s, pos)
        if idx == -1:
            break
        print(f"Match for {s}: 0x{idx:06x} -> {decomp[idx:idx+40]}")
        pos = idx + len(s)
