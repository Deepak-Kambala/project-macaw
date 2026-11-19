import struct

# Minimal OpenRISC 1000 (OR1K / Aeon) Assembler & Disassembler Proof of Concept
# Based on OpenRISC Architecture Manual (or1k ISA)

REGISTERS = {f"r{i}": i for i in range(32)}

def asm_movhi(rd, imm16):
    # l.movhi rd, imm16: opcode 0x06
    return (0x06 << 26) | (REGISTERS[rd] << 21) | (imm16 & 0xffff)

def asm_ori(rd, ra, imm16):
    # l.ori rd, ra, imm16: opcode 0x2A
    return (0x2A << 26) | (REGISTERS[rd] << 21) | (REGISTERS[ra] << 16) | (imm16 & 0xffff)

def asm_add(rd, ra, rb):
    # l.add rd, ra, rb: opcode 0x38, sub-opcode 0x00
    return (0x38 << 26) | (REGISTERS[rd] << 21) | (REGISTERS[ra] << 16) | (REGISTERS[rb] << 11)

def asm_sub(rd, ra, rb):
    # l.sub rd, ra, rb: opcode 0x38, sub-opcode 0x02
    return (0x38 << 26) | (REGISTERS[rd] << 21) | (REGISTERS[ra] << 16) | (REGISTERS[rb] << 11) | 0x02

def asm_sw(ra, rb, imm16):
    # l.sw imm16(ra), rb: opcode 0x35
    # imm[15:11] in 25:21, imm[10:0] in 10:0
    imm_hi = (imm16 >> 11) & 0x1f
    imm_lo = imm16 & 0x7ff
    return (0x35 << 26) | (imm_hi << 21) | (REGISTERS[ra] << 16) | (REGISTERS[rb] << 11) | imm_lo

def asm_lwz(rd, ra, imm16):
    # l.lwz rd, imm16(ra): opcode 0x21
    return (0x21 << 26) | (REGISTERS[rd] << 21) | (REGISTERS[ra] << 16) | (imm16 & 0xffff)

def asm_jr(rb):
    # l.jr rb: opcode 0x11
    return (0x11 << 26) | (REGISTERS[rb] << 11)

def asm_nop(k=0):
    return (0x15 << 26) | (k & 0xffff)

def disassemble_word(word):
    op = (word >> 26) & 0x3f
    if op == 0x06:
        rd = (word >> 21) & 0x1f
        imm = word & 0xffff
        return f"l.movhi  r{rd}, 0x{imm:04x}"
    elif op == 0x2A:
        rd = (word >> 21) & 0x1f
        ra = (word >> 16) & 0x1f
        imm = word & 0xffff
        return f"l.ori    r{rd}, r{ra}, 0x{imm:04x}"
    elif op == 0x38:
        rd = (word >> 21) & 0x1f
        ra = (word >> 16) & 0x1f
        rb = (word >> 11) & 0x1f
        subop = word & 0x0f
        if subop == 0x00:
            return f"l.add    r{rd}, r{ra}, r{rb}"
        elif subop == 0x02:
            return f"l.sub    r{rd}, r{ra}, r{rb}"
        return f"l.alu38  r{rd}, r{ra}, r{rb}, subop={subop}"
    elif op == 0x21:
        rd = (word >> 21) & 0x1f
        ra = (word >> 16) & 0x1f
        imm = word & 0xffff
        return f"l.lwz    r{rd}, 0x{imm:04x}(r{ra})"
    elif op == 0x11:
        rb = (word >> 11) & 0x1f
        return f"l.jr     r{rb}"
    elif op == 0x15:
        return f"l.nop    0x{word & 0xffff:04x}"
    return f"unknown (op 0x{op:02x}, word 0x{word:08x})"

# Test tiny program: Snake update step
# Inputs: r3 = x, r4 = y, r5 = dir (0=up, 1=right, 2=down, 3=left)
# Return: r3 = new_x, r4 = new_y
instructions = [
    # Prologue: l.nop
    asm_nop(0),
    # If dir == 1 (right): add 1 to x
    asm_add("r3", "r3", "r5"),
    # Return to link register r9
    asm_jr("r9"),
    # Delay slot: l.nop
    asm_nop(0)
]

print("=== OpenRISC 1000 Assembled Test Program ===")
for i, inst in enumerate(instructions):
    be_bytes = struct.pack(">I", inst)
    disasm = disassemble_word(inst)
    print(f"  [{i*4:04x}]: {be_bytes.hex(' ')} -> {disasm}")

# Now verify: Can we disassemble real instructions from T-MXL0MASC.bin?
print("\n=== Disassembling Reset Vector at 0x000100 in T-MXL0MASC.bin ===")
with open("Samsung-TV-Homebrew/firmware/T-MXL0MASC.bin", "rb") as f:
    f.seek(0x100)
    raw = f.read(32)

for i in range(0, len(raw), 4):
    word = struct.unpack(">I", raw[i:i+4])[0]
    print(f"  [0x{0x100+i:04x}]: {raw[i:i+4].hex(' ')} (0x{word:08x}) -> {disassemble_word(word)}")
