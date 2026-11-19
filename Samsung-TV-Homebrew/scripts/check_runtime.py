import re

with open("Samsung-TV-Homebrew/analysis/decompressed_main.bin", "rb") as f:
    decomp = f.read()

# Check for executable headers inside decompressed payload
elf_matches = [m.start() for m in re.finditer(b"\x7fELF", decomp)]
pe_matches = [m.start() for m in re.finditer(b"MZ", decomp)]
shebang_matches = [m.start() for m in re.finditer(b"#!/", decomp)]

print("ELF matches in decompressed:", [hex(m) for m in elf_matches])
print("Shebang matches in decompressed:", [hex(m) for m in shebang_matches])

# Check for any scripting engine or VM
vms = ["lua", "javascript", "v8", "quickjs", "duktape", "jerryscript", "python", "perl", "java", "jvm", "mhp", "bd-j", "flash", "swf", "webkit", "gecko", "opera", "browser"]
found_vms = {}
for vm in vms:
    matches = re.findall(re.escape(vm.encode()), decomp, re.IGNORECASE)
    if matches:
        found_vms[vm] = len(matches)

print("\nVM / Scripting Engine Scan:", found_vms)

# Check USB file extensions supported by DMP (Digital Media Player)
extensions = re.findall(rb"\.([a-zA-Z0-9]{2,4})\b", decomp)
ext_set = set([e.decode('latin1').lower() for e in extensions])
media_exts = [e for e in ext_set if e in ['mp3', 'wav', 'wma', 'aac', 'jpg', 'jpeg', 'png', 'bmp', 'avi', 'mp4', 'mkv', 'ts', 'mpg', 'mpeg', 'bin', 'txt', 'sub', 'srt', 'elf', 'sh', 'exe']]
print("\nSupported media extensions detected:", sorted(media_exts))
