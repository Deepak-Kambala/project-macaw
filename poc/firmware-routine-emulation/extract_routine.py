#!/usr/bin/env python3
"""
poc/firmware-routine-emulation/extract_routine.py

Extracts exact machine code bytes for verified real routines from the decompressed
MStar television firmware binary (Samsung-TV-Homebrew/analysis/decompressed_main.bin).
Preserves binary artifacts independently and generates routine_metadata.json.
"""

import os
import json
import hashlib

FIRMWARE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Samsung-TV-Homebrew/analysis/decompressed_main.bin"))
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

ROUTINE_DEFS = {
    "routine1_array_lookup": {
        "name": "Halfword Array Element Lookup / Extractor",
        "description": "Calculates array index offset (r4 << 1), adds base pointer (r3), loads 16-bit halfword from memory, zero-extends lower byte into r3, and returns.",
        "start_offset": 0x005177,
        "end_offset": 0x005184,
        "length_bytes": 13,
        "instruction_count": 5,
        "calling_convention": {
            "inputs": {
                "r3": "Base pointer to array of uint16_t elements",
                "r4": "Array element index (uint32_t)",
                "r9": "Return address (LR)"
            },
            "outputs": {
                "r3": "Extracted byte value ((uint8_t)array[index])"
            },
            "clobbered_registers": ["r7"]
        }
    },
    "routine2_mem_copy": {
        "name": "15-Byte Memory Buffer Copy Loop",
        "description": "Copies a 15-byte fixed buffer from source pointer (r5) to static global buffer (0x00529B26), loops with counter r6 from 0 to 15, sets return value r3 = 1, restores LR r9 from stack, and returns.",
        "start_offset": 0x0016E1,
        "end_offset": 0x001707,
        "length_bytes": 38,
        "instruction_count": 14,
        "calling_convention": {
            "inputs": {
                "r5": "Source memory buffer pointer (15 bytes readable)",
                "r1": "Stack pointer (top word contains saved r9)",
                "r9": "Return address (restored from stack frame)"
            },
            "outputs": {
                "r3": "Status return code (1 = TRUE / Success)",
                "r1": "Stack pointer restored (r1 + 4)"
            },
            "memory_effects": {
                "destination_address": "0x00529B26",
                "length_bytes": 15
            },
            "clobbered_registers": ["r4", "r6", "r7"]
        }
    }
}

def extract_routines():
    if not os.path.isfile(FIRMWARE_PATH):
        raise FileNotFoundError(f"Firmware binary not found at: {FIRMWARE_PATH}")

    with open(FIRMWARE_PATH, "rb") as f:
        firmware_bytes = f.read()

    firmware_sha256 = hashlib.sha256(firmware_bytes).hexdigest()
    print(f"Loaded firmware: {len(firmware_bytes)} bytes (SHA-256: {firmware_sha256})")

    metadata = {
        "source_binary": "Samsung-TV-Homebrew/analysis/decompressed_main.bin",
        "firmware_sha256": firmware_sha256,
        "routines": {}
    }

    for key, info in ROUTINE_DEFS.items():
        start = info["start_offset"]
        end = info["end_offset"]
        code_bytes = firmware_bytes[start:end]

        assert len(code_bytes) == info["length_bytes"], f"Length mismatch for {key}: expected {info['length_bytes']}, got {len(code_bytes)}"

        bin_path = os.path.join(OUT_DIR, f"{key}.bin")
        with open(bin_path, "wb") as bf:
            bf.write(code_bytes)

        code_hash = hashlib.sha256(code_bytes).hexdigest()
        info["raw_hex"] = code_bytes.hex()
        info["sha256"] = code_hash
        info["binary_file"] = f"{key}.bin"
        metadata["routines"][key] = info

        print(f"Extracted {key}: {len(code_bytes)} bytes -> {bin_path} (SHA-256: {code_hash[:16]}...)")

    meta_path = os.path.join(OUT_DIR, "routine_metadata.json")
    with open(meta_path, "w") as mf:
        json.dump(metadata, mf, indent=2)
    print(f"Saved metadata: {meta_path}")

if __name__ == "__main__":
    extract_routines()
