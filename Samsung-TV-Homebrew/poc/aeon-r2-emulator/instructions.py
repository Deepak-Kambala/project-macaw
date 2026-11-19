"""
poc/aeon-r2-emulator/instructions.py

Instruction semantic handlers for the Aeon R2 core.
All 32-bit register arithmetic is performed with strict unsigned 32-bit wrapping.
"""

def execute_instruction(inst, cpu):
    """
    Executes a DecodedInstruction on the CPU instance.
    Returns the next PC value.
    """
    mnem = inst.mnemonic
    f = inst.fields
    next_pc = cpu.regs.pc + inst.length

    # --- 16-bit instructions ---
    if mnem == "bt.nop":
        pass
    elif mnem == "bt.trap":
        cpu.halted = True
    elif mnem == "bt.mov":
        cpu.regs.write(f["rD"], cpu.regs.read(f["rA"]))
    elif mnem == "bt.add":
        val = (cpu.regs.read(f["rD"]) + cpu.regs.read(f["rA"])) & 0xFFFFFFFF
        cpu.regs.write(f["rD"], val)
    elif mnem == "bt.movi":
        cpu.regs.write(f["rD"], f["simm"] & 0xFFFFFFFF)
    elif mnem == "bt.addi":
        val = (cpu.regs.read(f["rD"]) + f["simm"]) & 0xFFFFFFFF
        cpu.regs.write(f["rD"], val)
    elif mnem == "bt.jr":
        target = cpu.regs.read(f["rD"])
        next_pc = target
        if f["rD"] == 9 and (target == 0 or target == 0xFFFFFFFF):
            cpu.halted = True
    elif mnem == "bt.j":
        next_pc = cpu.regs.pc + f["rel"]

    # --- 24-bit instructions ---
    elif mnem == "bn.nop":
        pass
    elif mnem == "bn.sw":
        addr = (cpu.regs.read(f["rA"]) + f["offset"]) & 0xFFFFFFFF
        val = cpu.regs.read(f["rD"])
        cpu.mem.write_u32(addr, val)
    elif mnem == "bn.lwz":
        addr = (cpu.regs.read(f["rA"]) + f["offset"]) & 0xFFFFFFFF
        val = cpu.mem.read_u32(addr)
        cpu.regs.write(f["rD"], val)
    elif mnem == "bn.addi":
        val = (cpu.regs.read(f["rA"]) + f["simm"]) & 0xFFFFFFFF
        cpu.regs.write(f["rD"], val)
    elif mnem == "bn.add":
        val = (cpu.regs.read(f["rA"]) + cpu.regs.read(f["rB"])) & 0xFFFFFFFF
        cpu.regs.write(f["rD"], val)
    elif mnem == "bn.sub":
        val = (cpu.regs.read(f["rA"]) - cpu.regs.read(f["rB"])) & 0xFFFFFFFF
        cpu.regs.write(f["rD"], val)
    elif mnem == "bn.and":
        val = (cpu.regs.read(f["rA"]) & cpu.regs.read(f["rB"])) & 0xFFFFFFFF
        cpu.regs.write(f["rD"], val)
    elif mnem == "bn.or":
        val = (cpu.regs.read(f["rA"]) | cpu.regs.read(f["rB"])) & 0xFFFFFFFF
        cpu.regs.write(f["rD"], val)
    elif mnem == "bn.xor":
        val = (cpu.regs.read(f["rA"]) ^ cpu.regs.read(f["rB"])) & 0xFFFFFFFF
        cpu.regs.write(f["rD"], val)
    elif mnem == "bn.ori":
        val = (cpu.regs.read(f["rA"]) | f["imm"]) & 0xFFFFFFFF
        cpu.regs.write(f["rD"], val)
    elif mnem == "bn.andi":
        val = (cpu.regs.read(f["rA"]) & f["imm"]) & 0xFFFFFFFF
        cpu.regs.write(f["rD"], val)
    elif mnem == "bn.beqi":
        if cpu.regs.read(f["rD"]) == f["imm"]:
            next_pc = cpu.regs.pc + f["rel"]
    elif mnem == "bn.bnei":
        if cpu.regs.read(f["rD"]) != f["imm"]:
            next_pc = cpu.regs.pc + f["rel"]
    elif mnem == "bn.j":
        next_pc = cpu.regs.pc + f["rel"]
    elif mnem == "bn.jal":
        cpu.regs.lr = (cpu.regs.pc + inst.length) & 0xFFFFFFFF
        next_pc = cpu.regs.pc + f["rel"]

    # --- 32-bit instructions ---
    elif mnem == "bg.addi":
        val = (cpu.regs.read(f["rA"]) + f["simm"]) & 0xFFFFFFFF
        cpu.regs.write(f["rD"], val)
    elif mnem == "bg.movhi":
        val = (f["imm"] << 16) & 0xFFFFFFFF
        cpu.regs.write(f["rD"], val)
    elif mnem == "bg.andi":
        val = (cpu.regs.read(f["rA"]) & f["imm"]) & 0xFFFFFFFF
        cpu.regs.write(f["rD"], val)
    elif mnem == "bg.ori":
        val = (cpu.regs.read(f["rA"]) | f["imm"]) & 0xFFFFFFFF
        cpu.regs.write(f["rD"], val)
    elif mnem == "bg.xori":
        val = (cpu.regs.read(f["rA"]) ^ f["imm"]) & 0xFFFFFFFF
        cpu.regs.write(f["rD"], val)
    elif mnem == "bg.sw":
        addr = (cpu.regs.read(f["rA"]) + f["offset"]) & 0xFFFFFFFF
        val = cpu.regs.read(f["rD"])
        cpu.mem.write_u32(addr, val)
    elif mnem == "bg.lwz":
        addr = (cpu.regs.read(f["rA"]) + f["offset"]) & 0xFFFFFFFF
        val = cpu.mem.read_u32(addr)
        cpu.regs.write(f["rD"], val)
    elif mnem == "bg.beqi":
        if cpu.regs.read(f["rD"]) == f["imm"]:
            next_pc = cpu.regs.pc + f["rel"]
    elif mnem == "bg.bnei":
        if cpu.regs.read(f["rD"]) != f["imm"]:
            next_pc = cpu.regs.pc + f["rel"]
    elif mnem == "bg.j":
        next_pc = cpu.regs.pc + f["rel"]
    elif mnem == "bg.jal":
        cpu.regs.lr = (cpu.regs.pc + inst.length) & 0xFFFFFFFF
        next_pc = cpu.regs.pc + f["rel"]

    else:
        raise NotImplementedError(f"No execution logic implemented for {mnem}")

    return next_pc & 0xFFFFFFFF
