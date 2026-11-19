# Firmware Memory Map Reconstruction

**Target Hardware:** Samsung UA23H4003ARLXL (Chassis U8BA, MStar Macaw12 Platform)  
**Processor Architecture:** MStar Aeon R2 (OpenRISC-derived 32-bit core)  
**Date:** November 2026  

---

## 1. Architectural Memory Space Structure

The MStar Macaw12 SoC implements a standard MIPS/OpenRISC-style 32-bit segmented memory architecture:
- **KSEG0 (`0x80000000` – `0x9FFFFFFF`, 512 MB):** Cached virtual memory mapped directly to physical DRAM starting at physical address `0x00000000`. Used for main application code (`.text`), read-only constants (`.rodata`), initialized globals (`.data`), and the runtime heap.
- **KSEG1 (`0xA0000000` – `0xBFFFFFFF`, 512 MB):** Uncached virtual memory mapped directly to physical DRAM or peripherals. Used for hardware DMA buffers, display framebuffers (GOP/GWIN), and Register Interface Unit (RIU) memory-mapped I/O.
- **Internal SRAM (`0xB0000000` – `0xB0000FFF`, 4 KB):** High-speed on-chip static RAM used exclusively by the bootloader for early stack allocation (`0xB0000FE8`) and boot BSS zeroing before external DRAM is trained.
- **Physical SPI NOR Flash (`0x00000000` – `0x003FFFFF`, 4 MB):** Winbond W25Q32 flash chip mapped to the external SPI bus controller.

---

## 2. Itemized Memory Region Matrix

| Memory Region | Virtual Start (Hex) | Virtual End (Hex) | Size | Region Type | Evidence Source | Confidence |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Bootloader Reset & Startup** | `0x00000100` | `0x00001FFF` | ~8 KB | Code (NOR) | Disassembly at `0x000100` | **CONFIRMED** |
| **Bootloader C Runtime** | `0x00002106` | `0x00010000` | ~56 KB | Code (NOR) | Branch at `0x0001d3` to `0x002106` | **CONFIRMED** |
| **Bootloader SRAM BSS** | `0xB0000000` | `0xB0000910` | 2,320 B | Writable BSS | Zeroing loop at `0x0001aa` | **CONFIRMED** |
| **Bootloader Initial Stack** | `0xB0000910` | `0xB0000FE8` | ~1.7 KB | Stack (SRAM) | Immediate at `0x0001c8` | **CONFIRMED** |
| **Main App Code (`.text`)** | `0x80000000` | `0x80150000` | ~1.31 MB | Executable Code | Decompressed main `0x000000`–`0x150000` | **CONFIRMED** |
| **Read-Only Data (`.rodata`)** | `0x80150000` | `0x80190000` | 256 KB | Read-Only Data | String tables, assertions, format strings | **CONFIRMED** |
| **Initialized Data (`.data`)** | `0x80190000` | `0x802F5BB0` | ~1.40 MB | Writable Data | UI tables, font bitmaps, OSD structures | **CONFIRMED** |
| **Application BSS (`.bss`)** | `0x802F5BB0` | `0x80350000` | ~360 KB | Zeroed RAM | Dynamic uninitialized globals | **STRONGLY SUPPORTED** |
| **Utopia Heap Memory** | `0x80350000` | `0x82000000` | ~28.7 MB | Dynamic Heap | `MsOS_AllocateMemory` pool | **STRONGLY SUPPORTED** |
| **GOP OSD Framebuffers** | `0x8C000000` | `0x8D000000` | ~16 MB | Display RAM | `HAL_GOP_SetDWINMIU`, double-buffered 720p | **STRONGLY SUPPORTED** |
| **RIU Peripheral MMIO** | `0xA0200000` | `0xA020FFFF` | 64 KB | Hardware Regs | MMIO immediate `0xA0200000` at `0x000107` | **CONFIRMED** |
| **Watchdog / Timer MMIO** | `0xA0006000` | `0xA00060FF` | 256 B | Timer Regs | Peripheral write at `0x002118` | **CONFIRMED** |

---

## 3. Linker Layout Formula

For any offset within `decompressed_main.bin`:
$$\text{KSEG0 Virtual Address} = 0x80000000 + \text{Offset}$$
$$\text{KSEG1 Uncached Mirror} = 0xA0000000 + \text{Offset}$$
$$\text{Physical DRAM Address} = \text{Virtual Address} \& 0x1FFFFFFF$$
