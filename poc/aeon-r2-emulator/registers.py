"""
poc/aeon-r2-emulator/registers.py

Register file implementation for the MStar Aeon R2 core.
Implements 32 32-bit GPRs (r0-r31) and Program Counter (PC).
Enforces hardware invariants:
  - r0 is hardwired to 0 (reads return 0, writes are discarded).
  - Register values are strictly masked to 32-bit unsigned integers (0x00000000 - 0xFFFFFFFF).
"""

class Registers:
    def __init__(self):
        # 32 general purpose registers
        self._regs = [0] * 32
        self.pc = 0

    def read(self, reg_num: int) -> int:
        if not (0 <= reg_num < 32):
            raise IndexError(f"Invalid register index: {reg_num}")
        if reg_num == 0:
            return 0
        return self._regs[reg_num]

    def write(self, reg_num: int, val: int):
        if not (0 <= reg_num < 32):
            raise IndexError(f"Invalid register index: {reg_num}")
        if reg_num == 0:
            return # r0 is read-only zero
        self._regs[reg_num] = val & 0xFFFFFFFF

    # Convenience aliases matching confirmed calling conventions
    @property
    def sp(self) -> int:
        return self.read(1)

    @sp.setter
    def sp(self, val: int):
        self.write(1, val)

    @property
    def fp(self) -> int:
        return self.read(2)

    @fp.setter
    def fp(self, val: int):
        self.write(2, val)

    @property
    def lr(self) -> int:
        return self.read(9)

    @lr.setter
    def lr(self, val: int):
        self.write(9, val)

    def snapshot(self) -> dict:
        return {f"r{i}": self._regs[i] for i in range(32)}
