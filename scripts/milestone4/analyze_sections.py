import math
from collections import Counter

def calculate_entropy(chunk):
    if not chunk:
        return 0.0
    c = Counter(chunk)
    l = len(chunk)
    return -sum((cnt / l) * math.log2(cnt / l) for cnt in c.values())

with open("Samsung-TV-Homebrew/analysis/decompressed_main.bin", "rb") as f:
    data = f.read()

total_len = len(data)
window_size = 32768
num_windows = (total_len + window_size - 1) // window_size

print(f"Total size: {total_len} bytes ({total_len/1024/1024:.2f} MB)")
print("=== Entropy Analysis of Decompressed Main Payload (32KB blocks) ===")

for i in range(num_windows):
    s = i * window_size
    e = min((i + 1) * window_size, total_len)
    chunk = data[s:e]
    ent = calculate_entropy(chunk)
    zero_cnt = chunk.count(0)
    ascii_cnt = sum(1 for b in chunk if 32 <= b <= 126)
    bar = "#" * int(ent * 4)
    print(f"[{s:06x} - {e:06x}] ({e-s:5d} B): ent={ent:5.3f} | zeros={zero_cnt:5d} | ascii={ascii_cnt:5d} | {bar}")
