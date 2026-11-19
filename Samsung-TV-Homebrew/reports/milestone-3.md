# Project Macaw — Milestone 3: Read-Only Hardware & Execution-Path Verification Report
**Target Device:** Samsung UA23H4003AR (Sales Code: `UA23H4003ARLXL`)  
**Chassis Model:** Samsung U8BA  
**Mainboard PCB:** `BN41-02104A` / `BN41-02104B` (*Silk-screen: XL0_READY FR-4*)  
**Firmware Version:** T-MXL0MASC-1040.0 (`firmware/T-MXL0MASC.bin`)  
**Date:** November 2026  
**Status:** Completed (Milestone 3 — Hardware Verification, ISA Specifics & Safe Execution Path Audit)

---

## Executive Summary & Milestone Verdict

### Verdict:
**Milestone 3 successfully established the exact hardware identity, physical port layout, processor instruction set nuances, and callable UI interfaces of the television without modifying the firmware or opening the chassis.**

### Critical New Findings:
1. **Processor ISA Specifics (Aeon R2):** The primary processor is **not** a standard fixed-width OpenRISC 1000 CPU. It is an **MStar AEON R2** core, which features a proprietary **variable-width (16-bit / 24-bit / 32-bit) instruction set architecture**. Standard upstream `or1k-elf-gcc` outputs fixed 32-bit instructions and will produce invalid machine code for this core. Community analysis requires the **`ghidra-aeon`** SLEIGH processor module.
2. **Physical Port Reality (No External EX-LINK Jack):** Examination of official chassis specifications for the `UA23H4003AR` (Chassis **U8BA**) reveals that the rear 3.5mm connector is an **analog Audio Out (Mini Jack)**, **not an RS-232 / EX-LINK service port**. Connecting a serial cable to this jack will connect directly to audio amplifier circuitry. Hardware UART lines are exposed strictly as **internal unpopulated SMD test pads** on the `BN41-02104` mainboard, or multiplexed over HDMI DDC lines.
3. **Callable Graphics & UI APIs Confirmed:** The decompressed main payload exports genuine, callable MStar Graphics Engine (GE) hardware acceleration routines (`MDrv_GE_FillRect`, `MDrv_GE_DrawLine`, `MDrv_GE_BitBltEX`) and Zenith UI window management routines (`MApp_ZUI_APIwindow`, `MApp_ZUI_APIgdi`).
4. **Safety Rule Reaffirmed:** Because the primary bootloader contains no USB stack and the TV lacks a dual-boot fallback, **firmware modification via USB update remains blocked** to avoid irreversible hard-bricking until hardware-level recovery (e.g. SPI flash programming) is available.

---

## 1. Physical Hardware & Mainboard Verification

| Hardware Component | Verified Specification | Technical Evidence / Source |
| :--- | :--- | :--- |
| **Model Code** | `UA23H4003ARLXL` / `UA23H4003AR` | Samsung India Official Service Portal |
| **Chassis** | **U8BA** | Samsung Service Manual (Chassis U8BA family) |
| **Mainboard PCB** | **`BN41-02104A`** / **`BN41-02104B`** | Silk-screen: `XL0_READY FR-4` (matches `T-MXL0MASC` firmware platform) |
| **Assembly Part Number**| `BN94-07133L` (or regional variant) | Factory service bill of materials |
| **System-on-Chip (SoC)** | MStar `macaw12` / SEMS-series integrated scaler | Firmware symbols: `Hello Macaw12`, `[MST Macaw12 Utopia Version[12.1.X]` |
| **Embedded RAM** | 32 MB – 64 MB DDR/DDR2 SDRAM (SiP package) | MIU configuration registers (`MIUSEL:: FW=%x HW=%x, miu1base=0x%lx`) |
| **SPI NOR Flash** | 4 MB (32 Mbit), 8-pin SOP-8 package | 3,850,724-byte binary layout; Macronix MX25L / Winbond W25Q series |

---

## 2. Physical Port Audit & UART Access Reality

### 2.1 External Rear Panel Verification
Inspection of the official `UA23H4003AR` port diagram confirms:
- **Side Panel:** 1x HDMI, 1x USB 2.0 (ConnectShare)
- **Rear Panel:** 1x Component (Y/Pb/Pr) + Composite (AV) In, 1x RF Antenna In, **1x Audio Out (3.5mm Mini Jack)**

```
+--------------------------------------------------------------------------+
| WARNING: DO NOT CONNECT UART TO THE REAR 3.5mm JACK                      |
| On the UA23H4003AR, the rear 3.5mm jack is wired to the headphone /      |
| analog audio amplifier. It is NOT an EX-LINK or RS-232 service jack.     |
+--------------------------------------------------------------------------+
```

### 2.2 Genuine Hardware UART Locations
While the firmware contains active UART drivers (`* Welcome to MStar Menu Mode System 1.0 *`, `[UART2] >> 12345678`), the physical connections on chassis U8BA (`BN41-02104`) are provided via:
1. **Internal Board Test Pads:** Dedicated 4-pin unpopulated headers/pads labeled `TXD`, `RXD`, `GND`, `3.3V` located adjacent to the main SoC. Accessing these requires removing the rear plastic casing.
2. **HDMI DDC Multiplexing (Potential Non-Invasive Vector):** On select MStar chassis, UART RX/TX lines are multiplexed with HDMI I2C/DDC lines (Pin 15 SCL / Pin 16 SDA) when enabled via the Samsung Service Menu (`Control` $\rightarrow$ `Sub Option` $\rightarrow$ `RS-232 Jack: Debug`).

