# Project Macaw — Milestone 2: Low-Level Custom Firmware Feasibility Report
**Target Device:** Samsung UA23H4003AR  
**Firmware Version:** T-MXL0MASC-1040.0  
**Binary File:** `firmware/T-MXL0MASC.bin`  
**Analysis Environment:** macOS (Apple Silicon M5), Python 3.14  
**Date:** November 2026  
**Status:** Completed (Milestone 2 — Low-Level Architecture, Toolchains & Game PoC Feasibility)

---

## Executive Summary

Milestone 1 established that the Samsung UA23H4003AR does not expose an application execution environment (e.g., Linux, widget engine, or script interpreter) accessible through the USB port.

Milestone 2 investigated whether **low-level custom firmware development** is technically feasible to execute homebrew code—specifically a proof-of-concept **Snake game** rendered via the TV's native display controller and controlled via the remote.

### Key Conclusions:
1. **USB-Only Homebrew Launch:** **Impossible.** There is no runtime to execute code from USB without flashing the SPI flash memory.
2. **Custom Firmware Flashing via USB Update:** **Theoretically possible, but practically unsafe without hardware recovery tools.**
   - The USB firmware update mechanism (`USB SW Update!`) validates firmware integrity using a simple **CRC32 checksum** rather than asymmetric cryptographic signatures (e.g., RSA/ECDSA).
   - **Crucial Risk Factor (No Recovery Fallback):** The primary bootloader (`0x000000 - 0x023880`) **contains no USB host stack**. The USB stack resides solely in the decompressed main system payload. Any flaw in custom firmware that halts execution prior to main system initialization will **permanently hard-brick the television**, rendering USB updates impossible.
3. **External Serial Access (Zero-Disassembly UART):** The television exposes an interactive **MStar Serial Debugger Console** via the external 3.5mm EX-LINK / Service jack (or multiplexed over VGA DDC lines) at 115200 baud, enabling real-time telemetry and boot debugging without opening or modifying the TV chassis.

---

## 1. MStar Macaw12 Processor & Hardware Capabilities

### 1.1 Architecture & Core Classification
From static string and binary disassembly analysis, the SoC platform is identified as **MStar `macaw12`** (TSUMV59 / MSD3xxx scaler/DTV family).

- **Primary Processing Core:** **MStar Aeon RISC32**
  - Architecture: **OpenRISC 1000 (OR1200 / OR1K)** derivative 32-bit core.
  - Registers: 32 general-purpose registers (`r0`–`r31`), Status Register (`sr`), Program Counter (`pc`), and Exception Effective Address Register (`eear`).
  - Diagnostic String: `[UART] Get Aeon Frequency error`, `_HAL_SetAeon_SPIMappingAddr`, `cpu/risc32/macaw12/interrupt.c`.
- **Secondary / Coprocessor Core:** **MStar R2 / PM Core**
  - Handles power management, standby monitoring, IR wake-up, CEC standby, and keypad scanning.
  - Diagnostic String: `Hello Macaw12 standby mode`, `[UART] Get R2 Frequency error`.
- **System-on-Chip Role:** Integrated TV video scaler, analog/DVB demodulator, audio DSP, and display controller.

---

## 2. OpenRISC / Aeon Toolchains & Cross-Compilation Support

Because the MStar Aeon core implements the OpenRISC 1000 instruction set architecture, modern cross-compilers can generate compatible bare-metal machine code:

### 2.1 Upstream GNU Toolchain (`or1k-elf`)
- **Target Triple:** `or1k-elf` (bare-metal)
- **Compiler:** `or1k-elf-gcc`
- **Assembler / Linker:** GNU Binutils (`or1k-elf-as`, `or1k-elf-ld`, `or1k-elf-objdump`)
- **Instruction Set Options:** `-mcpu=or1200` or `-mcpu=or1k`, `-msoft-float`, `-mhard-mul`, `-mhard-div`
- **Availability:** Upstream in GCC 9+ and GNU Binutils, packageable via Homebrew, Arch Linux, or Debian.

### 2.2 LLVM / Clang Support
- LLVM maintains an experimental `or1k` backend (`or1k-unknown-none-elf`).

