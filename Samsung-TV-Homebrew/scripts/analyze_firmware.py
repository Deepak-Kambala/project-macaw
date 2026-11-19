import os
import sys
import math
import re
from collections import Counter

FIRMWARE_PATH = "Samsung-TV-Homebrew/firmware/T-MXL0MASC.bin"

def calculate_entropy(data_chunk):
    if not data_chunk:
        return 0.0
    counter = Counter(data_chunk)
    length = len(data_chunk)
    return -sum((count / length) * math.log2(count / length) for count in counter.values())

def main():
    if not os.path.exists(FIRMWARE_PATH):
        print(f"Error: {FIRMWARE_PATH} not found")
        sys.exit(1)

    file_size = os.path.getsize(FIRMWARE_PATH)
    print(f"File: {FIRMWARE_PATH}")
    print(f"File size: {file_size} bytes ({file_size / 1024 / 1024:.2f} MB, hex: {hex(file_size)})")

    with open(FIRMWARE_PATH, "rb") as f:
        data = f.read()

    # Overall entropy
    overall_entropy = calculate_entropy(data)
    print(f"Overall Entropy: {overall_entropy:.4f} (out of 8.0)")

    # Find first non-zero byte
    first_non_zero = None
    for idx, b in enumerate(data):
        if b != 0:
            first_non_zero = idx
            break
    print(f"First non-zero byte offset: {hex(first_non_zero) if first_non_zero is not None else 'None'}")

    # Inspect first 128 bytes after first non-zero
    if first_non_zero is not None:
        chunk = data[first_non_zero:first_non_zero + 128]
        print(f"\nHex dump at first non-zero byte ({hex(first_non_zero)}):")
        for i in range(0, len(chunk), 16):
            hex_str = " ".join(f"{b:02x}" for b in chunk[i:i+16])
            ascii_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk[i:i+16])
            print(f"  {first_non_zero + i:08x}: {hex_str:<48}  {ascii_str}")

    # Block entropy analysis (e.g., 64KB blocks)
    block_size = 65536
    num_blocks = (file_size + block_size - 1) // block_size
    print(f"\nBlock Entropy (64KB chunks, total {num_blocks} blocks):")
    for i in range(num_blocks):
        start = i * block_size
        end = min((i + 1) * block_size, file_size)
        ent = calculate_entropy(data[start:end])
        bar = "#" * int(ent * 4)
        print(f"  [{start:08x} - {end:08x}] ({end-start:5d} B) : {ent:6.3f} | {bar}")

    # Search for known signatures
    signatures = {
        b"\x1f\x8b\x08": "GZIP",
        b"\x42\x5a\x68": "BZIP2",
        b"\xfd7zXZ\x00": "XZ",
        b"hsqs": "SquashFS (little endian)",
        b"sqsh": "SquashFS (big endian)",
        b"\x28\xcd\x3d\x45": "Zstandard",
        b"\x5d\x00\x00": "LZMA raw header candidate",
        b"\x7fELF": "ELF executable",
        b"UBI#": "UBI superblock",
        b"\x27\x05\x19\x56": "U-Boot legacy image",
        b"\xd0\x0d\xfe\xed": "Flattened Device Tree (FDT / DTB)",
        b"PK\x03\x04": "ZIP archive",
        b"ROMfs": "ROMFS",
        b"\x45\x3d\xcd\x28": "CramFS",
        b"MStar": "MStar string/signature",
        b"MSW": "MStar software signature",
        b"MTK": "MediaTek string",
        b"RTK": "Realtek string",
        b"Linux": "Linux string",
        b"bootloader": "bootloader string",
        b"u-boot": "U-Boot string",
        b"BOOT": "BOOT string",
    }

    print("\nSignature scan results:")
    for sig, name in signatures.items():
        matches = [m.start() for m in re.finditer(re.escape(sig), data)]
        if matches:
            print(f"  Found '{name}' ({len(matches)} occurrences):")
            for m in matches[:10]:
                context = data[max(0, m - 16):min(file_size, m + len(sig) + 16)]
                print(f"    Offset {hex(m)} ({m})")
            if len(matches) > 10:
                print(f"    ... and {len(matches) - 10} more.")

if __name__ == "__main__":
    main()
