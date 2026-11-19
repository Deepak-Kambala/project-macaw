"""
poc/aeon-r2-emulator/runner.py

High-level program runner for the Aeon R2 emulator.
Provides safe execution with instruction step limits and trace reporting.
"""

try:
    from .cpu import CPU
except ImportError:
    from cpu import CPU

class EmulatorRunner:
    def __init__(self, memory_size=0x100000):
        self.cpu = CPU(memory_size)

    def load_program(self, code_bytes: bytes, load_addr: int = 0x0000):
        self.cpu.mem.load_bytes(load_addr, code_bytes)
        self.cpu.regs.pc = load_addr

    def run(self, max_steps: int = 1000, initial_sp: int = 0x8000, initial_lr: int = 0xFFFFFFFF) -> dict:
        """
        Executes the loaded program until completion or max_steps limit.
        """
        self.cpu.regs.sp = initial_sp
        self.cpu.regs.lr = initial_lr
        self.cpu.halted = False

        steps_executed = 0
        while not self.cpu.halted and steps_executed < max_steps:
            self.cpu.step()
            steps_executed = self.cpu.step_count

        terminated_by_limit = (steps_executed >= max_steps and not self.cpu.halted)

        return {
            "steps_executed": steps_executed,
            "halted": self.cpu.halted,
            "terminated_by_limit": terminated_by_limit,
            "final_pc": self.cpu.regs.pc,
            "registers": self.cpu.regs.snapshot(),
            "tracer": self.cpu.tracer
        }