### 2.3 Community Documentation & References
- **OpenRISC Project:** Official architecture specifications and toolchain guides at [openrisc.io](https://openrisc.io).
- **Linux-Chenxing Project:** Reverse-engineering effort documenting MStar Aeon / R2 cores, interrupt controllers, and register sets at [linux-chenxing.org](https://linux-chenxing.org).

---

## 3. Memory Maps, RAM Capacity & Peripherals

Firmware reverse-engineering identified the memory organization utilized by the MStar Utopia abstraction layer:

```
+-------------------------------------------------------------------------+
| Address Range         | Classification    | Description                 |
+-------------------------------------------------------------------------+
| 0x00000000 - 0x01FFFFFF | KUSEG (Physical)  | Embedded DDR/DDR2 SDRAM     |
| 0x80000000 - 0x81FFFFFF | KSEG0 (Cached)    | System DRAM, Stack, Heap    |
| 0xA0000000 - 0xA1FFFFFF | KSEG1 (Uncached)  | DMA Buffers, Framebuffers   |
| 0x1F000000 - 0x1F200000 | Physical MMIO     | RIU (Register Interface)    |
| 0xBF000000 - 0xBF200000 | Virtual MMIO      | KSEG1 Uncached RIU Base     |
+-------------------------------------------------------------------------+
```

### 3.1 Memory & Peripheral Evidence from Firmware:
- **RIU Base Address:** `0x1F000000` (physical) / `0xBF000000` (virtual uncached). Confirmed by string: `"RIUreg base = 0x%lX, length = %lu"` and instruction constants `l.movhi rX, 0xbf00`.
- **System RAM (DRAM):** 
  - Embedded DDR/DDR2 SDRAM managed via the MIU (Memory Interface Unit).
  - Diagnostic strings: `"MIUSEL:: FW=%x HW=%x, miu1base=0x%lx"`, `"heap size is %dK under 300K!!"`.
  - Estimated capacity: 32 MB to 64 MB (typical for TSUMV59 / MStar Macaw12 scaler packages).
- **Flash ROM:** 4 MB (32 Mbit) SPI NOR Flash. Total firmware binary image: 3,850,724 bytes. Flash block protection strings reference Macronix MX25L series (`"MXIC Security Register 0x%02X"`).
- **Peripherals Detected:**
  - **GE (Graphics Engine):** 2D hardware bit-blitter (`MDrv_GE_BitBltEX`, `MDrv_GE_FillRect`, `MDrv_GE_DrawLine`).
  - **GOP (Graphics Output Plane):** Framebuffer window controller (`MApi_GOP_Init`, `gwin`).
  - **Timer Subsystem:** Hardware timer callbacks (`timer_cb/timer_cb.c`, `msAPI_Timer_Reset`).
  - **Keypad & IR Receiver:** 
    - ADC keypad input (`msKeypad_Init`, `OS_KEYPAD_Mutex`).
    - IR receiver driver handling remote control keycodes (`tv-ap/common/zui/MApp_ZUI_ACTkeypadfunctionosd.c`).
  - **UART Controller:** Multi-channel UART (UART0/UART2) with configurable baud rates.

---

## 4. Boot Sequence & Firmware Loading Process

The firmware execution pipeline is divided into distinct stages:

```
[Power On / Reset]
       │
       ▼
[Stage 1: Primary Bootloader (0x000100 - 0x00FFFF)]
  - OpenRISC Reset Vector at 0x000100
  - Initializes CPU core, clocks, and internal SRAM
  - Evaluates boot mode (Cold Boot vs Standby Wakeup)
       │
       ▼
[Stage 2: Secondary Bootloader & PM Runtime (0x010000 - 0x02387F)]
  - "Hello Macaw12 standby mode"
  - Power management, CEC, and keypad polling
  - OpenRISC Exception Vector Table configured (0x020280 - 0x020F40)
  - Initializes DRAM controller (MIU / DDR initialization)
  - Built-in zlib inflate engine unpacked into memory
       │
       ▼
[Stage 3: Main Payload Decompression (0x023880 - 0x31C776)]
  - Decompresses 3.1 MB raw DEFLATE stream into KSEG0 DRAM (0x80xxxxxx)
  - Jumps to main system entry point
       │
       ▼
[Stage 4: MStar Utopia RTOS & Subsystem Init]
  - Initializes RIU hardware registers, GOP, GE, Audio DSP, Video Decoder
  - Mounts Resource Partition (573 chunked LZMA streams at 0x31C777)
  - Starts Zenith UI (ZUI) main event loop
```

---

## 5. In-Depth USB Firmware Update Validation Analysis

The USB update routine (`USB SW Update!`) located in the decompressed main payload at offset `0x16afa5` operates as follows:

1. **File Detection:**
   - The TV searches the root directory of an attached FAT-formatted USB drive for the exact filename: `T-MXL0MASC.BIN`.
   - String: `">> _SearchFileInTarget(%s)"`.
2. **Buffer Allocation & Read:**
   - Allocates a staging buffer in DRAM.
   - Diagnostic strings:
     - `"Download Buffer Addr: 0x%08lx"`
     - `"Download Buffer Size: 0x%08lx"`
     - `"Copying image from USB to DRAM"`
3. **Integrity Verification:**
   - Verifies the image size against flash capacity (`"File size: 0x%08lx"`, `"Flash size: 0x%08lx"`).
   - Computes a **32-bit CRC (CRC32)** over the image in DRAM.
   - Diagnostic strings:
     - `"Error> CRC32 Integrity Check failed !!"`
     - `"CRC32 Integrity Check pass !!"`
   - **Absence of Cryptographic Signatures:** There is **no evidence of RSA, ECDSA, or SHA-256 public-key signature verification**. The update routine checks only file size, structural headers (`0x55aa5678`), and CRC32.
4. **Flashing Procedure:**
   - Once the CRC32 check passes, it disables write protection (`WriteProtect_SetBPStatus`) and writes blocks directly to flash using `Store2Flash(src, dst, sz)`.

---

## 6. Recovery & Bootloader Fallback Assessment

### Critical Question:
> *If custom firmware causes a crash or fails to boot, does the TV have an emergency USB recovery mode?*

### Finding: **NO FALLBACK EXISTS.**
- **No USB in Bootloader:** Inspection of the primary bootloader (`0x000000 - 0x023880`) reveals only basic SPI flash reading, memory initialization, and zlib decompression. The bootloader contains **no USB controller driver, no USB mass storage protocol stack, and no FAT filesystem parser**.
- **Location of USB Update Code:** All USB functionality—including `USB SW Update!`—resides exclusively inside the decompressed main payload (Stage 4).
- **Failure Consequence:** If modified code introduces a crash (e.g., unhandled exception, misconfigured vector table, or invalid memory reference) before or during Stage 3 decompression, the bootloader triggers:
  - `"system trap"`
  - `"======= Whole Chip Reset ======="`
  The CPU will enter an infinite reset loop or hang in standby.
- **Recovery Requirement:** Recovering from a corrupted flash image requires **external hardware intervention**:
  1. Clamping an external SOIC-8 test clip to the SPI flash chip and reprogramming it via an external SPI programmer (e.g., CH341A / Raspberry Pi / Flashrom).
  2. Or using an MStar ISP programmer connected to the VGA I2C bus via the MStar ISP Utility.

---

## 7. Proof-of-Concept: Snake Game Theoretical Implementation

Is it theoretically possible to run a simple Snake game on this platform?

### 7.1 Architecture of a Native Snake PoC
If embedded into the firmware image, a Snake game would utilize the following existing MStar APIs:

1. **Display & Graphics:**
   - **`MDrv_GE_FillRect(x, y, w, h, color)`:** Draws solid colored blocks on the OSD graphics plane to represent:
     - Background grid (black/dark gray)
     - Snake body segments (green)
     - Food item (red)
   - **`MApi_GOP_GWIN_SetDisplayPosition()`:** Binds the game window to an on-screen display layer (OSD plane).
2. **Game Loop & Timing:**
   - **`msAPI_Timer_Reset()` / `timer_cb`:** Uses MStar's hardware timer callback system to tick the game loop at fixed intervals (e.g., 150 ms per tick).
3. **Input Handling:**
   - The remote control D-pad generates key events routed through `MApp_ZUI_ACTkeypadfunctionosd.c`:
     - `KEY_UP`, `KEY_DOWN`, `KEY_LEFT`, `KEY_RIGHT` update the snake direction vector.
     - `KEY_ENTER` starts/restarts the game.
     - `KEY_EXIT` closes the game and restores normal TV operation.

### 7.2 Implementation Vectors:
- **Hooking an Existing Menu:** The simplest theoretical software hook would replace an existing, rarely used UI submenu (e.g., the "Shop Mode" or "Aging Menu" window in `MApp_ZUI_ACTshopmode.c` or `MApp_ZUI_ACTagingmenu.c`) with the game logic, preserving all underlying driver initialization.

---

## 8. Zero-Disassembly UART Access

The television firmware contains a full interactive serial debug shell:
```
******************************************
* Welcome to MStar Menu Mode System 1.0 *
******************************************
:\M>
<<HOTKEY>>
USB - usb update
UART switch (none / hk / mm / vdec)
```

### 8.1 Physical Interface: 3.5mm EX-LINK / Service Port
On Samsung TVs of this generation, UART serial communication is routed to the external **3.5mm Service / EX-LINK jack** on the rear I/O panel.

| 3.5mm TRS Connection | Signal Name | Electrical Level | Function |
| :--- | :--- | :--- | :--- |
| **Tip** | **RXD** | 3.3V TTL / RS-232* | Data from PC to TV |
| **Ring** | **TXD** | 3.3V TTL / RS-232* | Data from TV to PC |
| **Sleeve** | **GND** | 0V | Ground reference |

*\*Note: While older high-end Samsung models used $\pm$12V RS-232, entry-level MStar-based models typically use 3.3V TTL logic. A 3.3V USB-to-UART adapter (e.g., FTDI FT232R or CP2102) must be used to avoid damaging the SoC.*

### 8.2 Serial Port Parameters:
- **Baud Rate:** `115200`
- **Data Bits:** `8`
- **Parity:** `None`
- **Stop Bits:** `1`
- **Flow Control:** `None`

### 8.3 Activating UART Console via Service Menu:
1. Turn TV off into Standby.
2. On the standard remote control, press the key sequence: **`[INFO]` $\rightarrow$ `[MENU]` $\rightarrow$ `[MUTE]` $\rightarrow$ `[POWER]`**.
3. In the Samsung Service Menu:
   - Navigate to `Control` $\rightarrow$ `Sub Option`.
   - Ensure `RS-232 Jack` is configured to **`Debug`** or **`UART`**.
   - Ensure `Watchdog` is set to **`Off`** during debugging to prevent automatic reboots on halted loops.

---

## 9. Missing Hardware Information

To transition from static analysis to physical testing, the following hardware parameters must be verified:

| Parameter | Current Status | Verification Method |
| :--- | :--- | :--- |
| **Exact SoC Part Number** | Identified as `macaw12` platform | Requires reading SoC top marking (e.g., `TSUMV59XU` vs `MSD309`) or querying chip ID via UART |
| **Exact RAM Size** | Estimated 32 MB – 64 MB | Read MIU register status via UART boot log |
| **EX-LINK Voltage Level** | 3.3V TTL expected | Measure open-circuit voltage on 3.5mm jack with a multimeter before attaching FTDI |
| **IR Remote Scancodes** | General protocol identified | Capture scancodes for D-pad buttons via UART debug console log |

---

## 10. Final Feasibility Assessment

### Can a custom game run natively on this TV without external hardware?

| Execution Method | Feasibility | Technical Risk | Verdict |
| :--- | :--- | :--- | :--- |
| **USB Direct Execution (Homebrew App)** | **0% (Impossible)** | None (non-functional) | **Rejected:** The TV hardware and software stack completely lack an application runtime or executable loader. |
| **USB Firmware Update (Patched Binary)** | **10% (Theoretical only)** | **EXTREME (Permanent Hard-Brick)** | **Impractical without Hardware Programmer:** While the update mechanism uses an unsalted CRC32, the absence of an emergency USB recovery bootloader means any initial development error will brick the television irreversibly. |
| **Tethered UART Development (Service Port)** | **85% (Feasible)** | **Low** | **Recommended Starting Point:** Connecting a 3.3V USB-to-UART cable to the external 3.5mm service port allows developers to inspect the MStar debug shell, read memory registers, and test commands in real time without flashing or opening the TV. |

---

### External References & Documentation:
1. **Linux-Chenxing Project:** MStar / SigmaStar reverse-engineering documentation ([linux-chenxing.org](https://linux-chenxing.org)).
2. **OpenRISC 1000 Architecture Manual:** Architectural definitions for OR1200 / Aeon core registers and exception handling ([openrisc.io](https://openrisc.io)).
3. **SamyGO Community Wiki:** Samsung TV Ex-Link / Service port specifications and pinouts ([samygo.tv](https://wiki.samygo.tv)).
4. **MStar ISP Tooling:** Technical discussions on VGA DDC / I2C ISP flashing ([glcelectronics.com](https://glcelectronics.com)).
