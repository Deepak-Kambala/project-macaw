with open("Samsung-TV-Homebrew/firmware/T-MXL0MASC.bin", "rb") as f:
    data = f.read()

block0 = data[0x000000:0x010000]
block1 = data[0x010000:0x020000]

print(f"Block 0 non-zero bytes: {sum(1 for b in block0 if b != 0)}")
print(f"Block 1 non-zero bytes: {sum(1 for b in block1 if b != 0)}")

# Find differences between block 0 and block 1
diffs = [i for i in range(0x10000) if block0[i] != block1[i]]
print(f"Differences between Block 0 and Block 1: {len(diffs)} bytes")

# Let's see what is in block 0 vs block 1
import re
str0 = set(re.findall(rb"[\x20-\x7e]{4,}", block0))
str1 = set(re.findall(rb"[\x20-\x7e]{4,}", block1))
print("Strings unique to Block 0:", len(str0 - str1), [s.decode('latin1') for s in list(str0 - str1)[:5]])
print("Strings unique to Block 1:", len(str1 - str0), [s.decode('latin1') for s in list(str1 - str0)[:5]])
print("Common strings:", len(str0 & str1), [s.decode('latin1') for s in list(str0 & str1)[:5]])
