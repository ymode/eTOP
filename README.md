# eTOP

A system monitor for the [Pimoroni Explorer](https://shop.pimoroni.com/products/explorer) board — htop for your RP2350.

```
┌──────────────────────────────┐
│  eTOP  System Monitor        │
├──────────────────────────────┤
│  CPU     150 MHz             │
│  ████████████████░░░░  100%  │
├──────────────────────────────┤
│  MEM     148K / 264K         │
│  ████████████░░░░░░░░   56%  │
├──────────────────────────────┤
│  DISK    1.2M / 2.0M         │
│  ██████░░░░░░░░░░░░░░   30%  │
├──────────────────────────────┤
│  TEMP    28.3 C              │
│  ██████████░░░░░░░░░░   47%  │
├──────────────────────────────┤
│  VSYS    5.02V               │
│  UP      01h 23m 45s         │
├──────────────────────────────┤
│  A:Info B:GC C:ADC  X/Y:Brt  │
└──────────────────────────────┘
```

## What it shows

- **CPU** frequency
- **Memory** usage (allocated vs total)
- **Disk** usage (filesystem)
- **Temperature** from the RP2350 internal sensor
- **VSYS** supply voltage
- **Uptime** since boot

Progress bars change color from green to yellow to red as usage increases.

## Buttons

| Button | Action |
|--------|--------|
| A | Toggle detailed system info view |
| B | Force garbage collection |
| C | Toggle ADC channel monitor (all 6 channels) |
| X | Brightness up |
| Y | Brightness down |
| Z | Exit (blank screen) |

## Install

Copy `main.py` to your Explorer board:

```bash
mpremote cp main.py :main.py
```

Or open it in [Thonny](https://thonny.org) and save to the device. It runs automatically on boot.

## Requirements

- [Pimoroni Explorer](https://shop.pimoroni.com/products/explorer) (RP2350, 240x240 LCD)
- Pimoroni MicroPython firmware with the `explorer` module

## License

Public domain — see [LICENSE](LICENSE).
