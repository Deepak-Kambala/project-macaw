# Project Macaw — Samsung TV Firmware Reverse Engineering & Homebrew Research

Reverse engineering, architectural reconstruction, and host-side execution research targeting the **Samsung UA23H4003AR** television (Chassis `U8BA`, Firmware: `T-MXL0MASC-1040.0`).

---

## ⚠️ FINAL STRICT DECISION & SAFETY VERDICT

> ### **VERDICT: BETTER TO LEAVE UNTOUCHED — DO NOT FLASH OR UPDATE MODIFIED FIRMWARE**
> 
> **Decision:** **DO NOT ATTEMPT TO FLASH MODIFIED FIRMWARE VIA USB OR WRITE TO THE PHYSICAL TELEVISION STORAGE.**  
> Under current hardware conditions, attempting a modified USB firmware update or direct SPI write carries a **near 100% probability of permanently bricking the television (hard brick)**.  
> All custom code, reverse engineering, and game experimentation (including the Snake prototype) must remain **strictly confined to host-side simulation and the Aeon R2 emulator**.

### Why It Is Not Safe to Update (5 Critical Blockers):

1. **Absence of Emergency Recovery Fallback:**  
   The TV's bootloader (`0x000100` in SPI flash) contains no secondary recovery ROM, no dual-boot partition, and no documented emergency USB recovery key combination. If modified code crashes before the USB subsystem is brought up, the television is permanently unbootable.
2. **Strict Hardware Watchdog Interlocking (`0xA0006010`):**  
   The MStar Macaw12 SoC implements a hardware watchdog counter at MMIO `0xA0006010`. The main application superloop (`MApp_ZUI_Main`) must continuously strobe this counter. Any custom routine, unhandled exception, or blocking game loop will trigger an automatic hardware reboot within ~1.5 seconds, entering an infinite boot-loop.
3. **No Verified Hardware Debug Console (UART):**  
   The external 3.5 mm jack is verified to be analog audio output, **not** service UART. The internal UART test pads on the BN41-02104A/B mainboard have not been physically probed or verified with a logic analyzer. Without an active serial console, there is zero visibility into bootloader panics, exception dumps, or register state.
4. **No Physical SPI Flash Backup:**  
   The physical Winbond W25Q32 (4 MB SPI NOR) chip has not been dumped via an external hardware programmer (e.g., CH341A with SOIC8 test clip). Without a verified external dump, there is no way to restore corrupted flash memory.
5. **Multi-Stage Boot & Partition Checksums:**  
   The bootloader verifies flash chunk headers and CRC32 tables before executing payload decompression from `0x023880` to DRAM `0x80000000`. Altering binary payloads in flash alters checksums and breaks boot decompression.

### What Would Be Required Before Physical Execution is Ever Considered?
Physical code execution should **only** be reconsidered if all the following conditions are met:
- [ ] A full physical SPI flash backup is dumped and verified using an external programmer (e.g. CH341A / Pomona 5250 clip).
- [ ] Internal 3.3V UART test pads on the BN41-02104A/B PCB are identified, soldered, and confirmed to capture live serial bootlogs.
- [ ] The bootloader command prompt (MStar `<< MStar >>#` console) is accessible over UART to halt booting and load code into DRAM via serial/XMODEM without flashing SPI NOR flash.

Until those hardware milestones are achieved, **the device must be left alone in its factory state**.

---

## Hardware & Environment Specifications

- **Target Device:** Samsung UA23H4003AR (Series 4 LED Non-Smart TV)
- **Chassis:** U8BA
- **Mainboard:** High_X12_DVB_NonSmart (`BN41-02104A/B`)
- **System-on-Chip (SoC):** MStar Macaw12 / MSD6306 family
- **CPU Architecture:** 
  - Primary Core: **MStar Aeon R2** (32-bit OpenRISC-derived core, mixed 16/24/32-bit variable-length ISA)
  - Secondary Core: **MStar PM Coprocessor** (Standby & IR management)
- **Display Panel:** 23.6-inch LCD panel, native resolution **1366 × 768** (WXGA)
- **OS Platform:** MStar Utopia Bare-Metal RTOS (`"not enable MSOS_TYPE_LINUX"`)
- **Flash ROM:** Winbond W25Q32 (4 MB SPI NOR Flash)
- **Firmware Image:** `T-MXL0MASC.bin` (v1040.0, SHA-256: `f02cbf9ecf87087ea85826584cc9ad949b13d1ff404b1fe8888323b0f4ed52d5`)

---

## Project Macaw Milestones Summary

