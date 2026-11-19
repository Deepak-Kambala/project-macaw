# Project Macaw — Milestone 7 Final Report
## Firmware Runtime Reconstruction and Real-Code Emulation

**Target Hardware:** Samsung UA23H4003ARLXL  
**Chassis:** U8BA  
**Mainboard:** High_X12_DVB_NonSmart (BN41-02104A/B)  
**SoC:** MStar Macaw12 / MSD6306 family  
**CPU Core:** MStar Aeon R2 (32-bit OpenRISC-derived core)  
**Binary Artifacts:** `firmware/T-MXL0MASC.bin` & `analysis/decompressed_main.bin`  
**Git Branch:** `milestone-7-runtime-reconstruction`  
**Date:** November 2026  

---

## 1. Executive Summary & Core Mission

Milestone 7 achieved the most significant technical breakthrough of Project Macaw to date: **reconstructing the television firmware's full execution runtime and achieving bit-for-bit reproducible execution of real television firmware code inside an independent host-side Aeon R2 emulator**.

Rather than relying on synthetic hand-written test sequences, Milestone 7:
1. Reconstructed the complete boot chain from the hardware power-on reset vector (`0x000100` in flash) to the Utopia main application entry (`0x80000200` in DRAM).
2. Established an itemized 32-bit virtual and physical memory map across KSEG0, KSEG1, SRAM, and peripheral MMIO.
3. Uncovered the cooperative superloop scheduling model (`MApp_ZUI_Main.c`), software timer callback registry (`timer_cb/timer_cb.c`), and hardware watchdog timer (`0xA0006010`).
4. Reconstructed the 2D blitter graphics engine (`MDrv_GE_*`) and display output pipeline (`MDrv_GOP_*`) including double buffering (`dcMain`/`dcBuff`) and 720p-to-1366x768 panel upscaling.
5. Traced the remote-control input pipeline from 38 kHz physical IR carrier demodulation through RIU MMIO registers to the ZUI active window event dispatcher.
6. Expanded the host-side Aeon R2 emulator (`poc/aeon-r2-emulator/`) with six instructions (`bn.slli`, `bn.lh`, `bn.exthz`, `bn.extbz`, `bn.lbz`, `bn.sbz`) and resolved a subtle branch displacement rule in mixed-width ISAs.
7. Carved two genuine machine code routines directly from the TV firmware binary (`0x005177`, 13 bytes; `0x0016E1`, 38 bytes), executing both across multiple test vectors with 100% agreement against independent reference models.
8. Rigorously re-evaluated native Snake integration readiness, proving why firmware patching remains dangerous without physical hardware recovery.

---

## 2. Baseline Audit & Pre-Milestone Verification

Before executing new analysis, all artifacts and claims from Milestones 1–6 were audited against inspectable repository artifacts:

| Previous Finding / Claim | Milestone 6 Audit Status | Milestone 7 Independent Audit | Evidence Classification |
| :--- | :--- | :--- | :---: |
| **SoC Platform:** MStar Macaw12 | Strongly supported | Confirmed via MMIO peripherals, Utopia strings, and board markings | **CONFIRMED** |
| **CPU Architecture:** Aeon R2 | Verified | Confirmed via `shinyquagsire23/ghidra-aeon` and real firmware decoding | **CONFIRMED** |
| **Instruction Widths:** 16b / 24b / 32b | Verified | Confirmed by continuous multi-instruction decoding of firmware segments | **CONFIRMED** |
| **31-Byte Program Execution** | Verified | Verified on host emulator in Milestone 6 | **CONFIRMED** |
| **GE Graphics Functions Present** | Partially verified | Full API strings and assertions identified in `decompressed_main.bin` | **CONFIRMED** |
| **IR Scan-Code Strings Present** | Partially verified | Reconstructed via `IR_RATE` MMIO and `msKeypad` driver | **CONFIRMED** |
| **Direct USB Native Code Execution** | Unverified / Unsupported | Confirmed non-existent (media player only) | **INCORRECT** |
| **Firmware Recovery Mechanism** | Unverified | No emergency USB recovery key combo identified; SPI write risky | **UNVERIFIED** |

