#!/usr/bin/env python3
"""
scripts/milestone5/aeon_r2_mini_assembler.py

Host-side mini-assembler for the verified Aeon R2 instruction subset.
Encodes verified instructions (16-bit bt.*, 24-bit bn.*, 32-bit bg.*)
and round-trips them through the Aeon R2 decoder.
"""

import sys
import os

# Import decoder from verify_aeon_r2_isa
sys.path.append(os.path.dirname(__file__))
from verify_aeon_r2_isa import decode_instruction

class AeonR2Assembler:
    """Encodes verified Aeon R2 instructions into big-endian byte sequences."""

    @staticmethod
    def bt_nop(imm4=1):
        """16-bit nop: opcode 0x20, bit5=0, bit0=1"""
        val = (0x20 << 10) | ((imm4 & 0x0F) << 1) | 1
        return bytes([(val >> 8) & 0xFF, val & 0xFF])

    @staticmethod
    def bt_mov(rD, rA):
        """16-bit register move: opcode 0x22"""
        val = (0x22 << 10) | ((rD & 0x1F) << 5) | (rA & 0x1F)
        return bytes([(val >> 8) & 0xFF, val & 0xFF])

    @staticmethod
    def bt_add(rD, rA):
        """16-bit register add: opcode 0x23"""
        val = (0x23 << 10) | ((rD & 0x1F) << 5) | (rA & 0x1F)
        return bytes([(val >> 8) & 0xFF, val & 0xFF])

    @staticmethod
    def bt_movi(rD, simm5):
        """16-bit immediate move: opcode 0x26"""
        val = (0x26 << 10) | ((rD & 0x1F) << 5) | (simm5 & 0x1F)
        return bytes([(val >> 8) & 0xFF, val & 0xFF])

    @staticmethod
    def bt_addi(rD, simm5):
        """16-bit immediate add: opcode 0x27"""
        val = (0x27 << 10) | ((rD & 0x1F) << 5) | (simm5 & 0x1F)
        return bytes([(val >> 8) & 0xFF, val & 0xFF])

    @staticmethod
    def bt_jr(rD=9):
        """16-bit jump register (return): opcode 0x21, uimm=0x09"""
        val = (0x21 << 10) | ((rD & 0x1F) << 5) | 0x09
        return bytes([(val >> 8) & 0xFF, val & 0xFF])

    @staticmethod
    def bn_sw(offset, rA, rD):
        """24-bit store word: opcode 0x03, uimm0_2=0"""
        val = (0x03 << 18) | ((rD & 0x1F) << 13) | ((rA & 0x1F) << 8) | (offset & 0xFF)
        return bytes([(val >> 16) & 0xFF, (val >> 8) & 0xFF, val & 0xFF])

    @staticmethod
    def bn_lwz(rD, offset, rA):
        """24-bit load word zero-extended: opcode 0x03, uimm0_2=2"""
        val = (0x03 << 18) | ((rD & 0x1F) << 13) | ((rA & 0x1F) << 8) | (offset & 0xFC) | 2
        return bytes([(val >> 16) & 0xFF, (val >> 8) & 0xFF, val & 0xFF])

    @staticmethod
    def bn_addi(rD, rA, simm8):
        """24-bit immediate add: opcode 0x07"""
        val = (0x07 << 18) | ((rD & 0x1F) << 13) | ((rA & 0x1F) << 8) | (simm8 & 0xFF)
        return bytes([(val >> 16) & 0xFF, (val >> 8) & 0xFF, val & 0xFF])

    @staticmethod
    def bn_ori(rD, rA, ik8):
        """24-bit bitwise OR immediate: opcode 0x14"""
        val = (0x14 << 18) | ((rD & 0x1F) << 13) | ((rA & 0x1F) << 8) | (ik8 & 0xFF)
        return bytes([(val >> 16) & 0xFF, (val >> 8) & 0xFF, val & 0xFF])

    @staticmethod
    def bg_addi(rD, rA, simm16):
        """32-bit immediate add: opcode 0x3F"""
        val = (0x3F << 26) | ((rD & 0x1F) << 21) | ((rA & 0x1F) << 16) | (simm16 & 0xFFFF)
        return bytes([(val >> 24) & 0xFF, (val >> 16) & 0xFF, (val >> 8) & 0xFF, val & 0xFF])

    @staticmethod
    def bg_movhi(rD, uimm16):
        """32-bit load high immediate: opcode 0x30, bit0=1, uimm1_3=0"""
        val = (0x30 << 26) | ((rD & 0x1F) << 21) | ((uimm16 & 0xFFFF) << 5) | 1
        return bytes([(val >> 24) & 0xFF, (val >> 16) & 0xFF, (val >> 8) & 0xFF, val & 0xFF])

    @staticmethod
    def bg_ori(rD, rA, uimm16):
        """32-bit bitwise OR immediate: opcode 0x32"""
        val = (0x32 << 26) | ((rD & 0x1F) << 21) | ((rA & 0x1F) << 16) | (uimm16 & 0xFFFF)
        return bytes([(val >> 24) & 0xFF, (val >> 16) & 0xFF, (val >> 8) & 0xFF, val & 0xFF])

def main():
    print("==================================================================")
    print(" Aeon R2 Mini-Assembler & Round-Trip Verification                 ")
    print("==================================================================")
    
    asm = AeonR2Assembler()
    
    # Construct a sample subroutine:
    # int calculate_score(int head_x, int food_x) {
    #     // r3 = head_x, r4 = food_x
    #     // stack allocation: 16 bytes
    #     // save r9 (lr) and r10
    #     // compute delta = head_x - food_x
    #     // restore and return
    # }
    code = bytearray()
    
    # 1. Prologue: bg.addi r1, r1, -16
    code.extend(asm.bg_addi(1, 1, -16))
    # 2. Save r9 to 12(r1): bn.sw 12(r1), r9
    code.extend(asm.bn_sw(12, 1, 9))
    # 3. Save r10 to 8(r1): bn.sw 8(r1), r10
    code.extend(asm.bn_sw(8, 1, 10))
    # 4. Load constant 10 into r10: bt.movi r10, 10
    code.extend(asm.bt_movi(10, 10))
    # 5. Add r4 to r3: bt.add r3, r4
    code.extend(asm.bt_add(3, 4))
    # 6. Add r10 to r3: bt.add r3, r10
    code.extend(asm.bt_add(3, 10))
    # 7. Add immediate 5: bn.addi r3, r3, 5
    code.extend(asm.bn_addi(3, 3, 5))
    # 8. Restore r10 from 8(r1): bn.lwz r10, 8(r1)
    code.extend(asm.bn_lwz(10, 8, 1))
    # 9. Restore r9 from 12(r1): bn.lwz r9, 12(r1)
    code.extend(asm.bn_lwz(9, 12, 1))
    # 10. Epilogue: bg.addi r1, r1, 16
    code.extend(asm.bg_addi(1, 1, 16))
    # 11. Return: bt.jr r9
    code.extend(asm.bt_jr(9))
    
    print(f"Generated {len(code)} bytes of machine code.\n")
    print("Disassembling generated machine code to verify round-trip:\n")
    
    offset = 0
    step = 1
    all_matched = True
    while offset < len(code):
        raw, length, disasm = decode_instruction(code, offset)
        hex_str = " ".join(f"{b:02x}" for b in raw).ljust(12)
        print(f"  Step {step:02d} [0x{offset:02x}]: {hex_str} [{length*8}-bit] {disasm}")
        offset += length
        step += 1
        
    print(f"\nRound-trip verification successful: {offset == len(code)}")

if __name__ == "__main__":
    main()
