# Milestone 6: Aeon R2 Emulator Test Suite Report

**Subject:** Automated unit test results and verification matrix for `poc/aeon-r2-emulator/`  
**Test Runner:** `poc/aeon-r2-emulator/tests/test_emulator.py`  
**Date:** November 2026  

---

## 1. Test Suite Overview

An automated test suite was constructed to validate the Aeon R2 emulator independently of the mini-assembler. The suite tests instruction decoding, register invariants, 32-bit arithmetic wrapping, memory load/store operations, conditional branching, stack management, execution limits, and full program execution.

### Overall Results
- **Total Tests Executed:** 10
- **Passed:** 10 (100%)
- **Failed:** 0
- **Execution Time:** ~0.002s

---

## 2. Detailed Test Matrix

| Test Case | Category | Verification Objective | Result |
| :--- | :--- | :--- | :--- |
| `test_16bit_instruction_decoding` | Decoder | Validates decoding of `bt.nop`, `bt.mov`, `bt.add`, and `bt.jr` | **PASS** |
| `test_24bit_instruction_decoding` | Decoder | Validates decoding of `bn.nop`, `bn.sw`, `bn.lwz`, and `bn.addi` | **PASS** |
| `test_32bit_instruction_decoding` | Decoder | Validates decoding of `bg.addi` and `bg.movhi` | **PASS** |
| `test_unsupported_instruction_error` | Decoder | Ensures `UnsupportedInstructionError` is raised on illegal opcode | **PASS** |
| `test_r0_hardwired_zero` | CPU State | Verifies that writes to `r0` are discarded and `r0` always reads `0` | **PASS** |
| `test_arithmetic_overflow_wrapping` | CPU Arithmetic | Verifies unsigned 32-bit arithmetic overflow wrapping (`0xFFFFFFFF + 1 = 0`) | **PASS** |
| `test_load_and_store` | Memory | Verifies Big-Endian 32-bit word store (`bn.sw`) and load (`bn.lwz`) | **PASS** |
| `test_conditional_branch_taken_and_not_taken` | Control Flow | Tests `bn.beqi` condition evaluation (branch taken advances PC by rel; not taken advances by length) | **PASS** |
| `test_31byte_subroutine_execution` | Execution | Executes full 31-byte program: stack allocation, arithmetic, spill/restore, return | **PASS** |
| `test_execution_limit_infinite_loop` | Safety | Verifies emulator halts cleanly when `max_steps` instruction limit is hit | **PASS** |

---

## 3. Provenance of Test Vectors

1. **`0x0C 0x81 0x10` (`bn.sw 0x10(r1), r4`):** Sourced directly from line 184 of Ghidra SLEIGH `aeon_ORBIS32.sinc` and firmware exception handler at `0x020287`.
2. **`0xFC 0x21 0xFE 0xE4` (`bg.addi r1, r1, -284`):** Sourced directly from firmware exception vector entry at `0x020280`.
3. **`0x85 0x29` (`bt.jr r9`):** Sourced from Chakra3 `r2_backtrace.c` subroutine return convention.
4. **`0x0D 0x41 0x0A` (`bn.lwz r10, 8(r1)`):** Derived independently from SLEIGH `i24_simm2_6 << 2` specification.

---

## 4. Conclusion

The test suite validates that the emulator behaves deterministically according to the documented Aeon R2 architecture. All core components (registers, memory, decoder, execution, control flow, and safety limits) perform without regression.
