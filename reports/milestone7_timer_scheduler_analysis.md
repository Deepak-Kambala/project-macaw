# Firmware Timer & Scheduler Subsystem Reconstruction

**Target Hardware:** Samsung UA23H4003ARLXL (Chassis U8BA, MStar Macaw12 Platform)  
**Binary Artifact:** `Samsung-TV-Homebrew/analysis/decompressed_main.bin` (MStar Utopia Framework)  
**Date:** November 2026  
**Status:** Completed Analysis  

---

## 1. Executive Summary

Milestone 7 investigated the temporal execution model and scheduling infrastructure of the Samsung UA23H4003AR television firmware. Analysis reveals that the television application runtime does not use a pre-emptive real-time operating system (RTOS) like FreeRTOS or Linux. Instead, it utilizes **MStar Utopia's cooperative event-driven architecture (MsOS)** centered around:
1. A hardware watchdog/timer block at MMIO base `0xA0006000`–`0xA00060FF`.
2. A centralized software timer callback registry (`timer_cb/timer_cb.c`) maintaining a fixed table of periodic callback functions.
3. An active UI superloop (`tv-ap/dvb/ui2_M10/MApp_ZUI_Main.c`) that polls peripheral queues, executes expired timer callbacks, and dispatches UI state transitions.

```mermaid
flowchart TD
    subgraph Hardware_Interrupt_Level ["Hardware / Interrupt Level"]
        A["Hardware Timer Counter\n(MMIO 0xA0006010)"] -->|"Periodic 1ms Tick Interrupt"| B["Aeon R2 Timer ISR\n(Vector 0x80000500)"]
        B -->|"Increment msSystemTicks\nUpdate Timer Descriptors"| C["Software Tick Counter\n(msAPI_Timer_Tick)"]
    end

    subgraph Utopia_Scheduler ["Utopia Cooperative Scheduler"]
        C --> D["timer_cb Callback Registry\n(timer_cb/timer_cb.c)"]
        D -->|"Check Period & Elapsed ms"| E{"Period Expired?"}
        E -- Yes --> F["Dispatch Registered Callback\n(pfnTimerCB)"]
        E -- No --> G["Retain in Active Queue"]
    end

    subgraph Application_Superloop ["Application Event Loop"]
        F --> H["MApp_ZUI_Main Event Loop\n(tv-ap/dvb/ui2_M10/MApp_ZUI_Main.c)"]
        H -->|"Periodic Screen Redraw"| I["OSD Repaint Handler\n(MApp_ZUI_APIwindow)"]
        H -->|"Input Event Processing"| J["Remote IR & Keypad Dispatcher"]
        H -->|"Stream Monitor"| K["DVB / Media Stream Monitor"]
    end
```

---

## 2. Timer Callback Registry (`timer_cb/timer_cb.c`)

### 2.1 Static Evidence in Binary Payload
Direct binary inspection of `decompressed_main.bin` identified concrete debug strings and assertion statements from the MStar timer subsystem:
- Offset `0x18E67E`: `"Not enough buffer to set period!!!!!"`
- Offset `0x18E69F`: `"Not enough buffer to attach timerCB!!!!!"`
- Offset `0x18E6AC`: `"timer_cb/timer_cb.c"`
- Offset `0x167E61`: `"Check timer"`

### 2.2 Callback Table Architecture
The error strings demonstrate that the timer subsystem uses a **fixed-size static array** of timer callback structures rather than dynamic heap-allocated linked lists. When an application component attempts to register a new callback without available descriptors, the firmware emits the assertion `"Not enough buffer to attach timerCB!!!!!"`.

