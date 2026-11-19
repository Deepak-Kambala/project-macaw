# Milestone 7 Emulator Extensions & ISA Refinements

**Target Core:** MStar Aeon R2 (OpenRISC-derived 32-bit core)  
**Binary Artifacts:** `poc/aeon-r2-emulator/decoder.py` & `poc/aeon-r2-emulator/instructions.py`  
**Date:** November 2026  
**Status:** Completed & Regression Tested  

---

## 1. Executive Summary

In Milestone 7, the Aeon R2 emulator (`poc/aeon-r2-emulator/`) was expanded strictly as required by the execution requirements of real firmware routines extracted from `decompressed_main.bin`. Rather than speculating on unverified instructions, six concrete instructions were added and one critical branch displacement decoding rule was corrected against independent evidence from `shinyquagsire23/ghidra-aeon` (`aeon_ORBIS32.sinc`):

1. **`bn.slli`:** 24-bit shift left immediate (`rD = rA << imm`).
2. **`bn.lh`:** 24-bit load unsigned 16-bit halfword with even offset masking (`rD = mem.read_u16(rA + (offset & ~1))`).
3. **`bn.exthz`:** 24-bit zero-extend halfword (`rD = rA & 0xFFFF`).
4. **`bn.extbz`:** 24-bit zero-extend byte (`rD = rA & 0xFF`).
5. **`bn.lbz`:** 24-bit load unsigned 8-bit byte (`rD = mem.read_u8(rA + offset)`).
6. **`bn.sbz`:** 24-bit store 8-bit byte (`mem.write_u8(rA + offset, rD & 0xFF)`).
7. **Branch Displacement Fix (`bg.bnei` / `bg.beqi`):** Aeon R2 variable-length instructions allow odd-byte instruction lengths (24-bit / 3-byte). Consequently, 32-bit conditional branch displacements (`i32_simm3_13`) represent direct byte offsets ($PC + \text{offset}$), not halfword offsets ($PC + (\text{offset} \times 2)$). Correcting this eliminated an erroneous $2\times$ scaling factor.

---

## 2. Itemized Instruction Encodings & Semantics

### 2.1 `bn.slli` (Shift Left Logical Immediate)
- **Format:** 24-bit (`0x00–0x7F`)
- **Opcode:** `0x13` (bits 23..18)
- **Sub-opcode:** `uimm0_3 = 0` (bits 2..0)
- **Shift Count:** `uimm3_5` (bits 7..3)
- **Source Register:** `rA` (bits 12..8)
- **Destination Register:** `rD` (bits 17..13)
- **SLEIGH Reference:** `aeon_ORBIS32.sinc:329`:
  `:bn.slli i24_rD, i24_rA, i24_uimm3_5 is i24_uimm0_3 = 0 & i24_rD & i24_rA & i24_uimm3_5 { i24_rD = i24_rA << i24_uimm3_5; }`
- **Semantics:**
  $$\text{regs}[rD] = (\text{regs}[rA] \ll \text{imm}) \& 0\text{xFFFFFFFF}$$
- **Flags/Side Effects:** No condition flags modified.

### 2.2 `bn.lh` (Load Halfword)
- **Format:** 24-bit (`0x00–0x7F`)
- **Opcode:** `0x02` (bits 23..18)
- **Base Register:** `rA` (bits 12..8)
- **Destination Register:** `rD` (bits 17..13)
- **Offset:** `simm0_8 & 0xFE` (8-bit signed immediate masked to 2-byte alignment)
- **SLEIGH Reference:** `aeon_ORBIS32.sinc:201`:
  `:bn.lh i24_rD,i24_mB_2 is i24_opcode = 0x02 & i24_rD & i24_mB_2 { i24_rD[0,16] = 0; i24_rD[16,16] = *:2 i24_mB_2; }`
- **Semantics:**
  $$\text{EA} = (\text{regs}[rA] + (\text{simm8} \& \sim 1)) \& 0\text{xFFFFFFFF}$$
  $$\text{regs}[rD] = \text{mem.read\_u16}(\text{EA})$$

### 2.3 `bn.extbz` & `bn.exthz` (Zero-Extend Byte / Halfword)
- **Format:** 24-bit (`0x00–0x7F`)
- **Opcode:** `0x17` (bits 23..18)
- **Mode Selector:** `bit0 = 0`, `uimm1_4 = (val >> 1) & 0xF`:
  - `uimm1_4 == 0`: `bn.extbz` (zero-extend lowest 8 bits)
  - `uimm1_4 == 2`: `bn.exthz` (zero-extend lowest 16 bits)
