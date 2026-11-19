import re

with open("Samsung-TV-Homebrew/analysis/decompressed_main.bin", "rb") as f:
    decomp = f.read()

# Look for upgrade / update strings and validation
update_strings = [s for s in re.findall(rb"[\x20-\x7e]{4,}", decomp) if any(k in s.lower() for k in [b"update", b"crc", b"checksum", b"verify", b"check", b"swu", b"upgrade", b"flash"])]
print(f"Found {len(update_strings)} update/crc related strings:")
for s in update_strings[:30]:
    print(" ", s.decode('latin1'))
