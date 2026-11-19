#!/usr/bin/env python3
"""
poc/aeon-r2-emulator/tests/test_emulator.py

Comprehensive independent test suite for the MStar Aeon R2 emulator.
Tests decoding, CPU registers, memory model, arithmetic, memory access,
branching, function calls, execution limits, and the 31-byte test program.
"""

import unittest
import sys
import os

# Add emulator directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from cpu import CPU
from registers import Registers
from memory import Memory
from decoder import Decoder, UnsupportedInstructionError
from runner import EmulatorRunner

class TestAeonR2Decoder(unittest.TestCase):
    def setUp(self):
        self.mem = Memory(0x1000)

    def test_16bit_instruction_decoding(self):
        # bt.nop (0x20, bit0=1) -> 0x8001
        self.mem.load_bytes(0x00, bytes([0x80, 0x01]))
        inst = Decoder.decode(self.mem, 0x00)
        self.assertEqual(inst.length, 2)
        self.assertEqual(inst.mnemonic, "bt.nop")

        # bt.mov r3, r4 (opcode 0x22, rD=3, rA=4) -> (0x22 << 10) | (3 << 5) | 4 = 0x8864
        self.mem.load_bytes(0x02, bytes([0x88, 0x64]))
        inst = Decoder.decode(self.mem, 0x02)
        self.assertEqual(inst.length, 2)
        self.assertEqual(inst.mnemonic, "bt.mov")
        self.assertEqual(inst.fields["rD"], 3)
        self.assertEqual(inst.fields["rA"], 4)

        # bt.add r3, r4 (opcode 0x23, rD=3, rA=4) -> 0x8C64
        self.mem.load_bytes(0x04, bytes([0x8C, 0x64]))
        inst = Decoder.decode(self.mem, 0x04)
        self.assertEqual(inst.length, 2)
        self.assertEqual(inst.mnemonic, "bt.add")

        # bt.jr r9 (opcode 0x21, uimm=0x09, rD=9) -> 0x8529
        self.mem.load_bytes(0x06, bytes([0x85, 0x29]))
        inst = Decoder.decode(self.mem, 0x06)
        self.assertEqual(inst.length, 2)
        self.assertEqual(inst.mnemonic, "bt.jr")
        self.assertEqual(inst.fields["rD"], 9)

    def test_24bit_instruction_decoding(self):
        # bn.nop -> 0x000000
        self.mem.load_bytes(0x00, bytes([0x00, 0x00, 0x00]))
        inst = Decoder.decode(self.mem, 0x00)
        self.assertEqual(inst.length, 3)
        self.assertEqual(inst.mnemonic, "bn.nop")

        # bn.sw 12(r1), r9 -> 0x0D210C
        self.mem.load_bytes(0x03, bytes([0x0D, 0x21, 0x0C]))
        inst = Decoder.decode(self.mem, 0x03)
        self.assertEqual(inst.length, 3)
        self.assertEqual(inst.mnemonic, "bn.sw")
        self.assertEqual(inst.fields["rD"], 9)
        self.assertEqual(inst.fields["rA"], 1)
        self.assertEqual(inst.fields["offset"], 12)

        # bn.lwz r10, 8(r1) -> 0x0D410A (simm2_6 = 2 -> eff offset 8)
        self.mem.load_bytes(0x06, bytes([0x0D, 0x41, 0x0A]))
        inst = Decoder.decode(self.mem, 0x06)
        self.assertEqual(inst.length, 3)
        self.assertEqual(inst.mnemonic, "bn.lwz")
        self.assertEqual(inst.fields["rD"], 10)
        self.assertEqual(inst.fields["rA"], 1)
        self.assertEqual(inst.fields["offset"], 8)

        # bn.addi r3, r3, 5 -> 0x1C6305
        self.mem.load_bytes(0x09, bytes([0x1C, 0x63, 0x05]))
        inst = Decoder.decode(self.mem, 0x09)
        self.assertEqual(inst.length, 3)
        self.assertEqual(inst.mnemonic, "bn.addi")
        self.assertEqual(inst.fields["simm"], 5)

    def test_32bit_instruction_decoding(self):
        # bg.addi r1, r1, -16 -> 0xFC21FFF0
        self.mem.load_bytes(0x00, bytes([0xFC, 0x21, 0xFF, 0xF0]))
        inst = Decoder.decode(self.mem, 0x00)
        self.assertEqual(inst.length, 4)
        self.assertEqual(inst.mnemonic, "bg.addi")
        self.assertEqual(inst.fields["rD"], 1)
        self.assertEqual(inst.fields["rA"], 1)
        self.assertEqual(inst.fields["simm"], -16)

        # bg.movhi r4, 0x8000 -> 0xC0800001 (opcode 0x30, rD=4, imm=0x8000, bit0=1)
        val = (0x30 << 26) | (4 << 21) | (0x8000 << 5) | 1
        raw = bytes([(val >> 24) & 0xFF, (val >> 16) & 0xFF, (val >> 8) & 0xFF, val & 0xFF])
        self.mem.load_bytes(0x04, raw)
        inst = Decoder.decode(self.mem, 0x04)
        self.assertEqual(inst.length, 4)
        self.assertEqual(inst.mnemonic, "bg.movhi")
        self.assertEqual(inst.fields["rD"], 4)
        self.assertEqual(inst.fields["imm"], 0x8000)

    def test_unsupported_instruction_error(self):
        # Load illegal opcode (0xA0000000 -> opcode 0x28, not in supported set)
        self.mem.load_bytes(0x00, bytes([0xA0, 0x00, 0x00, 0x00]))
        with self.assertRaises(UnsupportedInstructionError):
            Decoder.decode(self.mem, 0x00)