- **SLEIGH Reference:** `aeon_ORBIS32.sinc:346, 348`:
  `:bn.extbz i24_rD, i24_rA is i24_uimm1_4 = 0x0 & i24_rD & i24_rA { i24_rD = zext(i24_rA[24,8]); }`
  `:bn.exthz i24_rD, i24_rA is i24_uimm1_4 = 0x2 & i24_rD & i24_rA { i24_rD = zext(i24_rA[16,16]); }`
- **Semantics:**
  $$\text{bn.extbz: } \text{regs}[rD] = \text{regs}[rA] \& 0\text{xFF}$$
  $$\text{bn.exthz: } \text{regs}[rD] = \text{regs}[rA] \& 0\text{xFFFF}$$

### 2.4 `bn.lbz` (Load Byte Zero-Extended)
- **Format:** 24-bit (`0x00–0x7F`)
- **Opcode:** `0x04` (bits 23..18)
- **Base Register:** `rA` (bits 12..8)
- **Destination Register:** `rD` (bits 17..13)
- **Offset:** `simm0_8` (8-bit signed immediate)
- **SLEIGH Reference:** `aeon_ORBIS32.sinc:212`:
  `:bn.lbz i24_rD,i24_mB is i24_opcode = 0x04 & i24_rD & i24_mB { i24_rD[0,24] = 0; i24_rD[24,8] = *:1 i24_mB; }`
- **Semantics:**
  $$\text{EA} = (\text{regs}[rA] + \text{simm8}) \& 0\text{xFFFFFFFF}$$
  $$\text{regs}[rD] = \text{mem.read\_u8}(\text{EA})$$

### 2.5 `bn.sbz` (Store Byte)
- **Format:** 24-bit (`0x00–0x7F`)
- **Opcode:** `0x06` (bits 23..18)
- **Base Register:** `rA` (bits 12..8)
- **Source Register:** `rD` (bits 17..13)
- **Offset:** `simm0_8` (8-bit signed immediate)
- **SLEIGH Reference:** `aeon_ORBIS32.sinc:215`:
  `:bn.sbz i24_mB,i24_rD is i24_opcode = 0x06 & i24_rD & i24_mB { *:1 i24_mB = i24_rD[24,8]; }`
- **Semantics:**
  $$\text{EA} = (\text{regs}[rA] + \text{simm8}) \& 0\text{xFFFFFFFF}$$
  $$\text{mem.write\_u8}(\text{EA}, \text{regs}[rD] \& 0\text{xFF})$$

---

## 3. Critical Architectural Discovery: Conditional Branch Displacement Units

### The Problem
During initial execution of Routine 2 (`0x0016E1`), the 15-iteration loop failed to repeat: instruction `0x0016F8` (`bg.bnei r6, 15, -13`) branched to `0x000FFD` instead of `0x00100A`.

### The Root Cause
In traditional RISC architectures (such as standard OpenRISC OR1K or MIPS), instructions are strictly aligned to 4-byte boundaries, and branch immediate fields store word or halfword displacements that the CPU shifts left by 2 ($rel \times 4$) or by 1 ($rel \times 2$).

However, MStar Aeon R2 features **mixed 16-bit, 24-bit, and 32-bit instructions**. Because 24-bit instructions have odd byte length (3 bytes), instruction boundaries are aligned to **halfword (2-byte) or byte boundaries**, not 4-byte boundaries.

Independent validation against `aeon_ORBIS32.sinc:74`:
```text
i32_rel_simm3_13: ea is i32_simm3_13 [ ea = i32_simm3_13 + inst_start; ] {
    export *:4 ea;
}
```
confirms that `i32_simm3_13` is added **directly to `inst_start` without any multiplication**.

### Verification
In Routine 2, the loop start is at offset $+10$ bytes (`0x0016EB`). The `bg.bnei` instruction is at offset $+23$ bytes (`0x0016F8`).
$$\text{Displacement} = 10 - 23 = -13 \text{ bytes}$$
Extracting bits 15..3 of `0xD0CFFF9E` yields signed value $-13$. When added directly:
$$0\text{x}0016\text{F}8 + (-13) = 0\text{x}0016\text{EB} \quad (\text{Exact Loop Target!})$$

---

## 4. Verification & Regression Testing

All added instructions and decoding rules have been validated:
1. `test_emulator.py`: 10/10 tests pass (full backward compatibility).
2. `test_real_routine.py`: 7/7 tests pass, including:
   - Negative counter-example proving failure under the old halfword scaling assumption.
   - Bit-for-bit validation of Routine 1 (7 test vectors).
   - Bit-for-bit validation of Routine 2 (5 test vectors).
