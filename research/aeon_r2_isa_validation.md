# Aeon R2 Instruction Set Architecture (ISA) Validation

**Target Processor:** MStar Aeon R2 (32-bit RISC core with variable-length instruction set)  
**Primary Reference:** `shinyquagsire23/ghidra-aeon` (`aeon_ORBIS32.sinc`, `aeon.slaspec`, `aeon.cspec`)  
**Secondary Reference:** MStar Chakra3 RTOS kernel sources (`r2_backtrace.c`)  
**Validation Date:** November 2026  

---

## 1. Architectural Overview

The **MStar Aeon R2** processor core is a proprietary implementation within the OpenRISC family developed by MStar Semiconductor (now MediaTek). Unlike standard OpenRISC 1000 (ORBIS32) cores which use fixed 32-bit instruction words, the Aeon R2 core introduces a **variable-width compressed instruction architecture** combining:
- **16-bit instructions (`bt.*`)**: Compact instructions for common register moves, short branches, and immediate additions.
- **24-bit instructions (`bn.*`)**: Mid-width instructions providing 5-bit register addresses and 8-bit immediates.
- **32-bit instructions (`bg.*`)**: Full-width instructions for 16-bit immediates, wide memory offsets, SPR access, and long branches/calls.

Endianness is strictly **Big Endian** across all token widths.

---

## 2. Instruction Width Determination

Instruction width is dictated by the top 3 bits (`Bits [7:5]`) of the first byte fetched:

```text
First Byte (B0): [ b7 b6 b5 | b4 b3 b2 b1 b0 ]
                   ^^^^^^^^
                   Decoder Prefix
```

| First Byte Range | Binary Prefix `b7..b5` | Decoder Category | Length | Instruction Family |
| :--- | :--- | :--- | :--- | :--- |
| `0x00` – `0x7F` | `000`, `001`, `010`, `011` | `i24_decoder = 0..3` | **24 bits (3 bytes)** | `bn.*` (e.g., `bn.sw`, `bn.lwz`, `bn.addi`, `bn.add`, `bn.ori`) |
| `0x80` – `0x9F` | `100` | `i16_decoder = 4` | **16 bits (2 bytes)** | `bt.*` (e.g., `bt.nop`, `bt.mov`, `bt.add`, `bt.addi`, `bt.jr`) |
| `0xA0` – `0xFF` | `101`, `110`, `111` | `i32_decoder = 5..7` | **32 bits (4 bytes)** | `bg.*` (e.g., `bg.addi`, `bg.jal`, `bg.sw`, `bg.lwz`, `bg.movhi`) |

### Cross-Verification with MStar Chakra3 Kernel
In MStar's official kernel backtrace implementation (`r2_backtrace.c`):
```c
#define OP_R2_ENTRI_PFX   0x17
#define OP_R2_ENTRI_SUB   0x18
#define OP_R2_STACK_PFX   0x20
#define OP_R2_BT_ADDI_PFX 0x27  /* 0x27 in 6-bit opcode -> top 3 bits 100 = 16-bit bt.addi */
#define OP_R2_BN_ADDI_PFX 0x07  /* 0x07 in 6-bit opcode -> top 3 bits 000 = 24-bit bn.addi */
#define OP_R2_BG_ADDI_PFX 0x3F  /* 0x3F in 6-bit opcode -> top 3 bits 111 = 32-bit bg.addi */
```
This confirms the tripartite division across both open reverse-engineering tools and vendor source code.

---

## 3. Instruction Encoding Fields

### 3.1 16-bit Token (`instr16`, Big Endian 16-bit word)
- `i16_opcode = (10, 15)` (6 bits)
- `i16_rD = (5, 9)` (5 bits)
- `i16_rA = (0, 4)` (5 bits)
- `i16_simm0_5 = (0, 4)` signed (5 bits)
- `i16_uimm0_5 = (0, 4)` unsigned (5 bits)
- `i16_bit5 = (5, 5)` (1 bit)
- `i16_bit0 = (0, 0)` (1 bit)

### 3.2 24-bit Token (`instr24`, Big Endian 24-bit word)
- `i24_opcode = (18, 23)` (6 bits)
- `i24_rD = (13, 17)` (5 bits)
- `i24_rA = (8, 12)` (5 bits)
- `i24_rB = (3, 7)` (5 bits)
- `i24_uimm0_2 = (0, 1)` (2 bits, sub-opcode)
- `i24_uimm0_3 = (0, 2)` (3 bits, sub-opcode)
- `i24_simm0_8 = (0, 7)` signed (8 bits)
- `i24_simm2_6 = (2, 7)` signed (6 bits, word-aligned offset)

