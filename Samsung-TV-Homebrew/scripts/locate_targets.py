FIRMWARE_PATH = "Samsung-TV-Homebrew/firmware/T-MXL0MASC.bin"

with open(FIRMWARE_PATH, "rb") as f:
    data = f.read()

targets = [
    b"T-MXL0MASC",
    b"Aeon",
    b"Macaw12",
    b"MSVC0000S3",
    b"SBT_YYMMDD00536735000",
    b"oversubscribed literal/length tree",
    b"zlib",
    b"inflate",
    b"deflate"
]

for t in targets:
    pos = 0
    while True:
        idx = data.find(t, pos)
        if idx == -1:
            break
        print(f"Target '{t.decode('latin1')}' found at 0x{idx:08x} ({idx})")
        # print surrounding 64 bytes
        start = max(0, idx - 16)
        end = min(len(data), idx + len(t) + 32)
        print("  Context:", data[start:end])
        pos = idx + len(t)
