import re

with open("Samsung-TV-Homebrew/analysis/decompressed_main.bin", "rb") as f:
    decomp = f.read()

source_files = re.findall(rb"[\w\./\\]+\.c", decomp)
print(f"Total source file paths found: {len(source_files)}")
unique_sources = sorted(list(set([s.decode('latin1') for s in source_files])))
print(f"Unique source files: {len(unique_sources)}")
for s in unique_sources[:40]:
    print(" ", s)
