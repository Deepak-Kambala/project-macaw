"""
poc/aeon-r2-emulator/trace.py

Execution tracer for the Aeon R2 emulator.
Records detailed per-instruction state transitions:
  - PC before execution
  - Raw instruction bytes and disassembly
  - Registers modified
  - Memory reads and writes
  - PC after execution
"""

class TraceStep:
    def __init__(self, step_num, pc_before, raw_bytes, disasm, reg_changes, mem_events, pc_after):
        self.step_num = step_num
        self.pc_before = pc_before
        self.raw_bytes = raw_bytes
        self.disasm = disasm
        self.reg_changes = reg_changes # dict of reg -> (old_val, new_val)
        self.mem_events = mem_events   # list of (type, addr, size, val)
        self.pc_after = pc_after

    def format(self) -> str:
        hex_str = " ".join(f"{b:02x}" for b in self.raw_bytes).ljust(12)
        lines = [f"Step {self.step_num:03d} | PC: 0x{self.pc_before:06x} | {hex_str} | {self.disasm}"]
        for r, (old_v, new_v) in self.reg_changes.items():
            lines.append(f"          REG: {r} changed from 0x{old_v:08x} to 0x{new_v:08x}")
        for evt in self.mem_events:
            op, addr, size, val = evt
            lines.append(f"          MEM: {op} {size}B @ 0x{addr:08x} = 0x{val:08x}")
        lines.append(f"          NEXT_PC: 0x{self.pc_after:06x}")
        return "\n".join(lines)

class ExecutionTracer:
    def __init__(self):
        self.steps = []

    def record(self, step: TraceStep):
        self.steps.append(step)

    def print_trace(self):
        for s in self.steps:
            print(s.format())

    def get_full_trace_text(self) -> str:
        return "\n".join(s.format() for s in self.steps)