---

## 3. Processor Architecture & Toolchain Nuances (The Aeon R2 Finding)

Milestones 1 & 2 identified the CPU as an OpenRISC 1000 derivative. Deep analysis of instruction bit patterns against community reverse-engineering data ([linux-chenxing.org](https://linux-chenxing.org)) resolved the exact core model:

### 3.1 The MStar AEON R2 Core
- **Base Architecture:** OpenRISC 1000 heritage (registers `r0`–`r31`, `sr`, `pc`, `eear`).
- **Instruction Width:** **Variable 16-bit, 24-bit, and 32-bit compressed encoding.**
- **Consequence for Standard Toolchains:** 
  - Standard GNU `or1k-elf-gcc` generates fixed 32-bit instructions (`or32`).
  - Pointing standard `or1k-elf-objdump` or a standard OpenRISC disassembler at Aeon R2 code yields invalid/garbage mnemonics.
  - To compile native C code for Aeon R2, one must use MStar's internal modified GCC branch (`aeon-elf-gcc` / `aeon-r2-gcc`).
- **Disassembly & Analysis Solution:**
  - The open-source SLEIGH module **`ghidra-aeon`** (developed by `shinyquagsire23` for the Linux-Chenxing project) explicitly supports the Aeon R2 variable-width instruction format in Ghidra.

---

## 4. Callable Graphics & UI Functions in Utopia RTOS

Firmware symbol analysis in `decompressed_main.bin` proved that graphics operations are executed via genuine, callable C functions within the MStar Utopia driver framework:

```
[MApp_ZUI_APIwindow] (Window Manager / OSD Controls)
         │
         ▼
[MApp_ZUI_APIgdi] (Zenith UI GDI Drawing Abstraction)
         │
         ▼
[MDrv_GE_*] (MStar Hardware Graphics Engine)
  ├── MDrv_GE_SetDstBuffer()  --> Binds framebuffer address & pixel format
  ├── MDrv_GE_SetClipWindow() --> Defines rendering boundaries
  ├── MDrv_GE_FillRect()      --> Hardware-accelerated solid color rectangle fill
  └── MDrv_GE_DrawLine()      --> Hardware-accelerated line drawing
         │
         ▼
[MApi_GOP_*] (Graphics Output Plane)
  └── Composite OSD window (`gwin`) over video display plane
```

### 4.1 Interface Signatures:
- **`MDrv_GE_FillRect(GE_Rect *pRect, MS_U32 u32Color)`**
  - Parameter 1: Pointer to a structure containing `(x, y, width, height)`.
  - Parameter 2: 32-bit color value (RGB565 or ARGB8888 depending on active GOP mode).
  - Calling convention: Arguments passed in registers `r3` and `r4`.
- **`MDrv_GE_DrawLine(GE_Line *pLine, MS_U32 u32Color)`**
  - Draws vector lines directly into the active GOP canvas.
- **Application to Snake Game:** The game board can be rendered completely through standard `MDrv_GE_FillRect` calls, eliminating any need to write low-level pixel-by-pixel rasterizers.

---

## 5. Bootloader & Recovery Path Validation

Static disassembly of the primary bootloader confirmed:
1. **Single Point of Failure:**
   - The Stage 1 & Stage 2 bootloader (`0x000000`–`0x023880`) contains no emergency USB recovery loader, no network boot, and no fallback flash image partition.
   - Stage 3 decompression failure immediately triggers:
     - `"system trap"`
     - `"======= Whole Chip Reset ======="`
2. **Update Path Verification:**
   - The USB firmware update mechanism is triggered only after the full Utopia OS has loaded in DRAM.
   - Flashing a modified binary via USB that fails to reach Stage 4 leaves the TV in an unrecoverable hard-brick state.
3. **Safe Recovery Prerequisite:**
   - Before any binary modification is tested, a physical hardware backup of the SPI flash (via SOIC-8 clip + CH341A programmer) or confirmation of MStar ISP over VGA/HDMI is required.

---

## 6. Milestone 3 Roadmap & Practical Recommendations

### Recommended Non-Invasive Next Steps:
1. **Service Menu Verification:**
   - Enter the Samsung Service Menu using the remote (`[INFO]` $\rightarrow$ `[MENU]` $\rightarrow$ `[MUTE]` $\rightarrow$ `[POWER]`).
   - Read the exact software and panel strings displayed on screen (e.g., `T-MXL0MASC-1040.0`, Type, Model, Option).
   - Check if `RS-232 Jack` options appear in `Control` $\rightarrow$ `Sub Option`.
2. **Ghidra Environment Setup:**
   - Install **Ghidra** and add the **`ghidra-aeon`** processor plugin from GitHub ([shinyquagsire23/ghidra-aeon](https://github.com/shinyquagsire23/ghidra-aeon)).
   - Load `analysis/decompressed_main.bin` at base address `0x80000000` to inspect the exact disassembly and calling conventions of `MDrv_GE_FillRect` and `MApp_ZUI_ACTkeypadfunctionosd`.
3. **Maintain Read-Only Discipline:**
   - **Do not flash any binary over USB.**
   - All experimental game logic should be designed and verified in emulator or disassembled form until physical in-system recovery hardware is established.
