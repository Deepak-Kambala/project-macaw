# Milestone 6: Remote-Control Input Pipeline Investigation

**Project:** Project Macaw (Samsung UA23H4003ARLXL / MStar Macaw12 / Aeon R2)  
**Subject:** Reverse engineering the execution path from physical IR reception to ZUI UI event handling  
**Date:** November 2026  

---

## 1. Executive Summary

Milestone 4 and 5 proposed a hypothetical execution pipeline connecting physical remote-control button presses to the MStar Zero UI (ZUI) framework:
$$\text{IR Hardware} \longrightarrow \text{drvIR Driver} \longrightarrow \text{Key Translation} \longrightarrow \text{ZUI Message Queue} \longrightarrow \text{MApp\_ZUI\_Main} \longrightarrow \text{u8WinProcID Dispatch}$$

Milestone 6 re-evaluates each stage of this proposed pipeline against binary evidence in `decompressed_main.bin`.

### Key Conclusions:
1. **ZUI Window Dispatch Architecture:** Confirmed by multiple format strings (`u8WinProcID= %d \n`, `_eActiveOSD=%d\n`) and source filenames (`tv-ap/dvb/ui2_M10/MApp_ZUI_ACT*.c`).
2. **Aging Menu Hooking Risk:** While `MApp_ZUI_ACTagingmenu.c` is present in the binary, its function entry addresses, dispatch table offsets, and exact callback signatures remain **unrecovered from `.text`**.
3. **Safety Directive:** Hooking or replacing this callback in firmware is strictly prohibited until the binary ABI, stack frame, and register constraints are extracted through disassembly.

---

## 2. Stage-by-Stage Evidence Classification

| Pipeline Stage | Technical Description | Evidence in Binary | Classification |
| :--- | :--- | :--- | :--- |
| **1. IR Physical Receiver** | Infrared photodiode detects 38 kHz modulated Samsung NEC-format pulses | Hardware physical front panel, schematic references | **VERIFIED** |
| **2. MStar IR Driver (drvIR)** | Hardware timer capture registers decode customer/key scan codes | `IR_RATE` string in `.rodata`, RIU register accesses at `0xA0200400` | **PARTIALLY VERIFIED** |
| **3. Scan-Code Translation** | Maps raw NEC code to logical TV key enums | Discrete key constants (`EN_EXE_CAPUTURE_AUDIO_THUMBNAIL_ENTER_KEY`, etc.) | **PARTIALLY VERIFIED** |
| **4. Inter-Thread Messaging** | Enqueues key event into OS message queue | Mailbox driver APIs (`MDrv_MBX_SendMsg`, `MDrv_MBX_GetMsgQueueStatus`) | **PARTIALLY VERIFIED** |
| **5. ZUI Event Loop** | `MApp_ZUI_Main` pumps messages and resolves active window | Source string `tv-ap/dvb/ui2_M10/MApp_ZUI_Main.c` at `0x16ce5c` | **STRONGLY SUPPORTED** |
| **6. Window Procedure Dispatch** | Active window procedure resolved via `u8WinProcID` and `_eActiveOSD` | Format strings `u8WinProcID= %d \n`, `_eActiveOSD=%d\n` at `0x16ca03` | **VERIFIED** |
| **7. Aging Menu Action Handler** | `MApp_ZUI_ACTagingmenu` processes D-pad navigation events | Source string `tv-ap/dvb/ui2_M10/MApp_ZUI_ACTagingmenu.c` at `0x16c870` | **HYPOTHESIS** |
| **8. Executable Hook Insertion** | Redirecting window procedure table entry to custom game loop | Function pointer table not located; callback ABI unverified | **UNVERIFIED** |

---

## 3. Detailed Technical Analysis

### 3.1 IR Driver and Hardware Demodulation
- The MStar Macaw12 SoC contains a dedicated hardware IR decoder connected to the physical front panel sensor.
- When an IR packet is received, the hardware decoder verifies the 16-bit Samsung custom code (`0x0707`) and generates an interrupt.
- In `decompressed_main.bin`, `IR_RATE` and hardware register access patterns show that timing registers are mapped in KSEG1 uncached MMIO space (`0xBF000000` / `0xA0200000`).

### 3.2 ZUI Window Procedure Dispatch (`u8WinProcID`)
At file offset `0x16ca03` in `decompressed_main.bin`:
```text
tv-ap/dvb/ui2_M10/MApp_ZUI_ACTglobal.c\x00u8WinProcID= %d \n\x00_eActiveOSD=%d\n\x00
```
This diagnostic printout confirms that MStar's ZUI framework uses an integer identifier (`u8WinProcID`) to index into a window procedure table (`pWinProcTable`), while `_eActiveOSD` tracks the currently focused fullscreen UI layer.

### 3.3 The "Aging Menu" Hijacking Proposal: Critical Reassessment
Milestone 4 and 5 proposed using the Aging Menu (`ACTagingmenu`) as the injection surface for the custom Snake game.
- **Why it was considered:** Aging mode is an engineering burn-in screen that displays full-screen color patterns without locking the RF tuner, HDMI stream, or audio decoders.
- **Why it cannot be hooked yet:**
  1. The string `MApp_ZUI_ACTagingmenu.c` is located in `.rodata` at `0x16c870`.
  2. The function pointer table that associates `u8WinProcID` with executable function pointers in `.text` has not been reconstructed.
  3. The exact calling convention (parameters passed in `r3`, `r4`, `r5`, stack cleanup, return codes) has not been verified for ZUI window procedures.

---

## 4. Safety Directive

**Under no circumstances should binary patching or callback redirection be attempted on the television firmware based solely on string-table analysis.**

Hooking a window procedure without verified function pointers and ABI definitions will cause:
1. Stack frame corruption and register clobbering.
2. Unhandled exception traps (`EPCR0` vector jump to `0x020280`).
3. Hardware watchdog reset loops.
4. Permanent device bricking in the absence of verified in-circuit recovery hardware.
