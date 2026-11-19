# Milestone 7: Baseline Audit Report

**Project:** Project Macaw (Samsung UA23H4003ARLXL / MStar Macaw12 / Aeon R2)  
**Audit Target:** Milestone 6 emulator, tests, mock graphics, research notes, and binary address space mappings  
**Starting Commit:** `e5fbbaa` (`milestone-6-aeon-emulator`)  
**Audit Date:** November 2026  

---

## 1. Executive Summary

Milestone 7 transitions Project Macaw from synthetic test workloads to **reproducible execution of real routines extracted directly from the original Samsung television firmware**.

Before executing extracted binary routines, this audit evaluates the Milestone 6 emulator, test suite, and address space models against ground truth.

### Primary Audit Findings:
1. **Emulator Soundness:** The Milestone 6 modular emulator (`poc/aeon-r2-emulator/`) is verified correct for its supported instruction subset (10/10 automated tests passing). It enforces Big-Endian byte ordering, unsigned 32-bit arithmetic wrapping, and strict zero-latching on `r0`.
2. **Address Space Confusion Clarified:** Prior milestones occasionally blurred the distinction between firmware file offsets, decompressed offsets, and CPU virtual addresses. This audit establishes strict mathematical boundaries between these 4 address spaces.
3. **Firmware Entry Point Discovered:** Analysis of the bootloader startup code at `0x000100` in `T-MXL0MASC.bin` revealed the complete early initialization sequence: cache invalidation, BSS clearing at `0xB0000000`–`0xB0000910`, stack pointer initialization at `0xB0000FE8`, and a branch (`bg.j +7987`) to bootloader `main()` at file offset `0x002106`.
4. **Main Application Entry Address Verified:** The header at file offset `0x020000` specifies `0x80000200` as the KSEG0 entry point for the decompressed Utopia application (`decompressed_main.bin` offset `0x000200`).

---

## 2. Address Space Distinction Matrix

To avoid confusion during routine extraction and execution, all addresses are categorized into four distinct spaces:

| Address Space | Base / Scope | Example Address | Description |
| :--- | :--- | :--- | :--- |
| **Firmware File Offset** | `0x000000`–`0x3AC364` | `0x020000` | Raw byte offset inside `T-MXL0MASC.bin` on disk |
| **Decompressed Offset** | `0x000000`–`0x2F5BB0` | `0x000200` | Raw byte offset inside `decompressed_main.bin` |
| **CPU Virtual Address (KSEG0)** | `0x80000000`–`0x802F5BB0` | `0x80000200` | Cached DRAM mapping for application code & data |
| **CPU Virtual Address (KSEG1)** | `0xA0000000`–`0xAFFFFFFF` | `0xA0006010` | Uncached DRAM / MMIO mapping (DMA buffers, peripherals) |
| **Physical MMIO (RIU)** | `0xBF000000` / `0xA0200000` | `0xA0200400` | Register Interface Unit hardware peripheral registers |
| **Bootloader SRAM** | `0xB0000000`–`0xB0000FFF` | `0xB0000FE8` | 4KB internal SRAM used by bootloader stack & BSS |

$$\text{KSEG0 Virtual Address} = 0x80000000 + \text{Decompressed File Offset}$$

---

## 3. Comprehensive Itemized Audit

| Component | Previous Claim | Audit Finding | Classification | Evidence & Reproduction |
| :--- | :--- | :--- | :--- | :--- |
| **Aeon R2 Instruction Widths** | Top 3 bits determine 16/24/32-bit | Independently confirmed by Ghidra SLEIGH & MStar kernel `r2_backtrace.c` | **VERIFIED** | `scripts/milestone6/validate_assembler.py` |
| **Register Conventions** | `r1`=sp, `r2`=fp, `r9`=lr, `r3-r8`=args | Confirmed in hardware exception frame `0x020280` and bootloader stack setup | **VERIFIED** | `Samsung-TV-Homebrew/firmware/T-MXL0MASC.bin` at `0x0001c8` |
| **Endianness** | Big Endian throughout | Validated across multi-byte loads/stores in emulator and binary headers | **VERIFIED** | `poc/aeon-r2-emulator/tests/test_emulator.py` |
| **Bootloader Entry Point** | `0x000100` | `0x000100` is the reset vector; initializes cache/BSS and jumps to `0x002106` | **VERIFIED** | Disassembly from `0x000100` to `0x0001d3` |
| **Main App Entry Point** | `0x80000200` | Confirmed by header at `0x020000`; offset `0x000200` contains valid Utopia init calls | **VERIFIED** | Header bytes `80 00 02 00` at `0x020000` |
| **GE API Offsets (`0x17bd3e`)** | Executable entry points | Debunked in Milestone 6; confirmed as ASCII strings in `.rodata` | **INCORRECT (Previous)** / **VERIFIED (Corrected)** | `Samsung-TV-Homebrew/analysis/decompressed_main.bin` at `0x17bd3e` |
| **GOP Display Pipeline** | OSD Window subsystem | Verified via strings `MDrv_GOP_Init`, `HAL_GOP_SetDWINMIU`, `MDrv_GOP_GWIN_*` | **VERIFIED** | `.rodata` string search at `0x17da23` |
| **Timer / Scheduler Subsystem** | `MsOS_*` or RTOS timers | `timer_cb/timer_cb.c` provides periodic callback registration (`attach timerCB`) | **VERIFIED** | String `timer_cb/timer_cb.c` at `0x18e6b5` |
| **IR Input Pipeline** | Window procedure hook | Format strings confirm `u8WinProcID`, but callback function pointers unrecovered | **HYPOTHESIS** | Format string `u8WinProcID= %d \n` at `0x16ca03` |
| **Host-Side Snake Demo** | Clean decoupled simulation | Verified by `integration_demo.py` producing 675KB PPM bitmap frames | **VERIFIED** | `poc/snake-host/integration_demo.py` |

---

## 4. Firmware Hash Verification

| Artifact | SHA-256 Hash | Status |
| :--- | :--- | :--- |
| `Samsung-TV-Homebrew/firmware/T-MXL0MASC.bin` | `f02cbf9ecf87087ea85826584cc9ad949b13d1ff404b1fe8888323b0f4ed52d5` | Verified / Pristine |
| `Samsung-TV-Homebrew/analysis/decompressed_main.bin` | `a7acb484039d43e045e9839a61c693ed6e621484fbf23e384ac33cc0b7ec5884` | Verified / Pristine |