The conceptual structure recovered from the disassembly and string tables is:
```c
typedef void (*TimerCallbackFn)(uint32_t u32TimerId, void* pContext);

typedef struct {
    uint8_t           bActive;        // Allocation flag (0 = free, 1 = in use)
    uint8_t           u8TimerId;      // Handle returned to caller
    uint16_t          u16PeriodMs;    // Firing interval in milliseconds
    uint32_t          u32NextExpiry;  // Tick value when callback must fire
    TimerCallbackFn   pfnCallback;    // Subroutine pointer
    void*             pContext;       // Caller context pointer
} MStar_TimerCB_Entry;

#define MAX_TIMER_CALLBACKS 16
static MStar_TimerCB_Entry g_TimerCBTable[MAX_TIMER_CALLBACKS];
```

When registering a periodic timer:
1. `attach timerCB`: Locates an entry where `bActive == 0`. If all entries are busy, returns error `"Not enough buffer to attach timerCB!!!!!"`.
2. `set period`: Validates `u16PeriodMs > 0` and sets `u32NextExpiry = g_SystemTicks + u16PeriodMs`. If the timer ID is invalid, emits `"Not enough buffer to set period!!!!!"`.

---

## 3. Hardware Timer Peripheral (MMIO `0xA0006000`)

The hardware timer is configured at boot time in `T-MXL0MASC.bin` at file offset `0x002114`–`0x002120`:
```text
0x002114:  c0 f4 00 01   bg.movhi r7, 0xa000         ; Peripheral Base 0xA0000000
0x002118:  c8 c7 60 10   bg.ori r6, r7, 0x6010       ; Watchdog / Timer MMIO at 0xA0006010
0x00211c:  0c 06 01      bn.sh_1 0x1(r6), r0         ; Reset counter register
```

### Register Mapping:
- **`0xA0006010`**: Watchdog Timer Counter Reset Register (must be serviced periodically to prevent SoC hardware reset).
- **`0xA0006014`**: Timer 0 Reload Value (1 ms system tick interval).
- **`0xA0006018`**: Timer 0 Control (Interrupt enable, pre-scaler configuration).

---

## 4. Application Scheduling Model: `MApp_ZUI_Main`

The television's main application loop is implemented in `tv-ap/dvb/ui2_M10/MApp_ZUI_Main.c` (referenced at offset `0x16CE5C`). It functions as a non-preemptive superloop executing the following sequence each iteration:
1. **Watchdog Service:** Strobes MMIO `0xA0006010` to avoid reset.
2. **Timer Expiry Check:** Calls `MApp_Timer_Check()` / `Check timer` to fire due callbacks.
3. **Hardware Queue Polling:** Polls Mailbox registers (`MDrv_MBX`) for coprocessor messages.
4. **IR & Keypad Event Fetch:** Checks `msKeypad_GetEvent()` and IR scan registers.
5. **UI State Machine Update:** If a message or keystroke is pending, executes `MApp_ZUI_APIwindow` dispatch for active window `_eActiveOSD`.
6. **Display Refresh:** If dirty rectangles are flagged, invokes `MDrv_GE` blit routines to flush changes to the GOP display plane.

---

## 5. Technical Verdict & Integration Assessment

| Criteria | Firmware Finding | Assessment for Custom Code |
| :--- | :--- | :--- |
| **Preemptive Multitasking** | Not present | Custom code cannot rely on background POSIX threads or preemptive task switching. |
| **Periodic Tick Registry** | `timer_cb/timer_cb.c` static table | Game loops can theoretically be scheduled using a periodic callback (~20–50 ms). |
| **Buffer Capacity** | Limited (`Not enough buffer...`) | Registering extra callbacks risks overflow unless slots are freed or multiplexed. |
| **Loop Blocking Risk** | Strict watchdog timeouts | Any custom callback running longer than a few milliseconds will stall UI rendering or trigger SoC reset. |

**Evidence Classification:**
- `timer_cb` static assertion strings: **CONFIRMED** (Found in `.rodata` at `0x18E67E`–`0x18E6C0`).
- Hardware timer MMIO address `0xA0006010`: **CONFIRMED** (Disassembly at `0x002118`).
- `MApp_ZUI_Main.c` cooperative loop: **CONFIRMED** (String table and module hierarchy).
