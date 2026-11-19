# Project Macaw — Samsung TV Firmware Reverse Engineering

Reverse engineering and static analysis of Samsung TV firmware for **Samsung UA23H4003AR** (Platform: `T-MXL0MASC-1040.0`).

This project investigates whether custom software execution or homebrew is feasible via the television's USB port.

---

## Hardware & Environment Specifications

- **Target Device:** Samsung UA23H4003AR (Series 4 LED DTV)
- **Firmware Package:** `T-MXL0MASC.bin` (v1040.0)
- **Flash ROM Size:** 3,850,724 bytes (~3.67 MB, 4MB SPI NOR Flash)
- **System-on-Chip (SoC):** MStar Semiconductor `macaw12` platform (TSUMV59 / MSD3xxx family)
- **CPU Architecture:** 
  - Primary: **MStar Aeon RISC32** (OpenRISC 1000 / OR1200 compatible core)
  - Secondary: **MStar R2 / PM coprocessor**
- **Operating System:** MStar Chameleon / Utopia Bare-Metal RTOS (`"not enable MSOS_TYPE_LINUX"`)

---

## Key Findings (Milestone 1)

> **Research Goal:** Determine whether the TV has an application execution environment that can be accessed through USB.

### Conclusion:
**No native application execution environment exists.**
1. **Not a Smart TV:** Unlike higher-tier Samsung Smart TVs (Series 5000+) which run Linux (Orsay or Tizen) and support widgets, this is a dedicated hardware scaler TV running a bare-metal RTOS.
2. **No Userland/Shell:** The firmware lacks any POSIX userland, dynamic linker, shell (`/bin/sh`), or script interpreter (no JavaScript, Lua, Python, or Java/MHP).
3. **USB Limitation:** The USB interface is bound exclusively to `MApp_FileBrowser` (Digital Media Player / ConnectShare), which parses strictly fixed media formats (JPEG image decoding, WAV/MP3 audio playback via hardware DSP).
4. **Firmware Update Mechanism:** The only USB code execution path is `USB SW Update!` which expects `T-MXL0MASC.BIN` and verifies it using a **CRC32 integrity check** before writing blocks to flash (`Store2Flash`).
5. **Community Homebrew:** The SamyGO project does not support the `T-MXL` firmware generation due to the absence of Linux and network daemons.

---

## Repository Structure

```
.
├── README.md
└── Samsung-TV-Homebrew/
    ├── firmware/
    │   └── T-MXL0MASC.bin             # Original firmware binary
    ├── analysis/
    │   ├── decompressed_main.bin      # Decompressed main OS payload (3.1 MB)
    │   ├── decompressed_strings.txt   # Strings extracted from main payload
    │   └── strings.txt                # Raw firmware string dump
    ├── scripts/
    │   ├── analyze_firmware.py        # Entropy and block analysis
    │   ├── test_zlib.py               # Raw DEFLATE detection and extraction
    │   ├── find_all_lzma.py           # Resource partition chunk decompressor
    │   ├── analyze_main_payload.py    # Decompressed payload inspection
    │   └── find_update_validation.py  # USB SW Update & CRC verification audit
    └── reports/
        └── firmware-analysis.md       # Comprehensive technical report
```

---

## Detailed Report

Read the complete technical report in:
- [firmware-analysis.md](Samsung-TV-Homebrew/reports/firmware-analysis.md)
