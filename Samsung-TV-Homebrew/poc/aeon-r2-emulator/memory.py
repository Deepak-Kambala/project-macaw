"""
poc/aeon-r2-emulator/memory.py

Byte-addressable memory model for the Aeon R2 core.
All multi-byte memory accesses are strictly Big-Endian.
Tracks memory accesses for execution tracing.
"""

class Memory:
    def __init__(self, size=0x100000): # Default 1MB address space
        self.size = size
        self._mem = bytearray(size)
        self.access_log = []

    def load_bytes(self, addr: int, data: bytes):
        if addr + len(data) > self.size:
            raise ValueError(f"Data exceeds memory bounds (addr=0x{addr:x}, len={len(data)})")
        self._mem[addr:addr+len(data)] = data

    def read_u8(self, addr: int) -> int:
        if addr < 0 or addr >= self.size:
            raise MemoryError(f"Memory read out of bounds at 0x{addr:08x}")
        val = self._mem[addr]
        self.access_log.append(("READ", addr, 1, val))
        return val

    def write_u8(self, addr: int, val: int):
        if addr < 0 or addr >= self.size:
            raise MemoryError(f"Memory write out of bounds at 0x{addr:08x}")
        self._mem[addr] = val & 0xFF
        self.access_log.append(("WRITE", addr, 1, val & 0xFF))

    def read_u16(self, addr: int) -> int:
        if addr < 0 or addr + 2 > self.size:
            raise MemoryError(f"Memory read out of bounds at 0x{addr:08x}")
        val = (self._mem[addr] << 8) | self._mem[addr + 1]
        self.access_log.append(("READ", addr, 2, val))
        return val

    def write_u16(self, addr: int, val: int):
        if addr < 0 or addr + 2 > self.size:
            raise MemoryError(f"Memory write out of bounds at 0x{addr:08x}")
        self._mem[addr] = (val >> 8) & 0xFF
        self._mem[addr + 1] = val & 0xFF
        self.access_log.append(("WRITE", addr, 2, val & 0xFFFF))

    def read_u32(self, addr: int) -> int:
        if addr < 0 or addr + 4 > self.size:
            raise MemoryError(f"Memory read out of bounds at 0x{addr:08x}")
        val = (self._mem[addr] << 24) | (self._mem[addr + 1] << 16) | (self._mem[addr + 2] << 8) | self._mem[addr + 3]
        self.access_log.append(("READ", addr, 4, val))
        return val

    def write_u32(self, addr: int, val: int):
        if addr < 0 or addr + 4 > self.size:
            raise MemoryError(f"Memory write out of bounds at 0x{addr:08x}")
        self._mem[addr] = (val >> 24) & 0xFF
        self._mem[addr + 1] = (val >> 16) & 0xFF
        self._mem[addr + 2] = (val >> 8) & 0xFF
        self._mem[addr + 3] = val & 0xFF
        self.access_log.append(("WRITE", addr, 4, val & 0xFFFFFFFF))

    def clear_log(self):
        self.access_log.clear()
