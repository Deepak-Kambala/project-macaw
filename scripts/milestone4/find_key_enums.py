import re

with open("Samsung-TV-Homebrew/analysis/decompressed_main.bin", "rb") as f:
    decomp = f.read()

matches = re.findall(rb"[\w]+_KEY[\w]*", decomp)
print(f"Total symbols matching *_KEY*: {len(matches)}")
unique_keys = sorted(list(set([m.decode('latin1') for m in matches])))
for k in unique_keys[:30]:
    print(" ", k)