### 3.3 32-bit Token (`instr32`, Big Endian 32-bit word)
- `i32_opcode = (26, 31)` (6 bits)
- `i32_rD = (21, 25)` (5 bits)
- `i32_rA = (16, 20)` (5 bits)
- `i32_simm0_16 = (0, 15)` signed (16 bits)
- `i32_uimm0_16 = (0, 15)` unsigned (16 bits)
- `i32_uimm1_3 = (1, 3)` (3 bits, sub-opcode)
- `i32_bit0 = (0, 0)` (1 bit)

---

## 4. Alignment & Sequential Decoding Dynamics

1. **Alignment Constraints:**
   - Standard 32-bit architectures enforce 4-byte alignment.
   - Aeon R2 instruction lengths include 3-byte (24-bit) instructions. Therefore, instructions can begin on **any byte boundary** (or at minimum 16-bit boundaries, but in practice packed sequentially).
   - In `decompressed_main.bin`, instructions immediately follow one another without padding bytes between different widths:
     - `0x000000`: 3 bytes (`bn.sw`)
     - `0x000003`: 3 bytes (`bn.muls`)
     - `0x000006`: 4 bytes (`bg.movhi`)
     - `0x00000a`: 4 bytes (`bg.addi`)
     - `0x00000e`: 2 bytes (`bt.add`)
     - `0x000010`: 4 bytes (`bg.movhi`)
2. **Sequential Desynchronization Risk:**
   - Because instruction lengths vary (2, 3, or 4 bytes), decoding must proceed strictly along valid execution paths.
   - If decoding starts mid-instruction or in an embedded data literal, the decoder will parse phantom instructions until resynchronizing.

---

## 5. Families Sufficiently Understood for Emulation

The following core instruction subset is independently verified and selected for Milestone 6 emulator implementation:

### Category 1: Arithmetic & Logic
- `bt.add rD, rA`: `rD = rD + rA` (16-bit)
- `bt.mov rD, rA`: `rD = rA` (16-bit)
- `bt.movi rD, simm5`: `rD = simm5` (16-bit)
- `bt.addi rD, simm5`: `rD = rD + simm5` (16-bit)
- `bn.add rD, rA, rB`: `rD = rA + rB` (24-bit)
- `bn.sub rD, rA, rB`: `rD = rA - rB` (24-bit)
- `bn.addi rD, rA, simm8`: `rD = rA + simm8` (24-bit)
- `bn.and rD, rA, rB`: `rD = rA & rB` (24-bit)
- `bn.or rD, rA, rB`: `rD = rA | rB` (24-bit)
- `bn.xor rD, rA, rB`: `rD = rA ^ rB` (24-bit)
- `bn.ori rD, rA, ik8`: `rD = rA | ik8` (24-bit)
- `bn.andi rD, rA, ik8`: `rD = rA & ik8` (24-bit)
- `bg.addi rD, rA, simm16`: `rD = rA + simm16` (32-bit)
- `bg.andi rD, rA, uimm16`: `rD = rA & uimm16` (32-bit)
- `bg.ori rD, rA, uimm16`: `rD = rA | uimm16` (32-bit)
- `bg.movhi rD, uimm16`: `rD = uimm16 << 16` (32-bit)

### Category 2: Memory Access (Load & Store)
- `bn.sw offset(rA), rD`: Store 32-bit word (`*:4 (rA + offset) = rD`) (24-bit)
- `bn.lwz rD, offset(rA)`: Load 32-bit word (`rD = *:4 (rA + offset)`) (24-bit)
- `bg.sw offset(rA), rD`: Store 32-bit word with 16-bit signed offset (32-bit)
- `bg.lwz rD, offset(rA)`: Load 32-bit word with 16-bit signed offset (32-bit)

### Category 3: Branches, Calls & Returns
- `bt.nop`: No operation (16-bit)
- `bt.jr rD`: Jump register (`PC = rD`); when `rD=9`, serves as subroutine return (`ret`) (16-bit)
- `bt.j rel10`: Relative unconditional branch (16-bit)
- `bn.beqi rD, imm3, rel8`: Branch if `rD == imm3` (24-bit)
- `bn.bnei rD, imm3, rel8`: Branch if `rD != imm3` (24-bit)
- `bg.jal rel25`: Jump and link (`r9 = PC + 4; PC = PC + rel25 * 2`) (32-bit)
- `bg.j rel25`: Unconditional relative jump (32-bit)

---

## 6. Ambiguous or Unsupported Instructions

The following instructions have unverified micro-architectural side-effects and are explicitly excluded from the minimal emulator:
1. `bg.flush_invalidate`, `bg.syncwritebuffer`: Cache control and write buffer synchronization. Emulated as NOPs if encountered.
2. `bg.mtspr` / `bg.mfspr`: Access to special purpose registers (SR, ESR, EPCR).
3. `bt.rfe`: Return from exception. Requires supervisor state modeling.
4. `bn.divs` / `bn.divu`: Hardware divider behavior on divide-by-zero.