| Milestone | Scope & Core Objective | Key Deliverables & Achievements | Status |
| :---: | :--- | :--- | :---: |
| **Milestone 1** | Binary structure & format static analysis | Confirmed MStar Macaw12 / Aeon RISC32; established that no USB userland shell exists. | **COMPLETED** |
| **Milestone 2** | Native code feasibility & architecture | Identified 32-bit virtual memory layout, Utopia C runtime, and Winbond SPI flash layout. | **COMPLETED** |
| **Milestone 3** | Hardware verification & safety boundaries | Proved 3.5mm jack is Audio Out (not UART); established strict read-only hardware policy. | **COMPLETED** |
| **Milestone 4** | Firmware reverse engineering & UI mapping | Identified `MDrv_GE_*` graphics blitter APIs, `MApp_ZUI_*` window procedures, and IR keycodes. | **COMPLETED** |
| **Milestone 5** | Aeon R2 ISA validation & mini-assembler | Validated mixed-width instruction model (16b/24b/32b) against `shinyquagsire23/ghidra-aeon`. | **COMPLETED** |
| **Milestone 6** | Independent emulator & Snake prototype | Built modular Aeon R2 emulator; executed verified 31-byte program; built MockGE Snake prototype. | **COMPLETED** |
| **Milestone 7** | Runtime reconstruction & real-code emulation | Reconstructed full boot chain, memory map, timers, and IR dispatch; **executed real TV firmware routines** on emulator with 100% accuracy. | **COMPLETED** |

---

## Host-Side Proof-of-Concept Implementations

### 1. Real Firmware Routine Emulation (`poc/firmware-routine-emulation/`)
Carved genuine machine code directly from the TV firmware binary (`Samsung-TV-Homebrew/analysis/decompressed_main.bin`) and executed on the host-side Aeon R2 emulator:
- **Routine 1 (`0x005177`, 13 bytes, 5 instructions):** Halfword Array Element Lookup / Extractor (`bn.slli`, `bt.add`, `bn.lh`, `bn.extbz`, `bt.jr`).
- **Routine 2 (`0x0016E1`, 38 bytes, 14 instructions):** 15-Byte Memory Buffer Copy Loop with branch looping (`bg.bnei`) and stack frame deallocation.
- Verified across multiple input test vectors with **100% bit-for-bit agreement** against independent reference models.
```bash
python3 poc/firmware-routine-emulation/run_routine.py
python3 -m unittest discover -s poc/firmware-routine-emulation/tests
```

### 2. Modular Aeon R2 Emulator (`poc/aeon-r2-emulator/`)
Host-side Python CPU emulator implementing Aeon R2 register bank, linear memory controller, instruction decoder, and execution tracer.
```bash
python3 -m unittest discover -s poc/aeon-r2-emulator/tests
```

### 3. Snake Engine & MockGE Graphics Prototype (`poc/snake-host/`)
Decoupled game engine operating on numeric coordinate models, rendering to a 1280x720 framebuffer via MStar-compatible `MockGE` blitter primitives:
```bash
python3 poc/snake-host/integration_demo.py
python3 -m unittest discover -s poc/snake-host/tests
```

---

## Key Milestone Reports

- **Milestone 7 Final Report:** [reports/milestone7_final_report.md](reports/milestone7_final_report.md)
- **Real Firmware Code Execution:** [reports/milestone7_real_code_execution.md](reports/milestone7_real_code_execution.md)
- **Snake Integration Readiness:** [reports/milestone7_snake_integration_readiness.md](reports/milestone7_snake_integration_readiness.md)
- **Firmware Entry Point Analysis:** [research/milestone7/firmware_entry_analysis.md](research/milestone7/firmware_entry_analysis.md)
- **Memory Map Reconstruction:** [research/milestone7/memory_map.md](research/milestone7/memory_map.md)
- **Timer & Scheduler Analysis:** [reports/milestone7_timer_scheduler_analysis.md](reports/milestone7_timer_scheduler_analysis.md)
- **Graphics Subsystem Runtime Analysis:** [research/milestone7/graphics_runtime_analysis.md](research/milestone7/graphics_runtime_analysis.md)
- **Remote Input Dispatch Analysis:** [reports/milestone7_input_dispatch_analysis.md](reports/milestone7_input_dispatch_analysis.md)
- **Initial Firmware Static Analysis (Milestone 1):** [reports/firmware-analysis.md](reports/firmware-analysis.md)

---

## Firmware Artifact Integrity

Both original firmware binaries remain strictly preserved and unmodified:

| File Artifact | Baseline SHA-256 Hash |
| :--- | :--- |
| `firmware/T-MXL0MASC.bin` | `f02cbf9ecf87087ea85826584cc9ad949b13d1ff404b1fe8888323b0f4ed52d5` |
| `analysis/decompressed_main.bin` | `a7acb484039d43e045e9839a61c693ed6e621484fbf23e384ac33cc0b7ec5884` |
