#!/usr/bin/env python3
"""
scripts/milestone5/verify_aeon_r2_isa.py

Verifies the Aeon R2 variable-width (16-bit, 24-bit, 32-bit) instruction set
architecture against multiple independent firmware regions.
References:
  - Ghidra Aeon module (shinyquagsire23/ghidra-aeon)
  - MStar Chakra3 R2 backtrace source (r2_backtrace.c)
"""

import sys
import os
import struct

def get_instr_len(b0):
    """
    Aeon R2 instruction width is determined by the top 3 bits of byte 0:
      Bits [7:5] = 0..3 (0x00..0x7F): 24-bit instruction (bn.*)
      Bits [7:5] = 4    (0x80..0x9F): 16-bit instruction (bt.*)
      Bits [7:5] = 5..7 (0xA0..0xFF): 32-bit instruction (bg.*)
    """
    decoder = (b0 >> 5) & 0x07
    if decoder < 4:
        return 3, "24-bit (bn)"
    elif decoder == 4:
        return 2, "16-bit (bt)"
    else:
        return 4, "32-bit (bg)"

def decode_instruction(data, offset):
    if offset >= len(data):
        return None, 0, "EOF"
    
    b0 = data[offset]
    length, itype = get_instr_len(b0)
    
    if offset + length > len(data):
        return None, length, "TRUNCATED"
        
    raw_bytes = data[offset:offset+length]
    
    disasm = "unknown"
    
    if length == 2:
        val = (raw_bytes[0] << 8) | raw_bytes[1]
        opcode = (val >> 10) & 0x3F
        bit5 = (val >> 5) & 1
        bit0 = val & 1
        rD = (val >> 5) & 0x1F
        rA = val & 0x1F
        
        if opcode == 0x20:
            if bit5 == 0 and bit0 == 1:
                uimm = (val >> 1) & 0x0F
                disasm = f"bt.nop 0x{uimm:x}"
            elif bit5 == 0 and bit0 == 0:
                uimm = (val >> 1) & 0x0F
                disasm = f"bt.trap 0x{uimm:x}"
            elif bit5 == 1 and bit0 == 0:
                simm = val & 0x1F
                if simm & 0x10: simm -= 0x20
                disasm = f"bt.swst {simm}"
        elif opcode == 0x21:
            uimm = val & 0x1F
            if uimm == 0 and bit5 == 0:
                disasm = "bt.rfe"
            elif uimm == 0x08:
                disasm = f"bt.jalr r{rD}"
            elif uimm == 0x09:
                if rD == 9:
                    disasm = "bt.jr r9 (ret)"
                else:
                    disasm = f"bt.jr r{rD}"
        elif opcode == 0x22:
            disasm = f"bt.mov r{rD}, r{rA}"
        elif opcode == 0x23:
            disasm = f"bt.add r{rD}, r{rA}"
        elif opcode == 0x24:
            rel = val & 0x3FF
            if rel & 0x200: rel -= 0x400
            disasm = f"bt.j {rel * 2:+d}"
        elif opcode == 0x25:
            simm = val & 0x1F
            if simm & 0x10: simm -= 0x20
            disasm = f"bt.movhi r{rD}, {simm}"
        elif opcode == 0x26:
            simm = val & 0x1F
            if simm & 0x10: simm -= 0x20
            disasm = f"bt.movi r{rD}, {simm}"
        elif opcode == 0x27:
            simm = val & 0x1F
            if simm & 0x10: simm -= 0x20
            disasm = f"bt.addi r{rD}, {simm}"
        else:
            disasm = f"bt.op_{opcode:02x}"
            
    elif length == 3:
        val = (raw_bytes[0] << 16) | (raw_bytes[1] << 8) | raw_bytes[2]
        opcode = (val >> 18) & 0x3F
        uimm0_2 = val & 0x03
        rD = (val >> 13) & 0x1F
        rA = (val >> 8) & 0x1F
        rB = (val >> 3) & 0x1F
        
        if opcode == 0x00:
            if uimm0_2 == 0 and rD == 0 and rA == 0 and (val & 0xFF) == 0:
                disasm = "bn.nop"
            elif uimm0_2 == 0:
                offset_val = (val & 0xFF)
                disasm = f"bn.sw_0 {offset_val}(r{rA}), r{rD}"
            else:
                disasm = f"bn.op0_{uimm0_2} r{rD}, r{rA}, {val & 0xFF}"
        elif opcode == 0x01:
            ik13 = val & 0x1FFF
            disasm = f"bn.movhi r{rD}, 0x{ik13:x}"
        elif opcode == 0x02:
            offset_val = (val & 0x3F) << 1
            disasm = f"bn.lh r{rD}, {offset_val}(r{rA})"
        elif opcode == 0x03:
            if uimm0_2 == 0:
                offset_val = (val & 0xFF)
                disasm = f"bn.sw 0x{offset_val:x}(r{rA}), r{rD}"
            elif uimm0_2 == 1:
                offset_val = (val & 0xFF)
                disasm = f"bn.sh_1 0x{offset_val:x}(r{rA}), r{rD}"
            elif uimm0_2 == 2:
                offset_val = (val & 0xFF)
                disasm = f"bn.lwz r{rD}, 0x{offset_val:x}(r{rA})"
            elif uimm0_2 == 3:
                offset_val = (val & 0xFF)
                disasm = f"bn.sh_2 0x{offset_val:x}(r{rA}), r{rD}"
        elif opcode == 0x04:
            offset_val = (val & 0xFF)
            disasm = f"bn.lbz r{rD}, 0x{offset_val:x}(r{rA})"
        elif opcode == 0x05:
            offset_val = (val & 0xFF)
            disasm = f"bn.lbs r{rD}, 0x{offset_val:x}(r{rA})"
        elif opcode == 0x06:
            offset_val = (val & 0xFF)
            disasm = f"bn.sbz 0x{offset_val:x}(r{rA}), r{rD}"
        elif opcode == 0x07:
            simm = val & 0xFF
            if simm & 0x80: simm -= 0x100
            disasm = f"bn.addi r{rD}, r{rA}, {simm}"
        elif opcode == 0x08:
            uimm10_3 = (val >> 10) & 0x07
            rel = (val >> 2) & 0xFF
            if rel & 0x80: rel -= 0x100
            if uimm0_2 == 0:
                disasm = f"bn.beqi r{rD}, {uimm10_3}, {rel * 2:+d}"
            elif uimm0_2 == 1:
                rel16 = (val >> 2) & 0xFFFF
                disasm = f"bn.bf {rel16:+d}"
            elif uimm0_2 == 2:
                disasm = f"bn.bnei r{rD}, {uimm10_3}, {rel * 2:+d}"
            elif uimm0_2 == 3:
                rel16 = (val >> 2) & 0xFFFF
                disasm = f"bn.bnf {rel16:+d}"
        elif opcode == 0x09:
            uimm10_3 = (val >> 10) & 0x07
            rel = (val >> 2) & 0xFF
            if rel & 0x80: rel -= 0x100
            names = ["bn.blesi", "bn.bleui", "bn.bgtsi", "bn.bgtui"]
            disasm = f"{names[uimm0_2]} r{rD}, {uimm10_3}, {rel * 2:+d}"
        elif opcode == 0x0A:
            ik18 = val & 0x3FFFF
            if ik18 & 0x20000: ik18 -= 0x40000
            disasm = f"bn.jal {ik18 * 2:+d}"
        elif opcode == 0x0B:
            ik18 = val & 0x3FFFF
            if ik18 & 0x20000: ik18 -= 0x40000
            disasm = f"bn.j {ik18 * 2:+d}"
        elif opcode == 0x0D:
            ik13 = val & 0x1FFF
            disasm = f"bn.movhi r{rD}, 0x{ik13:x}"
        elif opcode == 0x10:
            uimm0_3 = val & 0x07
            alu_ops = ["divs", "divu", "mulu", "muls", "add", "sub", "subb", "addc"]
            disasm = f"bn.{alu_ops[uimm0_3]} r{rD}, r{rA}, r{rB}"
        elif opcode == 0x11:
            uimm0_3 = val & 0x07
            bit_ops = ["op11_0", "op11_1", "op11_2", "op11_3", "and", "or", "xor", "nand"]
            disasm = f"bn.{bit_ops[uimm0_3]} r{rD}, r{rA}, r{rB}"
        elif opcode == 0x13:
            uimm0_3 = val & 0x07
            uimm3_5 = (val >> 3) & 0x1F
            shift_ops = ["slli", "srli", "srai", "rori", "sll", "srl", "sra", "ror"]
            if uimm0_3 < 4:
                disasm = f"bn.{shift_ops[uimm0_3]} r{rD}, r{rA}, {uimm3_5}"
            else:
                disasm = f"bn.{shift_ops[uimm0_3]} r{rD}, r{rA}, r{rB}"
        elif opcode == 0x14:
            ik = val & 0xFF
            disasm = f"bn.ori r{rD}, r{rA}, 0x{ik:x}"
        elif opcode == 0x15:
            ik = val & 0xFF
            disasm = f"bn.andi r{rD}, r{rA}, 0x{ik:x}"
        else:
            disasm = f"bn.op_{opcode:02x}"
            
    elif length == 4:
        val = (raw_bytes[0] << 24) | (raw_bytes[1] << 16) | (raw_bytes[2] << 8) | raw_bytes[3]
        opcode = (val >> 26) & 0x3F
        rD = (val >> 21) & 0x1F
        rA = (val >> 16) & 0x1F
        simm16 = val & 0xFFFF
        if simm16 & 0x8000: simm16 -= 0x10000
        uimm16 = val & 0xFFFF
        
        if opcode == 0x30:
            bit0 = val & 1
            uimm1_3 = (val >> 1) & 0x07
            if bit0 == 0:
                sf_ops = ["bg.sfeqi", "bg.op30_2", "bg.sfnei", "bg.op30_6", "bg.sflesi", "bg.sfleui", "bg.sfgtsi", "bg.sfgti"]
                disasm = f"{sf_ops[uimm1_3]} r{rD}, 0x{(val >> 5) & 0xFFFF:x}"
            else:
                if uimm1_3 == 0:
                    disasm = f"bg.movhi r{rD}, 0x{(val >> 5) & 0xFFFF:x}"
                elif uimm1_3 == 2:
                    disasm = f"bg.mtspr1 r{rD}, spr_0x{(val >> 5) & 0xFFFF:x}"
                elif uimm1_3 == 3:
                    disasm = f"bg.mfspr1 r{rD}, spr_0x{(val >> 5) & 0xFFFF:x}"
                elif uimm1_3 == 6:
                    disasm = f"bg.mtspr r{rA}, r{rD}, spr_0x{(val >> 5) & 0xFFFF:x}"
                elif uimm1_3 == 7:
                    disasm = f"bg.mfspr r{rD}, r{rA}, spr_0x{(val >> 5) & 0xFFFF:x}"
                else:
                    disasm = f"bg.op30_1_{uimm1_3} r{rD}, 0x{(val >> 5) & 0xFFFF:x}"
        elif opcode == 0x31:
            disasm = f"bg.andi r{rD}, r{rA}, 0x{uimm16:x}"
        elif opcode == 0x32:
            disasm = f"bg.ori r{rD}, r{rA}, 0x{uimm16:x}"
        elif opcode == 0x34:
            uimm0_3 = val & 0x07
            b_ops = ["bg.blesi", "bg.bleui", "bg.beqi", "bg.b011i", "bg.bgtsi", "bg.bgtui", "bg.bnei", "bg.b111i"]
            simm16_5 = (val >> 16) & 0x1F
            disasm = f"{b_ops[uimm0_3]} r{rD}, {simm16_5}, {(val >> 3) & 0x1FFF}"
        elif opcode == 0x35:
            uimm0_3 = val & 0x07
            b_ops = ["bg.bles", "bg.ble", "bg.beq", "bg.bf", "bg.bgts", "bg.bgt", "bg.bne", "bg.b111"]
            disasm = f"{b_ops[uimm0_3]} r{rD}, r{rA}, {(val >> 3) & 0x1FFF}"
        elif opcode == 0x36:
            disasm = f"bg.xori r{rD}, r{rA}, 0x{uimm16:x}"
        elif opcode == 0x39:
            bit0 = val & 1
            rel = (val >> 1) & 0x1FFFFFF
            if rel & 0x1000000: rel -= 0x2000000
            if bit0 == 0:
                disasm = f"bg.jal {rel * 2:+d}"
            else:
                disasm = f"bg.j {rel * 2:+d}"
        elif opcode == 0x3A:
            bit0 = val & 1
            simm1_15 = (val >> 1) & 0x7FFF
            if simm1_15 & 0x4000: simm1_15 -= 0x8000
            simm1_15 <<= 1
            if bit0 == 0:
                disasm = f"bg.lhs r{rD}, {simm1_15}(r{rA})"
            else:
                disasm = f"bg.lhz r{rD}, {simm1_15}(r{rA})"
        elif opcode == 0x3B:
            uimm0_2 = val & 0x03
            simm2_14 = (val >> 2) & 0x3FFF
            if simm2_14 & 0x2000: simm2_14 -= 0x4000
            simm2_14 <<= 2
            if uimm0_2 in (0, 1):
                disasm = f"bg.sw {simm2_14}(r{rA}), r{rD}"
            elif uimm0_2 == 2:
                disasm = f"bg.lwz r{rD}, {simm2_14}(r{rA})"
            elif uimm0_2 == 3:
                disasm = f"bg.sh {simm2_14}(r{rA}), r{rD}"
        elif opcode == 0x3C:
            disasm = f"bg.lbz r{rD}, 0x{simm16:x}(r{rA})"
        elif opcode == 0x3E:
            disasm = f"bg.sbz 0x{simm16:x}(r{rA}), r{rD}"
        elif opcode == 0x3F:
            disasm = f"bg.addi r{rD}, r{rA}, {simm16}"
        else:
            disasm = f"bg.op_{opcode:02x}"
            
    return raw_bytes, length, disasm

