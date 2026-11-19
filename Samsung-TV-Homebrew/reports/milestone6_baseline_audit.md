# Milestone 6: Baseline Audit Report

**Project:** Project Macaw (Samsung UA23H4003ARLXL / MStar Macaw12 / Aeon R2)  
**Audit Target:** Repository artifacts, previous milestone reports (Milestones 1–5), scripts, and claims  
**Commit Audited:** `a7b90a6`  
**Classification Scheme:**
- **Verified:** Directly reproduced or supported by independently inspectable evidence.
- **Partially verified:** Some evidence exists, but important details remain uncertain.
- **Hypothesis:** Plausible interpretation without sufficient direct evidence.
- **Unverified:** No reproducible evidence found.
- **Incorrect:** Contradicted by the available evidence.

---

## 1. Executive Audit Summary

The purpose of this baseline audit is to establish ground truth before implementing the Milestone 6 Aeon R2 emulator and host-side Snake integration. Prior milestones laid substantial groundwork, but several claims require critical refinement:

| Component / Claim | Previous Claim | Audit Finding | Status |
| :--- | :--- | :--- | :--- |
| **Firmware Integrity** | `T-MXL0MASC.bin` intact | Hashes verified (`f02cbf...`, `a7acb4...`) | **VERIFIED** |
| **Instruction Widths** | `0x00-0x7F` (24b), `0x80-0x9F` (16b), `0xA0-0xFF` (32b) | Confirmed by SLEIGH and MStar kernel backtrace macros | **VERIFIED** |
| **Instruction Boundary Detection** | Linear decoding across regions | Valid for code streams, but variable-length is non-self-synchronizing across data/tables | **PARTIALLY VERIFIED** |
| **Register & Calling Conventions** | `r1`=sp, `r2`=fp, `r9`=lr, `r3-r8`=args, `r3`=ret | Confirmed by exception frame `0x020280`, `aeon.cspec` | **VERIFIED** |
| **Mini-Assembler Correctness** | 100% round-trip verified against self | Self-referential test masked immediate decoding discrepancy in `bn.lwz` | **PARTIALLY VERIFIED** |
| **31-Byte Test Program** | Valid Aeon R2 machine code | Legal encodings, but `bn.lwz` immediate field encoding is word-shifted | **PARTIALLY VERIFIED** |
| **GE API Offsets (`0x17bd3e`, etc.)** | Executable GE functions | Offsets are ASCII strings in `.rodata`, NOT executable code addresses | **INCORRECT** |
| **Remote-Control Event Dispatch** | ZUI `u8WinProcID` Aging Menu hijack | Architecture supported by strings, but exact function pointers unconfirmed | **HYPOTHESIS** |
| **Snake Game Logic (`snake_sim.py`)** | Deterministic host simulation | Logic correctly handles grid, steering, collisions, and draw commands | **VERIFIED** |

---

## 2. Detailed Audit of Specific Components

### 2.1 Aeon R2 Instruction-Width Classification
- **Claim:** Instruction width is determined by the upper 3 bits (`Bits [7:5]`) of byte 0:
  - `0x00–0x7F` (top 3 bits `000`–`011`): 24-bit (`bn.*`)
  - `0x80–0x9F` (top 3 bits `100`): 16-bit (`bt.*`)
  - `0xA0–0xFF` (top 3 bits `101`–`111`): 32-bit (`bg.*`)
- **Evidence:**
  - `ghidra-aeon/data/languages/aeon_ORBIS32.sinc`: lines 145, 192, 420.
  - MStar Chakra3 `r2_backtrace.c` opcode definitions (`OP_R2_BT_ADDI_PFX 0x27`, `OP_R2_BN_ADDI_PFX 0x07`, `OP_R2_BG_ADDI_PFX 0x3F`).
- **Verdict:** **VERIFIED**.

### 2.2 Instruction Boundary Detection
- **Claim:** Firmware code regions can be linearly decoded by following the prefix width rule.
- **Evidence:** Disassembly of Bootloader Reset (`0x000100`), Exception Handler (`0x020280`), and Main Application (`0x000000`, `0x001000`) shows proper alignment and valid instructions.
- **Caveat:** Variable-length instruction architectures (16/24/32-bit) are not self-synchronizing. If a disassembler encounters embedded data, alignment padding, or jump tables, it will desynchronize until the next aligned function prologue.
- **Verdict:** **PARTIALLY VERIFIED** (valid for pure code streams; requires symbol/control-flow boundaries for full binary coverage).

### 2.3 Register Conventions and Calling Convention
- **Claim:** `r1` = Stack Pointer, `r2` = Frame Pointer, `r9` = Link Register / Return Address, `r3`–`r8` = Arguments, `r3` = Return Value.
- **Evidence:**
  - Exception handler at `0x020280` allocates stack with `bg.addi r1, r1, -284` and systematically spills `r3`–`r31` relative to `r1`.
  - Subroutine calls (`bg.jal`, `bn.jal`, `bt.jalr`) set `r9 = inst_next`.
  - Subroutine returns use `bt.jr r9`.
  - `aeon.cspec` defines `unaffected` registers and parameter passing in `r3`–`r8`.
- **Verdict:** **VERIFIED**.