---

## 3. Firmware Execution Entry Point & Startup Sequence

By disassembling the initial reset vector and analyzing binary headers, Milestone 7 reconstructed the **complete 4-stage boot chain**:

```mermaid
flowchart TD
    A["Hardware Power-On / Reset Vector\n(T-MXL0MASC.bin @ 0x000100)"] -->|"Initialize Cache & RIU MMIO"| B["CPU Core & Memory Controller Init\n(@ 0x000100 - 0x0001a9)"]
    B -->|"Clear Bootloader BSS (0xB0000000..0xB0000910)"| C["BSS Zeroing Loop\n(@ 0x0001aa - 0x0001c7)"]
    C -->|"Set r1 = 0xB0000FE8 (SRAM Stack)"| D["Stack Pointer Setup\n(@ 0x0001c8 - 0x0001d7)"]
    D -->|"bg.j +7987"| E["Bootloader C main()\n(@ 0x002106)"]
    E -->|"Verify SPI Header at 0x020000\nRead Chunk Table at 0x021180"| F["Payload Decompression Engine\n(Deflate Stream @ 0x023880)"]
    F -->|"Decompress 1,610,021 Bytes to DRAM @ 0x80000000"| G["DRAM Application Image\n(3,103,664 Bytes in KSEG0)"]
    G -->|"bg.jr 0x80000200 (Header Entry Point)"| H["Utopia Application Runtime Entry\n(decompressed_main.bin @ 0x000200)"]
```

- **Stage 1 (Hardware Reset):** Direct execution from SPI NOR at `0x00000100`. Enables instruction cache via SPR `0x8` and configures Memory Interface Unit registers at MMIO `0xA0200400`.
- **Stage 2 (SRAM Environment):** Clears bootloader BSS in on-chip SRAM (`0xB0000000`–`0xB0000910`) and initializes stack pointer `r1 = 0xB0000FE8` (aligned with `~3` in delay slot).
- **Stage 3 (Bootloader C Runtime):** Jumps to `0x002106`, initializes watchdog timer (`0xA0006010`), sets up UART (`0xA0203D41`), verifies partition table, and reads the Deflate compressed application chunk starting at `0x023880`.
- **Stage 4 (Utopia Runtime Entry):** Decompresses 1,610,021 bytes to DRAM `0x80000000`. Header at flash offset `0x020000` specifies entry vector `0x80000200` (`80 00 02 00`), jumping to Utopia application initialization.

---

## 4. Complete Memory Map Reconstruction

The television firmware implements a MIPS/OpenRISC-style 32-bit segmented virtual memory architecture:

| Memory Region | Virtual Address Range | Size | Description | Confidence |
| :--- | :--- | :---: | :--- | :---: |
| **Bootloader Code (NOR)** | `0x00000100` – `0x00010000` | ~64 KB | Direct-mapped SPI flash execution | **CONFIRMED** |
| **Bootloader SRAM Stack/BSS** | `0xB0000000` – `0xB0000FFF` | 4 KB | On-chip SRAM before DRAM initialization | **CONFIRMED** |
| **Main App Code (`.text`)** | `0x80000200` – `0x80150000` | ~1.31 MB | Executable application code in cached DRAM | **CONFIRMED** |
| **Read-Only Data (`.rodata`)** | `0x80150000` – `0x80190000` | 256 KB | Strings, assertions, lookup tables | **CONFIRMED** |
| **Initialized Data (`.data`)** | `0x80190000` – `0x802F5BB0` | ~1.40 MB | UI state, fonts, graphics context | **CONFIRMED** |
| **Application Heap / Pools** | `0x80350000` – `0x82000000` | ~28.7 MB | `MsOS_AllocateMemory` pool | **STRONGLY SUPPORTED** |
| **GOP Display Framebuffers** | `0x8C000000` – `0x8D000000` | ~16 MB | Double-buffered 720p OSD framebuffers | **STRONGLY SUPPORTED** |
| **RIU Peripheral MMIO** | `0xA0200000` – `0xA020FFFF` | 64 KB | Hardware controllers, IR, UART, MIU | **CONFIRMED** |
| **Watchdog / Timer MMIO** | `0xA0006000` – `0xA00060FF` | 256 B | Watchdog reset & timer tick counters | **CONFIRMED** |

