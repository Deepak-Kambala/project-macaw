# Snake Host Implementation & Firmware Integration Readiness

**Target Hardware:** Samsung UA23H4003ARLXL (Chassis U8BA, MStar Macaw12 Platform)  
**Host Prototype:** `poc/snake-host/` (`snake_sim.py`, `mock_ge.py`, `integration_demo.py`)  
**Date:** November 2026  
**Status:** Architecture Evaluated / Integration Roadmapped  

---

## 1. Executive Summary

Milestone 6 delivered a functional host-side Snake engine (`snake_sim.py`) coupled with a deterministic MockGE graphics pipeline (`mock_ge.py`). Milestone 7 re-evaluated this architecture against the newly reconstructed television firmware runtime (superloop scheduling, hardware GE blitting, and remote IR input dispatch).

**Key Finding:** The host-side Snake architecture cleanly decouples game logic from graphics rendering. However, **direct injection of Snake into television firmware remains strictly unfeasible at this milestone** due to boot integrity checks, watchdog timing constraints, and the lack of a verified hardware recovery mechanism.

---

## 2. Decoupling Review: Game Logic vs. Graphics

The host prototype implements a clean three-tier separation of concerns:
1. **Model Layer (`snake_sim.py`):**
   - Grid-based coordinate mathematics ($X \in [0, 39], Y \in [0, 23]$ on a $40 \times 24$ board).
   - Zero graphics dependencies; state updates operate purely on numeric coordinate tuples `(x, y)`.
   - Discrete tick stepping: `SnakeGame.step()` advances state by one simulation frame.
2. **Graphics Interface Layer (`mock_ge.py`):**
   - Implements `MockGE` exposing standard MStar Graphic Engine APIs: `fill_rect(x, y, w, h, color)`.
   - Deterministic pixel manipulation into a 32-bit linear framebuffer (`bytearray(1280 * 720 * 4)`).
   - Tracks drawing metrics: call counts, pixel write counts, and boundary checks.
3. **Orchestration Layer (`integration_demo.py`):**
   - Translates abstract game entity positions into pixel coordinates:
     $$X_{\text{pixel}} = X_{\text{cell}} \times 20 + \text{OFFSET}_X$$
     $$Y_{\text{pixel}} = Y_{\text{cell}} \times 20 + \text{OFFSET}_Y$$
   - Emits batch `FillRect` calls to render the board background, grid borders, snake body segments, and fruit.

---

## 3. Comprehensive Firmware Interface Readiness Matrix

| Requirement | Current Host Implementation | Physical Firmware Evidence | Status | Technical Assessment |
| :--- | :--- | :--- | :---: | :--- |
| **Periodic Tick Update** | Python system timer / loop (`time.sleep`) | `timer_cb/timer_cb.c` callback registry & watchdog (`0xA0006010`) | **ARCHITECTURALLY MAPPED** | A 30–50 ms timer callback slot would be required. However, static timer table capacity is limited, and long-running callbacks risk triggering watchdog resets. |
| **Directional Input** | Host keyboard events (`Arrow keys`, `WASD`) | `msKeypad` driver & IR scan register (`IR:%02dh`, `KEY_UP`..`KEY_RIGHT`) | **ARCHITECTURALLY MAPPED** | IR codes for navigation (`0x60`, `0x61`, `0x65`, `0x62`) and ENTER (`0x68`) match Snake controls. Hooking into `MApp_ZUI_APIwindow` requires patching flash code. |
| **Rectangle Rendering** | `MockGE.fill_rect` in Python bytearray | `MDrv_GE_FillRect` hardware blitter (`0x17BD3E` in `decompressed_main.bin`) | **ARCHITECTURALLY MAPPED** | `MDrv_GE_FillRect` is functionally identical to `MockGE.fill_rect`. Calling it in firmware requires active GE hardware context and valid buffer pointers. |
| **Display Plane Output** | Host PNG / ASCII framebuffer inspection | `MDrv_GOP_Init`, `HAL_GOP_SetDWINMIU`, GWIN 1280x720 plane | **ARCHITECTURALLY MAPPED** | OSD framebuffer resides in MIU DRAM (`0x8C000000`). Displaying custom graphics requires synchronizing buffer flips (`dcMain`/`dcBuff`) with V-Sync. |
| **Binary Memory Space** | Host RAM | DRAM KSEG0 (`0x80000000`), SRAM (`0xB0000000`) | **CONFIRMED** | A custom Aeon R2 Snake binary (~2–4 KB) could fit in unused padding within DRAM. |
| **Execution Safety & Recovery** | Safe host Python process | SPI NOR Flash (Winbond W25Q32, 4 MB) | **UNRESOLVED / DANGEROUS** | Physical UART is unverified. Bootloader recovery fallback is unproven. Modifying flash carries an unacceptable risk of permanently bricking the TV. |

---

## 4. Integration Feasibility Assessment

### 4.1 Theoretical Path (Why it works on paper)
If firmware code modification were safe:
1. Compile the Snake logic and GE render calls into Aeon R2 machine code using a verified cross-compiler.
2. Locate an unused factory/service menu dialog in ZUI (such as `MApp_ZUI_ACTagingmenu.c` or `MApp_ZUI_ACTkeypadfunctionosd.c`).
3. Overwrite its window procedure pointer with the custom Snake entry point.
4. When the user opens the dialog via the service menu, the TV routes remote-control key events (`KEY_UP`, `KEY_DOWN`, etc.) into Snake.
5. Snake uses `MDrv_GE_FillRect` to draw into `dcBuff` and flushes to the screen.

### 4.2 Engineering Reality (Why it cannot be attempted now)
1. **Boot Partition Signature:** Modifying `decompressed_main.bin` changes its compressed payload hash, causing the bootloader to reject the image or hang at startup.
2. **Watchdog Interlocking:** The main superloop (`MApp_ZUI_Main`) must continuously strobe the watchdog timer. If custom code stalls, the TV reboots in an endless loop.
3. **No Safety Net:** There is no known USB recovery key combination, no secondary boot ROM fallback, and no physical UART console to halt the bootloader if corrupted firmware is flashed.

### 4.3 Conclusion
The Snake game engine should remain on the host side. The next step toward physical execution must be **hardware-level verification (UART interface and board analysis)**, never unverified firmware modification.
