# Project Macaw — Technical References & Citations

Comprehensive bibliography of documentation, source repositories, hardware datasheets, standards specifications, and community research utilized throughout the reverse engineering, static analysis, architectural reconstruction, and emulation milestones of **Project Macaw** (Samsung UA23H4003AR, Platform `T-MXL0MASC-1040.0`).

---

## 1. Primary Hardware & Vendor Documentation

- **Samsung Electronics:**
  - *Official Product Support & Firmware Distribution: Samsung UA23H4003ARLXL*  
    URL: [samsung.com/in/support/model/UA23H4003ARLXL](https://www.samsung.com/in/support/model/UA23H4003ARLXL/)  
    *Usage:* Verified official baseline firmware package `T-MXL0MASC-1040.0`, product release timeline (2013–2014), and hardware specifications.
  - *Samsung Service Manual — Chassis U8BA / High_X12_DVB_NonSmart (Models: UA23H4003AR, UA28H4003AR, UA32EH4003R)*  
    Part Numbers: `BN41-02104A`, `BN41-02104B`, `BN94-07106A`  
    *Usage:* Identified mainboard PCB layout, power supply rails (32W AC 100–240V), tuner topology, display panel interface (LVDS to 1366x768 23.6-inch panel), and rear connector pinouts (confirming the 3.5 mm jack is dedicated analog Audio Out, not service UART).

- **Winbond Electronics Corporation:**
  - *W25Q32FV: 3V 32M-Bit Serial Flash Memory with Dual/Quad SPI & QPI Datasheet*  
    Publication: Revision J (Winbond Electronics Corp., 2014)  
    URL: [winbond.com](https://www.winbond.com/)  
    *Usage:* Reconstructed physical SPI NOR flash layout (4,194,304 bytes / 4 MB total, sector size 4 KB, block size 64 KB), read/write timings, and programming command sets.

- **MStar Semiconductor, Inc. (now MediaTek Inc.):**
  - *MSD6306 / TSUMV59 Series Broadcast Television Processor Platform Reference*  
    *Usage:* Architectural mapping of the Macaw12 system-on-chip, Memory Interface Unit (MIU), Register Interface Unit (RIU), and graphic scaler coprocessors.

---

## 2. Processor Architecture & Instruction Set References

- **OpenRISC Architecture Community:**
  - *OpenRISC 1000 Architecture Manual (Architecture Specification version 1.3)*  
    OpenRISC Project, 2017.  
    URL: [openrisc.io/architecture/](https://openrisc.io/architecture/)  
    *Usage:* Baseline architectural model for Aeon RISC32 core register files (`r0`–`r31`), supervisor status registers (SR/SPR), exception vectors, and arithmetic logic conventions.

- **shinyquagsire23:**
  - *ghidra-aeon: Ghidra Processor Module for MStar Aeon / Aeon R2 Core*  
    GitHub Repository: [github.com/shinyquagsire23/ghidra-aeon](https://github.com/shinyquagsire23/ghidra-aeon)  
    Key Files Analyzed:
    - `data/languages/aeon.slaspec`: SLEIGH specification defining register files and instruction field encodings.
    - `data/languages/aeon_ORBIS32.sinc`: Instruction bit patterns and semantics for 16-bit (`bt.*`), 24-bit (`bn.*`), and 32-bit (`bg.*`) instructions.
    - `data/languages/aeon_SPRs.sinc`: Special-purpose register definitions.  
    *Usage:* Primary independent validation authority for decoding the variable-length Aeon R2 ISA, proving instruction-width boundaries, and resolving the direct byte-offset addressing rule for `bg.bnei` / `bg.beqi`.

- **OpenRISC GNU Toolchain:**
  - *or1k-elf GCC Cross-Compiler Port*  
    Free Software Foundation / OpenRISC.  
    URL: [github.com/openrisc/or1k-gcc](https://github.com/openrisc/or1k-gcc)  
    *Usage:* Cross-compilation research, ABI calling convention comparison (`r3`–`r8` argument registers, `r9` link register, `r1` stack pointer), and prologue/epilogue verification.

- **Linux Kernel MStar Platform Patches:**
  - *MStar Aeon R2 Stack Unwinder and Backtrace Implementation (`r2_backtrace.c`)*  
    Linux-MStar Open Source Project.  
    *Usage:* Validated stack frame conventions (`bt.addi r1, -imm`, `bn.sw offset(r1), r9`) and exception return behavior.

---

## 3. Firmware Framework & Operating System Architecture

- **MStar Semiconductor Utopia Middleware:**
  - *Utopia (Universal Total Operating Platform & Integration Architecture) SDK Documentation & Source Headers*  
    *Usage:* Reconstructed module hierarchy, naming schemes, and interface semantics:
    - **`MDrv_GE_*`:** Graphic Engine 2D hardware blitter APIs (`MDrv_GE_FillRect`, `MDrv_GE_DrawLine`, `MDrv_GE_BitBltEX`, `MDrv_GE_SetDstBuffer`, `MDrv_GE_SetClipWindow`).
    - **`MDrv_GOP_*` / `HAL_GOP_*`:** Graphic Output Pipeline & GWIN window compositor (`MDrv_GOP_Init`, `HAL_GOP_SetDWINMIU`, `MDrv_GOP_GWIN_SetGwinInfo`, `MDrv_GOP_GWIN_WaitVsync`).
    - **`MsOS_*`:** Hardware abstraction layer for memory management (`MsOS_AllocateMemory`), shared memory (`MsOS_SHM_*`), and synchronization primitives.
    - **`timer_cb`:** Static callback array scheduler (`timer_cb/timer_cb.c`).
    - **`MApp_ZUI_*`:** Zoom UI framework window manager (`MApp_ZUI_Main.c`, `MApp_ZUI_APIwindow.c`, `MApp_ZUI_APIgdi.c`, `_eActiveOSD`).

- **NEC Remote Control Infrared Protocol:**
  - *NEC 38 kHz Infrared Transmission Protocol Specification*  
    *Usage:* Mapped physical carrier frequency (38 kHz), leading pulse timings (9 ms + 4.5 ms burst/space), bit encoding intervals (560 $\mu$s burst, 560 $\mu$s / 1690 $\mu$s space), and scan-code mapping for Samsung remotes (`KEY_UP=0x60`, `KEY_DOWN=0x61`, `KEY_LEFT=0x65`, `KEY_RIGHT=0x62`, `KEY_ENTER=0x68`).

---

## 4. Software Reverse Engineering & Binary Analysis Tools

- **National Security Agency (NSA):**
  - *Ghidra Software Reverse Engineering Framework* (v11.x)  
    URL: [ghidra-sre.org](https://ghidra-sre.org/)  
    *Usage:* Cross-referenced binary control-flow graphs, data-type propagation, and SLEIGH disassembly trees.

- **Binwalk:**
  - *Craig Heffner et al., Binwalk: Firmware Analysis Tool*  
    GitHub Repository: [github.com/ReFirmLabs/binwalk](https://github.com/ReFirmLabs/binwalk)  
    *Usage:* Baseline signature scanning, entropy calculation, and raw Deflate/LZMA partition chunk location.

- **Python Software Foundation:**
  - *Python Standard Library (v3.10+)*  
    Modules utilized: `struct` (binary unpacking), `hashlib` (SHA-256 verification), `zlib` (raw RFC 1951 decompression), `re` (symbolic pattern scanning), `unittest` (automated regression test suites).

---

## 5. Protocols, File Formats & Compression Standards

- **Internet Engineering Task Force (IETF):**
  - *RFC 1951: DEFLATE Compressed Data Format Specification version 1.3*  
    P. Deutsch, May 1996.  
    URL: [datatracker.ietf.org/doc/html/rfc1951](https://datatracker.ietf.org/doc/html/rfc1951)  
    *Usage:* Verified the non-zlib raw Deflate stream structure residing at flash offset `0x023880` and reproduced bitstream decompression yielding `decompressed_main.bin` (3,103,664 bytes).
  - *RFC 1950: ZLIB Compressed Data Format Specification version 3.3*  
    P. Deutsch, J-L. Gailly, May 1996.  
    URL: [datatracker.ietf.org/doc/html/rfc1950](https://datatracker.ietf.org/doc/html/rfc1950)

- **IEEE / ITU-T:**
  - *CRC-32 (IEEE 802.3 Ethernet Polynomial: `0xEDB88320`)*  
    *Usage:* Validated chunk integrity verification algorithms used by `USB SW Update!` in `T-MXL0MASC.bin`.

---

## 6. Community Reverse Engineering & Homebrew Research

- **SamyGO Community:**
  - *SamyGO: Samsung TV Open Source Firmware Modification Project*  
    URL: [samygo.tv](https://www.samygo.tv/)  
    *Usage:* Verified historical research into Samsung TV generations. Confirmed that SamyGO tools (F-Series, H-Series Smart TV rooting) strictly target Linux-based Orsay and Tizen platforms with ARM or MIPS cores, and explicitly do not support non-smart `T-MXL` MStar series televisions due to the complete lack of a Linux runtime.

- **RootMyTV Team:**
  - *RootMyTV: Rooting LG webOS Televisions*  
    URL: [rootmytv.org](https://rootmytv.org/)  
    *Usage:* Comparative case study on display plane overlay injection vs. native application execution in commercial television homebrew.

---

## 7. Embedded Security & Hardware Analysis Literature

- **Colin O'Flynn & Jasper van Woudenberg:**
  - *The Hardware Hacking Handbook: Breaking Embedded Security with Hardware Attacks*  
    No Starch Press, 2021. ISBN: 978-1-7185-0100-3.  
    *Usage:* Methodology reference for non-destructive board inspection, UART voltage level detection, oscilloscope/logic-analyzer baud discovery, and SPI NOR flash extraction protocols.

- **Andrew "bunnie" Huang:**
  - *Hacking the Xbox: An Introduction to Reverse Engineering*  
    No Starch Press, 2003. ISBN: 978-1-59327-029-2.  
    *Usage:* Foundational principles of defensive reverse engineering, hardware integrity boundaries, and safety protocols for avoiding brick states.

- **Chris Eagle:**
  - *The IDA Pro Book: The Unofficial Guide to the World's Most Popular Disassembler*  
    No Starch Press, 2011. ISBN: 978-1-59327-289-0.  
    *Usage:* Control-flow graph recovery techniques, basic block boundary identification, and cross-reference analysis in stripped embedded binaries.