class TestAeonR2CPUBehavior(unittest.TestCase):
    def setUp(self):
        self.cpu = CPU(0x10000)

    def test_r0_hardwired_zero(self):
        regs = self.cpu.regs
        regs.write(0, 0x12345678)
        self.assertEqual(regs.read(0), 0)

    def test_arithmetic_overflow_wrapping(self):
        regs = self.cpu.regs
        regs.write(3, 0xFFFFFFFF)
        # Execute bt.addi r3, 1 -> should wrap to 0
        # bt.addi r3, 1 = (0x27 << 10) | (3 << 5) | 1 = 0x9C61
        self.cpu.mem.load_bytes(0x00, bytes([0x9C, 0x61]))
        self.cpu.step()
        self.assertEqual(regs.read(3), 0x00000000)

    def test_load_and_store(self):
        regs = self.cpu.regs
        regs.write(1, 0x2000) # SP
        regs.write(4, 0xDEADBEEF)

        # bn.sw 4(r1), r4
        # opcode 0x03, rD=4, rA=1, simm8=4 -> 0x0C8104
        val = (0x03 << 18) | (4 << 13) | (1 << 8) | 4
        self.cpu.mem.load_bytes(0x00, bytes([(val >> 16) & 0xFF, (val >> 8) & 0xFF, val & 0xFF]))
        self.cpu.step()
        self.assertEqual(self.cpu.mem.read_u32(0x2004), 0xDEADBEEF)

        # bn.lwz r5, 4(r1)
        # simm2_6 = 1 (1 << 2 = 4), uimm0_2 = 2 -> offset byte = (1 << 2) | 2 = 6
        val_load = (0x03 << 18) | (5 << 13) | (1 << 8) | 6
        self.cpu.mem.load_bytes(0x03, bytes([(val_load >> 16) & 0xFF, (val_load >> 8) & 0xFF, val_load & 0xFF]))
        self.cpu.step()
        self.assertEqual(regs.read(5), 0xDEADBEEF)

    def test_conditional_branch_taken_and_not_taken(self):
        regs = self.cpu.regs
        regs.write(3, 10)

        # bn.beqi r3, 10, +6 (taken)
        # opcode 0x08, uimm0_2=0, rD=3, uimm10_3=10? wait, uimm10_3 is 3 bits (0..7). Let's use 5:
        regs.write(3, 5)
        # bn.beqi r3, 5, +6
        # opcode 0x08, rD=3, uimm10_3=5, rel8=3 (3*2 = +6)
        val_b = (0x08 << 18) | (3 << 13) | (5 << 10) | (3 << 2) | 0
        self.cpu.mem.load_bytes(0x00, bytes([(val_b >> 16) & 0xFF, (val_b >> 8) & 0xFF, val_b & 0xFF]))
        self.cpu.step()
        self.assertEqual(self.cpu.regs.pc, 0x06)

        # Not taken: r3 is 5, test if r3 == 2
        val_b_not = (0x08 << 18) | (3 << 13) | (2 << 10) | (3 << 2) | 0
        self.cpu.mem.load_bytes(0x06, bytes([(val_b_not >> 16) & 0xFF, (val_b_not >> 8) & 0xFF, val_b_not & 0xFF]))
        self.cpu.step()
        self.assertEqual(self.cpu.regs.pc, 0x09) # Advanced by instruction length (3 bytes)

class TestAeonR2ProgramExecution(unittest.TestCase):
    def test_31byte_subroutine_execution(self):
        """
        Executes the verified 31-byte test program:
          r3 = 7 (head_x), r4 = 3 (food_x)
          computes: r3 = 7 + 3 + 10 + 5 = 25
          allocates 16B stack, saves/restores r10 and r9, returns.
        """
        runner = EmulatorRunner()

        # The 31 bytes
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
        self.assertEqual(len(code), 31)

        runner.load_program(code, 0x0000)
        # Set inputs: r3=7, r4=3, sp=0x8000, lr=0xFFFFFFFF (halt on ret)
        runner.cpu.regs.write(3, 7)
        runner.cpu.regs.write(4, 3)

        res = runner.run(max_steps=50, initial_sp=0x8000, initial_lr=0xFFFFFFFF)

        self.assertTrue(res["halted"])
        self.assertFalse(res["terminated_by_limit"])
        self.assertEqual(res["steps_executed"], 11)

        # Expected return value in r3: 7 + 3 + 10 + 5 = 25
        self.assertEqual(res["registers"]["r3"], 25)
        # SP should be restored to 0x8000
        self.assertEqual(res["registers"]["r1"], 0x8000)
        # r10 should be restored to initial (0)
        self.assertEqual(res["registers"]["r10"], 0)

    def test_execution_limit_infinite_loop(self):
        """Tests that runner halts gracefully on max_steps limit."""
        runner = EmulatorRunner()
        # bn.j 0 (infinite loop jumping to itself)
        # opcode 0x0B, ik18=0 -> 0x02C00000 >> wait, 0x0B << 18 = 0x2C0000
        val = 0x0B << 18
        raw = bytes([(val >> 16) & 0xFF, (val >> 8) & 0xFF, val & 0xFF])
        runner.load_program(raw, 0x0000)

        res = runner.run(max_steps=20)
        self.assertTrue(res["terminated_by_limit"])
        self.assertEqual(res["steps_executed"], 20)

def main():
    unittest.main()

if __name__ == "__main__":
    main()
