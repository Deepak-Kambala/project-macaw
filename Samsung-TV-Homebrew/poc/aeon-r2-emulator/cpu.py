"""
poc/aeon-r2-emulator/cpu.py

Core CPU execution engine for MStar Aeon R2.
"""

try:
    from .registers import Registers
    from .memory import Memory
    from .decoder import Decoder
    from .instructions import execute_instruction
    from .tracer import TraceStep, ExecutionTracer
except ImportError:
    from registers import Registers
    from memory import Memory
    from decoder import Decoder
    from instructions import execute_instruction
    from tracer import TraceStep, ExecutionTracer

class CPU:
    def __init__(self, memory_size=0x100000):
        self.regs = Registers()
        self.mem = Memory(memory_size)
        self.tracer = ExecutionTracer()
        self.step_count = 0
        self.halted = False

    def reset(self, initial_pc=0):
        self.regs = Registers()
        self.regs.pc = initial_pc
        self.tracer = ExecutionTracer()
        self.step_count = 0
        self.halted = False

    def step(self) -> bool:
        """
        Executes a single instruction.
        Returns True if execution can continue, False if halted.
        """
        if self.halted:
            return False

        pc_before = self.regs.pc
        self.mem.clear_log()
        regs_before = self.regs.snapshot()

        # Fetch & decode
        inst = Decoder.decode(self.mem, pc_before)
        if inst is None:
            self.halted = True
            return False

        # Execute
        next_pc = execute_instruction(inst, self)

        # Invariant: r0 is always 0
        if self.regs.read(0) != 0:
            self.regs.write(0, 0)

        # Check register changes
        regs_after = self.regs.snapshot()
        reg_changes = {}
        for r_name in regs_before:
            if regs_before[r_name] != regs_after[r_name]:
                reg_changes[r_name] = (regs_before[r_name], regs_after[r_name])

        # Memory events
        mem_events = list(self.mem.access_log)

        # Advance PC
        self.regs.pc = next_pc
        self.step_count += 1

        # Record trace
        trace_step = TraceStep(
            step_num=self.step_count,
            pc_before=pc_before,
            raw_bytes=inst.raw_bytes,
            disasm=inst.disasm,
            reg_changes=reg_changes,
            mem_events=mem_events,
            pc_after=next_pc
        )
        self.tracer.record(trace_step)

        return not self.halted
