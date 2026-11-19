"""
poc/firmware-routine-emulation/reference_implementation.py

Host reference implementations of the real routines extracted from
Samsung-TV-Homebrew/analysis/decompressed_main.bin.
Used for independent verification against the Aeon R2 emulator.
"""

from typing import List, Tuple

def ref_routine1_array_lookup(table: List[int], index: int) -> int:
    """
    Reference calculation for Routine 1 (0x005177, 13 bytes):
    - r3 = base pointer of array of 16-bit integers
    - r4 = element index
    - Reads 16-bit halfword at table[index]
    - Returns lowest byte zero-extended ((uint8_t)halfword) in r3.
    """
    if index < 0 or index >= len(table):
        raise IndexError(f"Index {index} out of range for table of length {len(table)}")
    val16 = table[index] & 0xFFFF
    return val16 & 0xFF

def ref_routine2_mem_copy(src_bytes: bytes) -> Tuple[int, bytes]:
    """
    Reference calculation for Routine 2 (0x0016E1, 38 bytes):
    - Copies 15 bytes from src_bytes[0..14]
    - Returns (status_code, copied_bytes) where status_code == 1 (Success)
    """
    if len(src_bytes) < 15:
        raise ValueError(f"Source buffer too small: {len(src_bytes)} bytes, required 15 bytes")
    copied = src_bytes[:15]
    return 1, copied
