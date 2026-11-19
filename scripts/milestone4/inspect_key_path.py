import re

with open("Samsung-TV-Homebrew/analysis/decompressed_main.bin", "rb") as f:
    decomp = f.read()

# Let's search for KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_ENTER, etc.
key_names = [
    b"KEY_UP", b"KEY_DOWN", b"KEY_LEFT", b"KEY_RIGHT", b"KEY_ENTER",
    b"KEY_EXIT", b"KEY_MENU", b"KEY_POWER", b"KEY_SELECT", b"KEY_RETURN",
    b"VK_UP", b"VK_DOWN", b"VK_LEFT", b"VK_RIGHT", b"VK_SELECT"
]

print("=== Key Identifier Search ===")
for k in key_names:
    matches = [m.start() for m in re.finditer(re.escape(k), decomp)]
    print(f"{k.decode()}: {len(matches)} matches")
    for m in matches[:3]:
        sub = decomp[max(0, m-30):min(len(decomp), m+len(k)+30)]
        pr = "".join(chr(b) if 32 <= b <= 126 else " " for b in sub)
        print(f"  [0x{m:06x}]: {pr.strip()}")

# Search for ZUI Action handlers: MApp_ZUI_ACT*
zui_acts = re.findall(rb"MApp_ZUI_ACT[\w]+", decomp)
print(f"\nTotal MApp_ZUI_ACT symbols found: {len(zui_acts)}")
unique_acts = sorted(list(set([a.decode('latin1') for a in zui_acts])))
print("Unique action handlers:")
for a in unique_acts[:30]:
    print(" ", a)
