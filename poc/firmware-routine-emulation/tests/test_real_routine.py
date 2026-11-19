"""
poc/firmware-routine-emulation/tests/test_real_routine.py

Unit test suite validating the extraction, decoding, and execution of real
routines extracted from Samsung TV firmware binary (decompressed_main.bin).
"""

import unittest
import os
import sys

EMULATOR_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../aeon-r2-emulator"))
ROUTINES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(EMULATOR_DIR)
sys.path.append(ROUTINES_DIR)

from cpu import CPU
from decoder import Decoder
from run_routine import run_routine1, run_routine2
from reference_implementation import ref_routine1_array_lookup, ref_routine2_mem_copy

class TestRealFirmwareRoutines(unittest.TestCase):

    def setUp(self):
        self.r1_bin = os.path.join(ROUTINES_DIR, "routine1_array_lookup.bin")
        self.r2_bin = os.path.join(ROUTINES_DIR, "routine2_mem_copy.bin")
        self.assertTrue(os.path.isfile(self.r1_bin), f"Missing {self.r1_bin}")
        self.assertTrue(os.path.isfile(self.r2_bin), f"Missing {self.r2_bin}")

        with open(self.r1_bin, "rb") as f:
            self.r1_bytes = f.read()
        with open(self.r2_bin, "rb") as f:
            self.r2_bytes = f.read()

    def test_routine1_binary_attributes(self):
        """Verifies length and expected byte sequence of Routine 1."""
        self.assertEqual(len(self.r1_bytes), 13)
        self.assertEqual(self.r1_bytes.hex(), "4ce4088ce308e7015c67008529")

    def test_routine2_binary_attributes(self):
        """Verifies length and expected byte sequence of Routine 2."""
        self.assertEqual(len(self.r2_bytes), 38)
        self.assertEqual(self.r2_bytes.hex(), "98c0c0e00a61fc879b2640e53410e70018e4009cc19c81d0cfff9e98e188670d21029c248529")

    def test_routine1_instruction_decoding(self):
        """Verifies instruction-by-instruction decoding of Routine 1."""
        cpu = CPU(memory_size=0x10000)
        cpu.mem.load_bytes(0x1000, self.r1_bytes)
        pc = 0x1000

        expected_mnemonics = ["bn.slli", "bt.add", "bn.lh", "bn.extbz", "bt.jr"]
        for exp in expected_mnemonics:
            inst = Decoder.decode(cpu.mem, pc)
            self.assertEqual(inst.mnemonic, exp)
            pc += inst.length
        self.assertEqual(pc, 0x1000 + 13)

    def test_routine2_instruction_decoding(self):
        """Verifies instruction-by-instruction decoding of Routine 2."""
        cpu = CPU(memory_size=0x10000)
        cpu.mem.load_bytes(0x1000, self.r2_bytes)
        pc = 0x1000

        expected_mnemonics = [
            "bt.movi", "bg.movhi", "bg.addi", "bn.add", "bn.lbz",
            "bn.sbz", "bt.addi", "bt.addi", "bg.bnei", "bt.movi",
            "bt.mov", "bn.lwz", "bt.addi", "bt.jr"
        ]
        for exp in expected_mnemonics:
            inst = Decoder.decode(cpu.mem, pc)
            self.assertEqual(inst.mnemonic, exp)
            pc += inst.length
        self.assertEqual(pc, 0x1000 + 38)

    def test_routine1_execution_against_reference(self):
        """Executes Routine 1 across diverse test cases and verifies against reference model."""
        ok, results = run_routine1(verbose=False)
        self.assertTrue(ok)
        for _, _, _, res_hex, exp_hex, matched, steps in results:
            self.assertTrue(matched)
            self.assertEqual(res_hex, exp_hex)
            self.assertEqual(steps, 5)

    def test_routine2_execution_against_reference(self):
        """Executes Routine 2 across diverse test cases and verifies against reference model."""
        ok, results = run_routine2(verbose=False)
        self.assertTrue(ok)
        for _, src_hex, copied_hex, matched, steps in results:
            self.assertTrue(matched)
            self.assertEqual(src_hex, copied_hex)
            self.assertEqual(steps, 98)

    def test_counter_example_failed_branch_assumption(self):
        """
        Negative test proving that an incorrect assumption (multiplying bg.bnei displacement by 2)
        would fail this routine test.
        """
        val = 0xd0cfff9e
        rel13 = (val >> 3) & 0x1FFF
        if rel13 & 0x1000: rel13 -= 0x2000
        # Correct displacement in bytes is -13
        self.assertEqual(rel13, -13)
        # Incorrect assumption (halfword multiplication) produces -26
        incorrect_rel = rel13 * 2
        self.assertEqual(incorrect_rel, -26)
        # The loop top is at offset +10 from start, branch is at offset +23 -> 23 - 13 = 10
        self.assertEqual(23 + rel13, 10)
        self.assertNotEqual(23 + incorrect_rel, 10)

if __name__ == "__main__":
    unittest.main()