---

## 5. Timer & Scheduling Subsystem Reconstruction

- **Architecture:** Non-preemptive cooperative superloop (`tv-ap/dvb/ui2_M10/MApp_ZUI_Main.c`).
- **Callback Table:** Fixed-capacity static array in `timer_cb/timer_cb.c`. Emits assertion `"Not enough buffer to attach timerCB!!!!!"` when table capacity is exceeded.
- **Hardware Watchdog:** Hardware counter at MMIO `0xA0006010` must be serviced continuously to prevent SoC reboot. Any custom subroutine blocking longer than ~1.5 seconds triggers a hardware reboot.

---

## 6. Graphics Subsystem Runtime Analysis (GE & GOP)

- **2D Blitter (GE):** Hardware acceleration engine providing `MDrv_GE_FillRect`, `MDrv_GE_DrawLine`, `MDrv_GE_BitBltEX`, and clipping window support (`MDrv_GE_SetClipWindow`). Driven via a hardware FIFO command queue (`VCMQ`).
- **Compositor (GOP):** Reads pixel planes out of MIU DRAM via DMA windows (GWIN). Supports 1280x720 internal rendering stretched to the native 1366x768 panel using polyphase filtering.
- **Double Buffering:** Maintained through two distinct contexts: `dcMain` (front scan-out buffer) and `dcBuff` (back drawing buffer). Screen tearing is avoided by synchronizing buffer swaps with V-Sync (`MDrv_GOP_GWIN_WaitVsync`).

---

## 7. Remote Input Pipeline & IR Event Dispatch

- **Demodulation:** Physical 38 kHz NEC-format infrared signals are sampled by the MStar IR pulse engine configured via `IR_RATE` registers (`0xA0203D41`).
- **Driver Queue:** `msKeypad_Init` manages scan-code buffering under mutex protection (`OS_KEYPAD_Mutex`).
- **Keycode Translation:** Raw scan codes (`IR:%02dh`) are mapped to logical keys (`KEY_UP=0x0001`, `KEY_DOWN=0x0002`, `KEY_LEFT=0x0003`, `KEY_RIGHT=0x0004`, `KEY_ENTER=0x0005`, `KEY_EXIT=0x0006`).
- **ZUI Window Dispatch:** Key events are dispatched to active dialog window procedures (`_eActiveOSD`).

---

## 8. Aeon R2 Instruction Set Extensions

The Aeon R2 emulator (`poc/aeon-r2-emulator/`) was expanded to support the instructions required by extracted firmware routines:

| Instruction | Format | Length | Opcode | Description | Reference in Ghidra-Aeon |
| :--- | :---: | :---: | :---: | :--- | :--- |
| **`bn.slli`** | 24-bit | 3 bytes | `0x13` | Shift left logical immediate (`rD = rA << imm`) | `aeon_ORBIS32.sinc:329` |
| **`bn.lh`** | 24-bit | 3 bytes | `0x02` | Load unsigned 16-bit halfword with even alignment | `aeon_ORBIS32.sinc:201` |
| **`bn.exthz`** | 24-bit | 3 bytes | `0x17` | Zero-extend 16-bit halfword (`rD = rA & 0xFFFF`) | `aeon_ORBIS32.sinc:348` |
| **`bn.extbz`** | 24-bit | 3 bytes | `0x17` | Zero-extend 8-bit byte (`rD = rA & 0xFF`) | `aeon_ORBIS32.sinc:346` |
| **`bn.lbz`** | 24-bit | 3 bytes | `0x04` | Load unsigned 8-bit byte (`rD = *addr`) | `aeon_ORBIS32.sinc:212` |
| **`bn.sbz`** | 24-bit | 3 bytes | `0x06` | Store 8-bit byte (`*addr = rD & 0xFF`) | `aeon_ORBIS32.sinc:215` |

---

## 9. Critical Architectural Discovery: Branch Displacements in Aeon R2

