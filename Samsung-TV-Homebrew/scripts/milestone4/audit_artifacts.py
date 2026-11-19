import hashlib
import os

files = [
    "Samsung-TV-Homebrew/firmware/T-MXL0MASC.bin",
    "Samsung-TV-Homebrew/analysis/decompressed_main.bin",
    "Samsung-TV-Homebrew/analysis/decompressed_strings.txt",
    "Samsung-TV-Homebrew/analysis/strings.txt",
    "Samsung-TV-Homebrew/reports/firmware-analysis.md",
    "Samsung-TV-Homebrew/reports/milestone-2.md",
    "Samsung-TV-Homebrew/reports/milestone-3.md"
]

print("=== Artifact Audit & Checksums ===")
for path in files:
    if os.path.exists(path):
        size = os.path.getsize(path)
        with open(path, "rb") as f:
            content = f.read()
        md5 = hashlib.md5(content).hexdigest()
        sha256 = hashlib.sha256(content).hexdigest()
        print(f"File: {path}")
        print(f"  Size:   {size} bytes ({size/1024/1024:.2f} MB)")
        print(f"  MD5:    {md5}")
        print(f"  SHA256: {sha256}\n")
    else:
        print(f"MISSING: {path}\n")
