#!/usr/bin/env python3
"""
poc/aeon-r2-emulator/run_program.py

Executes the verified 31-byte Aeon R2 test program on the emulator,
providing a complete execution trace, register inspection, and memory dump.
"""

import sys
import os

# Add local path
sys.path.append(os.path.dirname(__file__))
from runner import EmulatorRunner

def main():
    print("==================================================================")
    print(" Project Macaw: Aeon R2 Program Execution Trace                   ")
    print("==================================================================")

    # 31-byte machine code program
    code = bytes([
        0xFC, 0x21, 0xFF, 0xF0, # bg.addi r1, r1, -16
        0x0D, 0x21, 0x0C,       # bn.sw 12(r1), r9
        0x0D, 0x41, 0x08,       # bn.sw 8(r1), r10
        0x99, 0x4A,             # bt.movi r10, 10
        0x8C, 0x64,             # bt.add r3, r4
        0x8C, 0x6A,             # bt.add r3, r10
        0x1C, 0x63, 0x05,       # bn.addi r3, r3, 5
        0x0D, 0x41, 0x0A,       # bn.lwz r10, 8(r1)
        0x0D, 0x21, 0x0E,       # bn.lwz r9, 12(r1)
        0xFC, 0x21, 0x00, 0x10, # bg.addi r1, r1, 16
        0x85, 0x29              # bt.jr r9 (ret)
    ])

    print("Program Assembly:")
    asm_lines = [
        "0x00: bg.addi r1, r1, -16    ; Allocate 16 bytes stack frame",
        "0x04: bn.sw 12(r1), r9       ; Spill return address (r9)",
        "0x07: bn.sw 8(r1), r10       ; Spill callee-saved r10",
        "0x0a: bt.movi r10, 10        ; Load constant 10 into r10",
        "0x0c: bt.add r3, r4          ; r3 = r3 + r4 (head_x + food_x)",
        "0x0e: bt.add r3, r10         ; r3 = r3 + 10",
        "0x10: bn.addi r3, r3, 5      ; r3 = r3 + 5",
        "0x13: bn.lwz r10, 8(r1)      ; Restore r10 from stack",
        "0x16: bn.lwz r9, 12(r1)      ; Restore return address (r9)",
        "0x19: bg.addi r1, r1, 16     ; Deallocate stack frame",
        "0x1d: bt.jr r9               ; Return to caller"
    ]
    for line in asm_lines:
        print(f"  {line}")

    hex_str = " ".join(f"{b:02x}" for b in code)
    print(f"\nMachine Code ({len(code)} bytes):\n  {hex_str}\n")

    runner = EmulatorRunner()
    runner.load_program(code, 0x0000)

    # Initial inputs: head_x = 7 (r3), food_x = 3 (r4), initial r10 = 0
    initial_r3 = 7
    initial_r4 = 3
    runner.cpu.regs.write(3, initial_r3)
    runner.cpu.regs.write(4, initial_r4)
    runner.cpu.regs.write(10, 0x11112222) # Arbitrary initial value for r10 to verify restoration

    print(f"Initial State:")
    print(f"  PC:  0x{runner.cpu.regs.pc:06x}")
    print(f"  r1 (SP): 0x8000")
    print(f"  r3 (arg0): {initial_r3}")
    print(f"  r4 (arg1): {initial_r4}")
    print(f"  r9 (LR): 0xFFFFFFFF (sentinel to halt on return)")
    print(f"  r10: 0x{runner.cpu.regs.read(10):08x}\n")

    print("--- Instruction Execution Trace ---")
    result = runner.run(max_steps=50, initial_sp=0x8000, initial_lr=0xFFFFFFFF)
    runner.cpu.tracer.print_trace()

    print("\n--- Final CPU State ---")
    print(f"Halted: {result['halted']}")
    print(f"Steps Executed: {result['steps_executed']}")
    print(f"Final PC: 0x{result['final_pc']:06x}")
    print(f"r1 (SP): 0x{result['registers']['r1']:08x} (Expected: 0x00008000)")
    print(f"r3 (Return Value): {result['registers']['r3']} (Expected: {initial_r3 + initial_r4 + 10 + 5})")
    print(f"r4: {result['registers']['r4']} (Expected: {initial_r4})")
    print(f"r9 (LR): 0x{result['registers']['r9']:08x} (Expected: 0xffffffff)")
    print(f"r10: 0x{result['registers']['r10']:08x} (Expected: 0x11112222)")

    print("\n--- Final Stack Memory Dump (0x7FF0 - 0x8000) ---")
    for addr in range(0x7FF0, 0x8000, 4):
        val = runner.cpu.mem.read_u32(addr)
        print(f"  [0x{addr:04x}]: 0x{val:08x}")

    # Validation
    exp_r3 = initial_r3 + initial_r4 + 10 + 5
    success = (
        result['halted'] and
        result['registers']['r3'] == exp_r3 and
        result['registers']['r1'] == 0x8000 and
        result['registers']['r10'] == 0x11112222 and
        result['steps_executed'] == 11
    )
    print(f"\nExecution Verification: {'SUCCESS' if success else 'FAILURE'}")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