During Routine 2 emulation, a critical architectural rule was discovered:
- In standard 32-bit RISC ISAs (OpenRISC OR1K, MIPS), branch immediates represent instruction words or halfwords ($rel \times 4$ or $rel \times 2$).
- In MStar Aeon R2, variable-length instructions (16, 24, and 32 bits) permit odd-byte instruction lengths (24-bit / 3-byte).
- Consequently, 32-bit conditional branch displacements (`bg.bnei`, `bg.beqi`) represent **direct byte offsets** ($PC + rel$), with no multiplication factor.
- Resolving this discrepancy allowed the 15-iteration loop in Routine 2 to branch accurately back to the loop header (`0x0016EB`).

---

## 10. Real Firmware Routine Extraction (`extract_routine.py`)

Using `poc/firmware-routine-emulation/extract_routine.py`, two routines were carved directly from `decompressed_main.bin`:
1. `routine1_array_lookup.bin`: 13 bytes from offset `0x005177`.
   - Hex: `4ce4088ce308e7015c67008529`
   - SHA-256: `488c210cbec62a9fa1260eb7f1896791d09e8636ba2bbf9ef9d5e38d7bb680ee`
2. `routine2_mem_copy.bin`: 38 bytes from offset `0x0016E1`.
   - Hex: `98c0c0e00a61fc879b2640e53410e70018e4009cc19c81d0cfff9e98e188670d21029c248529`
   - SHA-256: `46c4e466d38a549c4fae3b33df1796191b794d07ff67db43ce2bb97f8c1f0b0c`

All extracted artifacts and metadata are recorded in `routine_metadata.json`.

---

## 11. Real Firmware Routine Emulation (`run_routine.py`)

`run_routine.py` executes both extracted binary routines under strict CPU state harnesses:
- **Routine 1 (Array Lookup):**
  - Sets up array in memory, configures `r3` (base) and `r4` (index), executes 5 instructions, verifies return value in `r3`.
- **Routine 2 (Memory Copy Loop):**
  - Configures `r5` (source), stack frame `r1` with saved link register sentinel, executes 98 instructions (15 loop iterations), verifies 15 bytes written to destination buffer `0x00529B26`, verifies return value `r3 = 1`, and verifies stack pointer deallocated by 4 bytes.

---

## 12. Test Results & Multi-Input Verification Matrix

### Routine 1 Execution Results
| Test | Table Elements | Index | Expected | Emulated | Result |
| :---: | :--- | :---: | :---: | :---: | :---: |
| 1 | `[0x1234, 0x5678, 0xABCD, 0x00FF, 0xA055]` | 0 | `0x34` | `0x34` | **PASS (5 steps)** |
| 2 | `[0x1234, 0x5678, 0xABCD, 0x00FF, 0xA055]` | 1 | `0x78` | `0x78` | **PASS (5 steps)** |
| 3 | `[0x1234, 0x5678, 0xABCD, 0x00FF, 0xA055]` | 2 | `0xCD` | `0xCD` | **PASS (5 steps)** |
| 4 | `[0x1234, 0x5678, 0xABCD, 0x00FF, 0xA055]` | 3 | `0xFF` | `0xFF` | **PASS (5 steps)** |
| 5 | `[0x1234, 0x5678, 0xABCD, 0x00FF, 0xA055]` | 4 | `0x55` | `0x55` | **PASS (5 steps)** |
| 6 | `[0x0000, 0xFFFF, 0x0102, 0x0408, 0x1020]` | 1 | `0xFF` | `0xFF` | **PASS (5 steps)** |
| 7 | `[0x0000, 0xFFFF, 0x0102, 0x0408, 0x1020]` | 3 | `0x08` | `0x08` | **PASS (5 steps)** |

