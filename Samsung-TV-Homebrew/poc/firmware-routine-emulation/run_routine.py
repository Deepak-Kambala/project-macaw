#!/usr/bin/env python3
"""
poc/firmware-routine-emulation/run_routine.py

Executes real firmware binary routines extracted from the Samsung TV firmware
inside the host-side Aeon R2 emulator and validates results against reference models.
"""

import sys
import os

# Add emulator to path
EMULATOR_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../aeon-r2-emulator"))
sys.path.append(EMULATOR_DIR)

from cpu import CPU
from reference_implementation import ref_routine1_array_lookup, ref_routine2_mem_copy

ROUTINES_DIR = os.path.dirname(os.path.abspath(__file__))

def run_routine1(test_cases=None, verbose=True):
    """
    Executes extracted Routine 1 (0x005177, 13 bytes, array halfword lookup).
    """
    bin_path = os.path.join(ROUTINES_DIR, "routine1_array_lookup.bin")
    with open(bin_path, "rb") as f:
        code_bytes = f.read()

    if test_cases is None:
        test_cases = [
            # (array_data, index)
            ([0x1234, 0x5678, 0xABCD, 0x00FF, 0xA055], 0),
            ([0x1234, 0x5678, 0xABCD, 0x00FF, 0xA055], 1),
            ([0x1234, 0x5678, 0xABCD, 0x00FF, 0xA055], 2),
            ([0x1234, 0x5678, 0xABCD, 0x00FF, 0xA055], 3),
            ([0x1234, 0x5678, 0xABCD, 0x00FF, 0xA055], 4),
            ([0x0000, 0xFFFF, 0x0102, 0x0408, 0x1020], 1),
            ([0x0000, 0xFFFF, 0x0102, 0x0408, 0x1020], 3),
        ]

    if verbose:
        print("==================================================================")
        print("Executing Real Firmware Routine 1: Array Halfword Element Extractor")
        print(f"Artifact: {bin_path} ({len(code_bytes)} bytes)")
        print("==================================================================")

    results = []
    for tc_idx, (table, index) in enumerate(test_cases):
        cpu = CPU(memory_size=0x100000)
        code_addr = 0x1000
        table_addr = 0x2000

        # Load code
        cpu.mem.load_bytes(code_addr, code_bytes)

        # Load table into memory (16-bit big endian)
        for i, val in enumerate(table):
            cpu.mem.write_u16(table_addr + (i * 2), val & 0xFFFF)

        # Set registers
        cpu.regs.write(3, table_addr)  # r3 = base pointer
        cpu.regs.write(4, index)       # r4 = array index
        cpu.regs.write(9, 0xFFFFFFFF)  # r9 = LR return address (sentinel halts on ret)
        cpu.regs.pc = code_addr

        steps = 0
        while not cpu.halted and steps < 20:
            cpu.step()
            steps += 1

        res = cpu.regs.read(3)
        expected = ref_routine1_array_lookup(table, index)

        matched = (res == expected)
        results.append((tc_idx, index, hex(table[index]), hex(res), hex(expected), matched, steps))

        if verbose:
            status_str = "PASS" if matched else "FAIL"
            print(f"Test {tc_idx+1}: index={index}, val={hex(table[index])} -> return r3={hex(res)} (expected {hex(expected)}) [{status_str}, {steps} steps]")

    all_passed = all(r[5] for r in results)
    return all_passed, results


def run_routine2(test_cases=None, verbose=True):
    """
    Executes extracted Routine 2 (0x0016E1, 38 bytes, 15-byte memory copy loop).
    """
    bin_path = os.path.join(ROUTINES_DIR, "routine2_mem_copy.bin")
    with open(bin_path, "rb") as f:
        code_bytes = f.read()

    if test_cases is None:
        test_cases = [
            b"Hello Samsung!!",
            bytes([i * 17 % 256 for i in range(15)]),
            bytes([0xAA] * 15),
            bytes([0x00, 0xFF, 0x55, 0xAA] * 3 + [0x11, 0x22, 0x33]),
            b"Project Macaw12"
        ]

    if verbose:
        print("\n==================================================================")
        print("Executing Real Firmware Routine 2: 15-Byte Memory Buffer Copy Loop")
        print(f"Artifact: {bin_path} ({len(code_bytes)} bytes)")
        print("==================================================================")

    results = []
    DEST_ADDR = 0x00529B26  # Global destination buffer hardcoded in routine

    for tc_idx, src_data in enumerate(test_cases):
        cpu = CPU(memory_size=0x1000000)  # 16 MB space to cover 0x00529B26
        code_addr = 0x1000
        src_addr = 0x2000
        stack_addr = 0x8000

        # Load code
        cpu.mem.load_bytes(code_addr, code_bytes)

        # Load source data
        cpu.mem.load_bytes(src_addr, src_data[:15])

        # Prepare stack frame with saved link register (r9 = 0xFFFFFFFF sentinel)
        cpu.mem.write_u32(stack_addr, 0xFFFFFFFF)

        # Set registers
        cpu.regs.write(1, stack_addr)  # r1 = SP
        cpu.regs.write(5, src_addr)    # r5 = source pointer
        cpu.regs.pc = code_addr

        steps = 0
        while not cpu.halted and steps < 100:
            cpu.step()
            steps += 1

        status_code = cpu.regs.read(3)
        sp_after = cpu.regs.read(1)

        # Read copied memory from destination buffer
        copied_mem = bytes([cpu.mem.read_u8(DEST_ADDR + i) for i in range(15)])

        expected_status, expected_mem = ref_routine2_mem_copy(src_data)

        matched_status = (status_code == expected_status)
        matched_mem = (copied_mem == expected_mem)
        matched_sp = (sp_after == stack_addr + 4)  # popped 4-byte stack frame
        all_ok = matched_status and matched_mem and matched_sp

        results.append((tc_idx, src_data[:15].hex(), copied_mem.hex(), all_ok, steps))

        if verbose:
            status_str = "PASS" if all_ok else "FAIL"
            print(f"Test {tc_idx+1}: copied {len(copied_mem)} bytes -> '{copied_mem.hex()}' [ret={status_code}, sp_delta={sp_after - stack_addr}] [{status_str}, {steps} steps]")

    all_passed = all(r[3] for r in results)
    return all_passed, results


if __name__ == "__main__":
    ok1, _ = run_routine1(verbose=True)
    ok2, _ = run_routine2(verbose=True)
    if ok1 and ok2:
        print("\nALL REAL FIRMWARE ROUTINES EXECUTED AND VERIFIED SUCCESSFULLY!")
    else:
        print("\nEXECUTION FAILED!")
        sys.exit(1)