### 2.4 Mini-Assembler Encoding Correctness & 31-Byte Program
- **Claim:** `scripts/milestone5/aeon_r2_mini_assembler.py` generates valid Aeon R2 machine code that round-trips 100%.
- **Evidence Audit:**
  - `bg.addi r1, r1, -16`: `fc 21 ff f0` -> Opcode `0x3F`, `rD=1`, `rA=1`, `simm16=-16`. **VERIFIED**.
  - `bn.sw 12(r1), r9`: `0d 21 0c` -> Opcode `0x03`, `uimm0_2=0`, `rD=9`, `rA=1`, `offset=12`. **VERIFIED**.
  - `bt.movi r10, 10`: `99 4a` -> Opcode `0x26`, `rD=10`, `simm5=10`. **VERIFIED**.
  - `bt.add r3, r4`: `8c 64` -> Opcode `0x23`, `rD=3`, `rA=4`. **VERIFIED**.
  - `bn.addi r3, r3, 5`: `1c 63 05` -> Opcode `0x07`, `rD=3`, `rA=3`, `simm8=5`. **VERIFIED**.
  - `bt.jr r9`: `85 29` -> Opcode `0x21`, `uimm=0x09`, `rD=9`. **VERIFIED**.
  - `bn.lwz r10, 8(r1)`: `0d 41 0a` -> Opcode `0x03`, `uimm0_2=2`. In `aeon_ORBIS32.sinc`:
    `i24_mB_16: i24_simm0_8_masked(i24_rA) is i24_simm0_8 & i24_rA & i24_simm2_6 [ i24_simm0_8_masked = i24_simm2_6 << 2; ]`
    The byte offset is `i24_simm2_6 << 2`. In the Milestone 5 script, the decoder printed `0xa(r1)` instead of evaluating the word-shifted immediate (`(0x0A >> 2) << 2 = 8`). While the encoding `0x0A` correctly represents offset 8 in hardware, the Milestone 5 decoder reported raw byte `0x0A`.
- **Verdict:** **PARTIALLY VERIFIED** (Machine code encodings are valid against SLEIGH, but decoder output displayed raw immediate fields rather than effective memory offsets).

### 2.5 GE API Offsets (`0x17bd3e`, `0x17bd4f`, `0x17bd60`, `0x17bd9d`)
- **Claim in early milestones:** Functions `MDrv_GE_FillRect`, `MDrv_GE_DrawLine`, etc. reside at `0x17bd3e`, etc.
- **Evidence Audit:**
  - Inspection of `decompressed_main.bin` at `0x17bd3e`:
    Contains ASCII bytes `4d 44 72 76 5f 47 45 5f 46 69 6c 6c 52 65 63 74 00` ("MDrv_GE_FillRect\0").
  - This is inside the `.rodata` section (`0x150000`–`0x190000`), NOT executable `.text` (`0x000000`–`0x150000`).
  - These strings are diagnostic tags passed to assertion macros (`%s: address fail`, `%s: pitch fail`).
- **Verdict:** **INCORRECT**. The offsets are string-table locations, NOT executable function entry points. The actual driver functions reside in `.text`.

### 2.6 Remote-Control Event-Dispatch Assumptions
- **Claim:** Remote control input can be intercepted by hooking `MApp_ZUI_ACTagingmenu`.
- **Evidence Audit:**
  - The string `tv-ap/dvb/ui2_M10/MApp_ZUI_ACTagingmenu.c` exists in `.rodata` at `0x16c870`.
  - Format string `u8WinProcID= %d \n` exists at `0x16ca03`.
  - However, the exact dispatch table offset, function pointer addresses, and callback signatures have not been extracted from `.text`.
- **Verdict:** **HYPOTHESIS**. The structural existence of ZUI action modules is verified, but hooking them requires executable address recovery.

### 2.7 Existing Snake Engine Correctness
- **Claim:** `poc/snake-host/snake_sim.py` implements a verified host-side Snake game decoupled from graphics.
- **Evidence Audit:**
  - The script executes standalone with 8 automated unit tests.
  - All 8 tests passed in Milestone 5: initial state, direction changes, 180° reverse rejection, food consumption, growth, wall collision, self collision, and rendering call generation.
- **Verdict:** **VERIFIED**.

---

## 3. Baseline Hash Verification

| Artifact | SHA-256 Hash | Audit Status |
| :--- | :--- | :--- |
| `Samsung-TV-Homebrew/firmware/T-MXL0MASC.bin` | `f02cbf9ecf87087ea85826584cc9ad949b13d1ff404b1fe8888323b0f4ed52d5` | Verified / Unchanged |
| `Samsung-TV-Homebrew/analysis/decompressed_main.bin` | `a7acb484039d43e045e9839a61c693ed6e621484fbf23e384ac33cc0b7ec5884` | Verified / Unchanged |

---

## 4. Priority Action Items for Milestone 6

1. **Independent Disassembler/Decoder:** Build an independent Aeon R2 decoder based directly on `ghidra-aeon` and MStar Chakra3 specifications to independently validate `aeon_r2_mini_assembler.py`.
2. **Modular Emulator:** Construct `poc/aeon-r2-emulator/` supporting the verified instruction subset (arithmetic, logical, branches, load/store, calls/returns) with full trace capability.
3. **Mock GE Graphics Engine:** Create `poc/snake-host/mock_ge.py` implementing an abstract framebuffer interface without claiming binary ABI equivalence to the TV.
4. **End-to-End Integration:** Connect the verified Snake game engine to the mock graphics engine and demonstrate deterministic host-side frame rendering.