### Routine 2 Execution Results
| Test | Source Data (15 Bytes) | Status Return | SP Popped | Memory at `0x00529B26` | Result |
| :---: | :--- | :---: | :---: | :---: | :---: |
| 1 | `"Hello Samsung!!"` | `1` | $+4$ bytes | `48656c6c6f2053616d73756e672121` | **PASS (98 steps)** |
| 2 | `00 11 22 33 44 55 66 77 88 99 AA BB CC DD EE` | `1` | $+4$ bytes | `00112233445566778899aabbccddee` | **PASS (98 steps)** |
| 3 | `AA AA AA AA AA AA AA AA AA AA AA AA AA AA AA` | `1` | $+4$ bytes | `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` | **PASS (98 steps)** |
| 4 | `00 FF 55 AA 00 FF 55 AA 00 FF 55 AA 11 22 33` | `1` | $+4$ bytes | `00ff55aa00ff55aa00ff55aa112233` | **PASS (98 steps)** |
| 5 | `"Project Macaw12"` | `1` | $+4$ bytes | `50726f6a656374204d616361773132` | **PASS (98 steps)** |

---

## 13. Negative Counter-Example Testing

To verify the test suite's discriminative ability:
- Unit test `test_counter_example_failed_branch_assumption` in `test_real_routine.py` introduces the false halfword-scaling assumption ($rel \times 2 = -26$).
- The test demonstrates that this false assumption calculates loop target $+23 - 26 = -3$, crashing out of bounds.
- The test proves mathematically that only the validated byte displacement ($rel = -13$, target $+23 - 13 = 10$) satisfies the firmware's control-flow graph.

---

## 14. Snake Integration Readiness & Hardware Barriers

| Requirement | Host Status | TV Firmware Reality | Feasibility Verdict |
| :--- | :--- | :--- | :--- |
| **Game Loop** | Independent grid logic (`snake_sim.py`) | Cooperative superloop (`MApp_ZUI_Main`) | Ready for host simulation |
| **Graphics** | `MockGE.fill_rect` in framebuffer | `MDrv_GE_FillRect` hardware blitter | Identical API surface |
| **Input** | Keyboard arrows | NEC IR scan codes (`KEY_UP`..`ENTER`) | Direct 1:1 mapping |
| **Flashing / Execution** | Host Python | Winbond W25Q32 flash, unverified UART | **STRICTLY PROHIBITED** |

**Conclusion:** Snake logic is completely decoupled and technically compatible with MStar GE blitter APIs. However, **flashing or modifying TV firmware remains unacceptable** due to boot integrity checks, watchdog timeouts, and the total absence of a verified recovery fallback.

---

## 15. Safety Boundaries & Hash Integrity Audit

All Milestone 7 work was strictly confined to host-side static analysis, firmware slicing, and emulator execution. Zero hardware connections, zero flash modifications, and zero SPI writes occurred.

### SHA-256 Hash Verification:
| File Artifact | Baseline Hash (Milestone 1) | Post-Milestone 7 Hash | Integrity Status |
| :--- | :--- | :--- | :---: |
| `firmware/T-MXL0MASC.bin` | `f02cbf9ecf87087ea85826584cc9ad949b13d1ff404b1fe8888323b0f4ed52d5` | `f02cbf9ecf87087ea85826584cc9ad949b13d1ff404b1fe8888323b0f4ed52d5` | **IDENTICAL (UNCHANGED)** |
| `analysis/decompressed_main.bin` | `a7acb484039d43e045e9839a61c693ed6e621484fbf23e384ac33cc0b7ec5884` | `a7acb484039d43e045e9839a61c693ed6e621484fbf23e384ac33cc0b7ec5884` | **IDENTICAL (UNCHANGED)** |

---

## 16. Recommendations for Milestone 8

1. **Physical Hardware Inspection:** Conduct non-destructive physical inspection of the television chassis and mainboard (BN41-02104A/B) to locate and multimeter-test the internal debug UART header.
2. **Read-Only UART Capture:** Connect a 3.3V USB-to-UART adapter to the verified test pads to record the live boot log during normal television power-up.
3. **SPI Flash Backup:** Read and preserve a physical dump of the Winbond W25Q32 chip using an external clip/programmer before any write attempts are ever considered.
4. **Toolchain Compilation Pipeline:** Investigate cross-compilation of C code to Aeon R2 machine code using OpenRISC GCC or Clang targeting the emulator first.