def disassemble_region(data, start_offset, num_instructions, region_name):
    print(f"\n=======================================================")
    print(f" Region: {region_name} (Start: 0x{start_offset:06x})")
    print(f"=======================================================")
    offset = start_offset
    inst_count = 0
    stats = {2: 0, 3: 0, 4: 0}
    
    while inst_count < num_instructions and offset < len(data):
        raw_bytes, length, disasm = decode_instruction(data, offset)
        if raw_bytes is None:
            break
        stats[length] += 1
        hex_str = " ".join(f"{b:02x}" for b in raw_bytes).ljust(12)
        print(f"0x{offset:06x}:  {hex_str}  [{length*8}-bit]  {disasm}")
        offset += length
        inst_count += 1
        
    print(f"--- Instruction Statistics: 16-bit: {stats[2]}, 24-bit: {stats[3]}, 32-bit: {stats[4]} ---")
    return stats

def main():
    fw_path = "Samsung-TV-Homebrew/firmware/T-MXL0MASC.bin"
    decomp_path = "Samsung-TV-Homebrew/analysis/decompressed_main.bin"
    
    if not os.path.exists(fw_path) or not os.path.exists(decomp_path):
        print("Required binaries not found!")
        sys.exit(1)
        
    with open(fw_path, "rb") as f:
        fw_data = f.read()
        
    with open(decomp_path, "rb") as f:
        decomp_data = f.read()
        
    print("==================================================================")
    print(" Aeon R2 Instruction Set Verification Across Independent Regions ")
    print("==================================================================")
    
    # Region A: Bootloader reset vector in T-MXL0MASC.bin at 0x000100
    disassemble_region(fw_data, 0x000100, 20, "Region A: Bootloader Reset Vector (0x000100 in T-MXL0MASC.bin)")
    
    # Region B: Exception vector table in T-MXL0MASC.bin at 0x020280
    disassemble_region(fw_data, 0x020280, 25, "Region B: Exception Vector Frame Save (0x020280 in T-MXL0MASC.bin)")
    
    # Region C: Decompressed Main Firmware Entry Point (0x000000)
    disassemble_region(decomp_data, 0x000000, 25, "Region C: Main Application Entry Point (0x000000 in decompressed_main.bin)")

    # Region D: Function Prologue in Main Firmware at 0x001000
    disassemble_region(decomp_data, 0x001000, 20, "Region D: Subroutine Prologue (0x001000 in decompressed_main.bin)")

if __name__ == "__main__":
    main()
