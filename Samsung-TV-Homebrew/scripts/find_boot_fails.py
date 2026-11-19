with open("Samsung-TV-Homebrew/firmware/T-MXL0MASC.bin", "rb") as f:
    data = f.read()

import re

# Search Block 0 and Block 1 for error messages, failure strings, watchdog, or recovery
boot_strings = re.findall(rb"[\x20-\x7e]{4,}", data[:0x23880])
print(f"Total strings in bootloader (0x000000 - 0x023880): {len(boot_strings)}")
for s in boot_strings:
    dec = s.decode('latin1')
    if any(k in dec.lower() for k in ["fail", "err", "trap", "reset", "recover", "watchdog", "wdt", "boot", "usb", "update"]):
        print(" ", dec)
