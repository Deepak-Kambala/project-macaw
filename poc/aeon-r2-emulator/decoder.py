"""
poc/aeon-r2-emulator/decoder.py

Independent instruction decoder for the Aeon R2 variable-width architecture.
Adheres strictly to the SLEIGH specification in ghidra-aeon.
"""

class UnsupportedInstructionError(Exception):
    pass

class DecodedInstruction:
    def __init__(self, length, mnemonic, fields, disasm, raw_bytes):
        self.length = length
        self.mnemonic = mnemonic
        self.fields = fields
        self.disasm = disasm
        self.raw_bytes = raw_bytes

    def __repr__(self):
        return f"<{self.disasm} [{self.length}B]>"

class Decoder:
    @staticmethod
    def decode(mem, pc: int) -> DecodedInstruction:
        b0 = mem.read_u8(pc)
        prefix = (b0 >> 5) & 0x07

        # -------------------------------------------------------------
        # 16-bit instructions (i16_decoder = 4, range 0x80 - 0x9F)
        # -------------------------------------------------------------
        if prefix == 4:
            b1 = mem.read_u8(pc + 1)
            raw = bytes([b0, b1])
            val = (b0 << 8) | b1
            opcode = (val >> 10) & 0x3F
            rD = (val >> 5) & 0x1F
            rA = val & 0x1F
            simm5 = val & 0x1F
            if simm5 & 0x10: simm5 -= 0x20
            uimm = val & 0x1F

            if opcode == 0x20:
                bit5 = (val >> 5) & 1
                bit0 = val & 1
                imm4 = (val >> 1) & 0x0F
                if bit5 == 0 and bit0 == 1:
                    return DecodedInstruction(2, "bt.nop", {"imm": imm4}, f"bt.nop 0x{imm4:x}", raw)
                elif bit5 == 0 and bit0 == 0:
                    return DecodedInstruction(2, "bt.trap", {"imm": imm4}, f"bt.trap 0x{imm4:x}", raw)
            elif opcode == 0x21:
                if uimm == 0x09:
                    disasm = f"bt.jr r{rD}" + (" (ret)" if rD == 9 else "")
                    return DecodedInstruction(2, "bt.jr", {"rD": rD}, disasm, raw)
            elif opcode == 0x22:
                return DecodedInstruction(2, "bt.mov", {"rD": rD, "rA": rA}, f"bt.mov r{rD}, r{rA}", raw)
            elif opcode == 0x23:
                return DecodedInstruction(2, "bt.add", {"rD": rD, "rA": rA}, f"bt.add r{rD}, r{rA}", raw)
            elif opcode == 0x24:
                rel = val & 0x3FF
                if rel & 0x200: rel -= 0x400
                rel_bytes = rel * 2
                return DecodedInstruction(2, "bt.j", {"rel": rel_bytes}, f"bt.j {rel_bytes:+d}", raw)
            elif opcode == 0x26:
                return DecodedInstruction(2, "bt.movi", {"rD": rD, "simm": simm5}, f"bt.movi r{rD}, {simm5}", raw)
            elif opcode == 0x27:
                return DecodedInstruction(2, "bt.addi", {"rD": rD, "simm": simm5}, f"bt.addi r{rD}, {simm5}", raw)

            raise UnsupportedInstructionError(f"Unsupported 16-bit opcode 0x{opcode:02x} at PC=0x{pc:08x} (bytes: {raw.hex()})")

        # -------------------------------------------------------------
        # 24-bit instructions (i24_decoder = 0..3, range 0x00 - 0x7F)
        # -------------------------------------------------------------
        elif prefix < 4:
            b1 = mem.read_u8(pc + 1)
            b2 = mem.read_u8(pc + 2)
            raw = bytes([b0, b1, b2])
            val = (b0 << 16) | (b1 << 8) | b2
            opcode = (val >> 18) & 0x3F
            rD = (val >> 13) & 0x1F
            rA = (val >> 8) & 0x1F
            rB = (val >> 3) & 0x1F
            uimm0_2 = val & 0x03

            if opcode == 0x00:
                if uimm0_2 == 0 and rD == 0 and rA == 0 and (val & 0xFF) == 0:
                    return DecodedInstruction(3, "bn.nop", {}, "bn.nop", raw)
            elif opcode == 0x03:
                if uimm0_2 == 0:
                    # bn.sw: simm0_8(rA)
                    simm8 = val & 0xFF
                    if simm8 & 0x80: simm8 -= 0x100
                    return DecodedInstruction(3, "bn.sw", {"rD": rD, "rA": rA, "offset": simm8}, f"bn.sw {simm8}(r{rA}), r{rD}", raw)
                elif uimm0_2 == 2:
                    # bn.lwz: simm2_6 << 2
                    simm2_6 = (val >> 2) & 0x3F
                    if simm2_6 & 0x20: simm2_6 -= 0x40
                    eff_offset = simm2_6 << 2
                    return DecodedInstruction(3, "bn.lwz", {"rD": rD, "rA": rA, "offset": eff_offset}, f"bn.lwz r{rD}, {eff_offset}(r{rA})", raw)
            elif opcode == 0x07:
                simm8 = val & 0xFF
                if simm8 & 0x80: simm8 -= 0x100
                return DecodedInstruction(3, "bn.addi", {"rD": rD, "rA": rA, "simm": simm8}, f"bn.addi r{rD}, r{rA}, {simm8}", raw)
            elif opcode == 0x08:
                uimm10_3 = (val >> 10) & 0x07
                rel8 = (val >> 2) & 0xFF
                if rel8 & 0x80: rel8 -= 0x100
                rel_bytes = rel8 * 2
                if uimm0_2 == 0:
                    return DecodedInstruction(3, "bn.beqi", {"rD": rD, "imm": uimm10_3, "rel": rel_bytes}, f"bn.beqi r{rD}, {uimm10_3}, {rel_bytes:+d}", raw)
                elif uimm0_2 == 2:
                    return DecodedInstruction(3, "bn.bnei", {"rD": rD, "imm": uimm10_3, "rel": rel_bytes}, f"bn.bnei r{rD}, {uimm10_3}, {rel_bytes:+d}", raw)
            elif opcode == 0x0A:
                ik18 = val & 0x3FFFF
                if ik18 & 0x20000: ik18 -= 0x40000
                rel_bytes = ik18 * 2
                return DecodedInstruction(3, "bn.jal", {"rel": rel_bytes}, f"bn.jal {rel_bytes:+d}", raw)
            elif opcode == 0x0B:
                ik18 = val & 0x3FFFF
                if ik18 & 0x20000: ik18 -= 0x40000
                rel_bytes = ik18 * 2
                return DecodedInstruction(3, "bn.j", {"rel": rel_bytes}, f"bn.j {rel_bytes:+d}", raw)
            elif opcode == 0x10:
                uimm0_3 = val & 0x07
                alu_names = ["divs", "divu", "mulu", "muls", "add", "sub", "subb", "addc"]
                name = f"bn.{alu_names[uimm0_3]}"
                return DecodedInstruction(3, name, {"rD": rD, "rA": rA, "rB": rB}, f"{name} r{rD}, r{rA}, r{rB}", raw)
            elif opcode == 0x11:
                uimm0_3 = val & 0x07
                logic_names = ["op0", "op1", "op2", "op3", "and", "or", "xor", "nand"]
                name = f"bn.{logic_names[uimm0_3]}"
                return DecodedInstruction(3, name, {"rD": rD, "rA": rA, "rB": rB}, f"{name} r{rD}, r{rA}, r{rB}", raw)
            elif opcode == 0x14:
                ik = val & 0xFF
                return DecodedInstruction(3, "bn.ori", {"rD": rD, "rA": rA, "imm": ik}, f"bn.ori r{rD}, r{rA}, 0x{ik:x}", raw)
            elif opcode == 0x15:
                ik = val & 0xFF
                return DecodedInstruction(3, "bn.andi", {"rD": rD, "rA": rA, "imm": ik}, f"bn.andi r{rD}, r{rA}, 0x{ik:x}", raw)

            raise UnsupportedInstructionError(f"Unsupported 24-bit opcode 0x{opcode:02x} at PC=0x{pc:08x} (bytes: {raw.hex()})")

        # -------------------------------------------------------------
        # 32-bit instructions (i32_decoder = 5..7, range 0xA0 - 0xFF)
        # -------------------------------------------------------------
        else:
            b1 = mem.read_u8(pc + 1)
            b2 = mem.read_u8(pc + 2)
            b3 = mem.read_u8(pc + 3)
            raw = bytes([b0, b1, b2, b3])
            val = (b0 << 24) | (b1 << 16) | (b2 << 8) | b3
            opcode = (val >> 26) & 0x3F
            rD = (val >> 21) & 0x1F
            rA = (val >> 16) & 0x1F
            simm16 = val & 0xFFFF
            if simm16 & 0x8000: simm16 -= 0x10000
            uimm16 = val & 0xFFFF

            if opcode == 0x3F:
                return DecodedInstruction(4, "bg.addi", {"rD": rD, "rA": rA, "simm": simm16}, f"bg.addi r{rD}, r{rA}, {simm16}", raw)
            elif opcode == 0x30:
                bit0 = val & 1
                uimm1_3 = (val >> 1) & 0x07
                imm16 = (val >> 5) & 0xFFFF
                if bit0 == 1 and uimm1_3 == 0:
                    return DecodedInstruction(4, "bg.movhi", {"rD": rD, "imm": imm16}, f"bg.movhi r{rD}, 0x{imm16:04x}", raw)
            elif opcode == 0x31:
                return DecodedInstruction(4, "bg.andi", {"rD": rD, "rA": rA, "imm": uimm16}, f"bg.andi r{rD}, r{rA}, 0x{uimm16:04x}", raw)
            elif opcode == 0x32:
                return DecodedInstruction(4, "bg.ori", {"rD": rD, "rA": rA, "imm": uimm16}, f"bg.ori r{rD}, r{rA}, 0x{uimm16:04x}", raw)
            elif opcode == 0x34:
                uimm0_3 = val & 0x07
                simm16_5 = (val >> 16) & 0x1F
                if simm16_5 & 0x10: simm16_5 -= 0x20
                rel13 = (val >> 3) & 0x1FFF
                if rel13 & 0x1000: rel13 -= 0x2000
                rel_bytes = rel13 * 2
                if uimm0_3 == 2:
                    return DecodedInstruction(4, "bg.beqi", {"rD": rD, "imm": simm16_5, "rel": rel_bytes}, f"bg.beqi r{rD}, {simm16_5}, {rel_bytes:+d}", raw)
                elif uimm0_3 == 6:
                    return DecodedInstruction(4, "bg.bnei", {"rD": rD, "imm": simm16_5, "rel": rel_bytes}, f"bg.bnei r{rD}, {simm16_5}, {rel_bytes:+d}", raw)
            elif opcode == 0x36:
                return DecodedInstruction(4, "bg.xori", {"rD": rD, "rA": rA, "imm": uimm16}, f"bg.xori r{rD}, r{rA}, 0x{uimm16:04x}", raw)
            elif opcode == 0x39:
                bit0 = val & 1
                rel25 = (val >> 1) & 0x1FFFFFF
                if rel25 & 0x1000000: rel25 -= 0x2000000
                rel_bytes = rel25 * 2
                if bit0 == 0:
                    return DecodedInstruction(4, "bg.jal", {"rel": rel_bytes}, f"bg.jal {rel_bytes:+d}", raw)
                else:
                    return DecodedInstruction(4, "bg.j", {"rel": rel_bytes}, f"bg.j {rel_bytes:+d}", raw)
            elif opcode == 0x3B:
                uimm0_2 = val & 0x03
                simm2_14 = (val >> 2) & 0x3FFF
                if simm2_14 & 0x2000: simm2_14 -= 0x4000
                eff_offset = simm2_14 << 2
                if uimm0_2 in (0, 1):
                    return DecodedInstruction(4, "bg.sw", {"rD": rD, "rA": rA, "offset": eff_offset}, f"bg.sw {eff_offset}(r{rA}), r{rD}", raw)
                elif uimm0_2 == 2:
                    return DecodedInstruction(4, "bg.lwz", {"rD": rD, "rA": rA, "offset": eff_offset}, f"bg.lwz r{rD}, {eff_offset}(r{rA})", raw)

            raise UnsupportedInstructionError(f"Unsupported 32-bit opcode 0x{opcode:02x} at PC=0x{pc:08x} (bytes: {raw.hex()})")
