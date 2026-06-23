# Mains Powered VESC Motor Driver

> **HVAC VESC** — A mains-powered, VESC-compatible three-phase motor driver with active Power Factor Correction, built for compressor and HVAC applications.

[![License: CERN-OHL](https://img.shields.io/badge/Hardware%20License-CERN%20OHL-orange)](https://ohwr.org/cern_ohl_s_v2.txt)
[![VESC Compatible](https://img.shields.io/badge/Firmware-VESC%20Compatible-blue)](https://vesc-project.com/)
[![KiCad](https://img.shields.io/badge/EDA-KiCad%2010-brightgreen)](https://www.kicad.org/)
[![Revision](https://img.shields.io/badge/Rev-R1-lightgrey)]()

---

## Overview

This project is an open-hardware, mains-powered (230 V AC) three-phase motor driver that is fully compatible with the [VESC firmware](https://vesc-project.com/) ecosystem. It targets compressor and HVAC drive applications and is designed with grid compliance in mind, featuring active Power Factor Correction (PFC) to meet IEC 61000-3-2 harmonic emission limits.

The board takes 230 V AC directly from the mains, rectifies it to a high-voltage DC bus, and drives a three-phase motor through an Infineon IKCM10H60 Intelligent Power Module. A VESC Express (ESP32) module provides wireless connectivity and acts as the CAN/Wi-Fi/BT bridge, while an STM32F405 runs the VESC motor-control firmware.

---

## Key Features

| Feature | Details |
|---|---|
| **Input** | 230 V AC single-phase mains |
| **HV Bus** | Rectified DC bus (~325 V DC nominal) |
| **Power Bridge** | Infineon `IKCM10H60GAXKMA1` IPM — 10 A / 600 V, integrated gate drivers & bootstrap |
| **Active PFC** | Texas Instruments `UCC28180D` — CCM PFC controller |
| **MCU** | STMicroelectronics `STM32F405RGTx` running VESC firmware |
| **Connectivity** | VESC Express (ESP32) — Wi-Fi, Bluetooth & CAN bridge |
| **USB** | USB Type-C (programming / configuration) |
| **CAN Bus** | Dual isolated CAN interfaces |
| **Debug** | Tag-Connect SWD header |
| **Status LEDs** | Red & Green indicators |
| **License** | CERN Open Hardware Licence v2 |

---

## Block Diagram

```
         230 V AC
             │
     ┌───────▼────────┐
     │   Power in     │  EMI filter, inrush, rectifier
     │  (powerin.sch) │
     └───────┬────────┘
             │ HV DC Bus (~325 V)
     ┌───────▼────────┐
     │   Active PFC   │  UCC28180D — CCM boost PFC
     │   (pfc.sch)    │  IEC 61000-3-2 compliant
     └───────┬────────┘
             │ Regulated HV Bus
     ┌───────▼────────┐
     │  3-Phase IPM   │  IKCM10H60GAXKMA1
     │  (phases.sch)  │  10 A / 600 V, 3-phase bridge
     └───────┬────────┘
             │ U / V / W
          Motor / Compressor

     ┌──────────────────────────────────────────┐
     │              Control Domain              │
     │                                          │
     │  STM32F405  ◄──►  Isolator  ◄──►  IPM   │
     │  (VESC FW)        (iso.sch)    gate sigs │
     │      │                                   │
     │  Filters ── Current U/V/W sensing        │
     │  (filters)  Bus voltage / Phase voltages │
     │      │                                   │
     │  VESC Express (ESP32) ── CAN / BT / WiFi │
     │  LV Power ── 3.3 V / 5 V rails          │
     └──────────────────────────────────────────┘
```

---

## Schematic Hierarchy

The design is split into focused sub-sheets for clarity and reuse:

| Sheet | File | Description |
|---|---|---|
| Top-level | `CompressorController.kicad_sch` | Connectors, indicators, sheet assembly |
| MCU | `MCU.kicad_sch` | STM32F405RGTx, crystal, decoupling, SWD |
| PFC | `pfc.kicad_sch` | UCC28180D active PFC stage |
| Power in | `powerin.kicad_sch` | Mains input, EMI filter, bridge rectifier |
| Phases | `phases.kicad_sch` | IKCM10H60 IPM, current sensing |
| Filters | `filters.kicad_sch` | ADC anti-aliasing for current & voltage signals |
| Isolator | `isolator.kicad_sch` | Gate-signal and fault isolation barrier |
| LV Power | `lvpower.kicad_sch` | 3.3 V / 5 V low-voltage power supply |
| WiFi & BT | `express.kicad_sch` | VESC Express (ESP32) module |
| CAN | `can.kicad_sch` | Isolated CAN transceivers |

---

## Firmware

This board is designed to run the open-source **VESC firmware** and is configurable via **VESC Tool**.

- [VESC Firmware](https://github.com/vedderb/bldc)
- [VESC Tool](https://vesc-project.com/vesc_tool)

Motor parameters, PID gains, current limits, and field-weakening are all configured through VESC Tool over USB-C or wirelessly via the onboard VESC Express (Wi-Fi / BLE).

---

## Regulatory Compliance Targets

This design is being developed with the following standards in scope:

| Standard | Scope |
|---|---|
| **IEC 61000-3-2** | Harmonic current emission limits *(primary — addressed by active PFC)* |
| **IEC 60335-2-34** | Particular requirements for motor-compressors |
| **EN IEC 63000** | RoHS technical documentation |

> ⚠️ **Note:** This is an open hardware design. Regulatory certification (CE marking) must be obtained by the integrating party before placing the product on the EU market. The presence of PFC significantly aids IEC 61000-3-2 Class A/D compliance but does not guarantee it without verified measurement.

---

## Safety Warnings

> **⚡ HIGH VOLTAGE — MAINS POWERED**
>
> This board operates at lethal voltages. The HV DC bus reaches approximately **325–400 V DC** from rectified mains. Do **not** touch the board while powered. Ensure adequate enclosure, creepage/clearance distances, and fusing when integrating into a product. Only qualified persons should work on mains-connected equipment.

---

## License

This project is released under the **CERN Open Hardware Licence Version 2 – Strongly Reciprocal (CERN-OHL-S v2)**.

You may study, modify, and distribute this design, provided that any derivative works are released under the same licence and that attribution to the original authors is maintained.

© Picobello B.V. — see [`LICENSE`](LICENSE) for full terms.

---

## Contributing

Issues, improvements, and pull requests are welcome. Please open an issue before submitting large changes so the direction can be aligned first.

When contributing hardware changes, include updated schematics (KiCad 10 `.kicad_sch` format) and a description of what was changed and why.
