# CompressorController R1 — design verification

**Date:** 2026-11-12 · **Board:** CompressorController (Rev R1) · **Source:** `CompressorController.kicad_sch` / `.kicad_pcb`, `production/bom.csv`
**Sourcing data:** Konnect JLCPCB database refreshed this session (821,288 parts; previous cache was 6 days old, 819,228 parts).

> Scope: LCSC/JLC part validity + stock, HV-bus bulk capacitance, and a general schematic review.
> Not re-checked (per your request): hall sensors, motor-temp connector (J4), the existing DRC violations.

> **Update (same session, 16:35) — changes applied at your request**
> - **C37**: C5422 (1 µF 0805 **Y5V**) → **C28323** (1 µF 50 V **X7R**, Basic, 3.85 M stock).
> - **R97 / R103 / R104**: assigned **C2904210** (Milliohm HoJLR1206-1W-2mR-1 %, 1 W 2 mΩ 1206, 61 k stock).
> - **R69**: assigned **C5375488** (Milliohm HoYLR2512-3W-200mR-1 %, 200 mΩ 3 W 2512 — same series as the 20 mΩ R70, 35 k stock).
> - **Rated input power confirmed at 900 W** → revised HV-capacitance verdict in §2.6.
> - All other findings intentionally left for you to resolve.

---

## 0. Summary

| Area | Verdict |
|---|---|
| **Sourcing** | 82 LCSC codes originally, **all still valid** in the refreshed database. **Five were re-coded in this revision** (C37, R97/R103/R104, R69 — see update note); only **E1** (spark gap) remains without a code. One code (F3) is still a fuse *clip*, not the fuse. A handful are low stock, one critically (PFC inductor: **2 pcs**). |
| **HV capacitance** | 990 µF (3 × 330 µF/450 V) is **fine up to ≈1.8 kW**. Above that the limit is the capacitors' **100 Hz ripple-current rating**, not the capacitance value: at 2 kW you are at/over the bank rating, at 2.5 kW clearly over. Ripple voltage is not a problem (4 % at 2 kW). |
| **Other bugs** | 1 serious functional bug (isolated CAN port cannot work — a digital isolator is used as a CAN transceiver), 2 safety items (4–7 min bus discharge, USB-C on a mains-referenced ground), plus several margin/coordination issues. Details in §3. |

---

## 1. LCSC / JLC part verification

### 1.1 Method
- Regenerated the BOM from the schematic and cross-checked it against `production/bom.csv` and against the footprints actually present on the PCB. Reference sets match exactly: **263 fitted parts**, nothing on the board is missing from the BOM and nothing in the BOM is absent from the board.
- Every code was looked up in the refreshed JLCPCB SQLite database (part exists, manufacturer part, package, library type, stock, price).
- Package vs footprint was checked for the non-obvious parts (INA240 D-package pinout, 74LVC1G66 SOT-353 pinout, IPM DIP-24, TO-247, USB-C, 7.62 mm connectors, 5×20 mm fuse).

### 1.2 BOM gaps — parts with **no** LCSC/JLC code

| Ref | Value | Footprint | Impact |
|---|---|---|---|
| **R97, R103, R104** | 2 mΩ | R_1206 | ✅ **Resolved — C2904210** (HoJLR1206-1W-2mR-1 %, 1 W, 1 %, 61 k stock). These are the three IPM low-side current shunts and the *only* connection from NU/NV/NW to GND, so they were the critical gap. |
| **R69** | 0.2 Ω | R_2512 | ✅ **Resolved — C5375488** (HoYLR2512-3W-200mR-1 %, same series as R70). Fitted, it parallels the 20 mΩ PFC shunt: SOC trip 14.25 A → 15.67 A (~9 % more PFC headroom). |
| **E1** | Spark gap | sparkgap | No code. Presumably hand-fitted / mechanical; confirm that is intended. |

### 1.3 Wrong part behind a code

| Ref | Value in BOM | Code | What the code actually is |
|---|---|---|---|
| **F3** | 16 A | C41371865 | XF-103 **5×20 mm fuse clip/holder** (30 A, 500 V), not a fuse. The 16 A fuse itself has no BOM line. Either add the fuse part or make clear it is hand-inserted. |

### 1.4 Stock

Parts below 400 pcs (single-build quantity in brackets):

| Code | Stock | Qty | Part | Note |
|---|---|---|---|---|
| **C52766608** | **2** | 1 | XR106125T331MV1L2, 330 µH 11.3 A PFC inductor | **Show-stopper for production.** Only 2 pieces in the JLC database. Also the part that sets the PFC power ceiling (§2.5). |
| C5422 | 17 | 1 | CL21F105ZBFNNNE, 1 µF 0805 **Y5V** | Low stock *and* a poor choice: Y5V loses ~60–70 % of its capacitance at 12–15 V. It is only decoupling the relay coil, so it works, but use X5R/X7R. |
| **C15742** | 29 | 1 | STM32F405RGT6 | Fine for one board; no production headroom. |
| **C340576** | 29 | 1 | TDK CS11-E2GA222MYNSA, 2.2 nF X1/Y2 | Fine for one board. Note C40/C42/C43 use a *different* 2.2 nF X1/Y2 (C2919125, 12 k stock) for the same job — consolidate to one part. |
| C570974 | 160 | 1 | TAS10-15-NH 15 V/10 W PSU | OK for now. |
| C42401690 | 166 | 1 | BCA65S30D3 SiC boost diode | OK for now. |
| C47279087 | 253 | 1 | 1.5 µF 630 V film | OK. |
| C5121957 | 326 | 2 | DB2ERM-7.62-3P-GN | OK. |

Everything else is ≥ 500 pcs, most are ≥ 10 k. **No code in the BOM is obsolete or missing from the current JLCPCB database.**

Library split: **57 of the 82 codes are Extended** parts (JLC setup/feed fee each), 22 are **Basic**, 4 are **Preferred**. Worth consolidating a few: the 2.2 nF Y-caps (above), and 100 nF/1 k/10 k are already Basic.

### 1.5 Full list

| LCSC | Qty | Stock | Type | MFR part / value | Refs | Flag |
|---|---|---|---|---|---|---|
| C25804 | 20 | 43,766,123 | Basic | 0603WAF1002T5E / 10k | R11, R19, R20, R21, R22, R23, R24, R44, R45, R46, R47, R48, R49, R50, R56, R61, R65, R76, R82, R83 |  |
| C14663 | 34 | 37,616,260 | Basic | CC0603KRX7R9BB104 / 100nF | C1, C13, C14, C15, C16, C17, C19, C24, C25, C26, C29, C3, C30, C32, C33, C35, C36, C4, C5, C50, C53, C56, C6, C60, C63, C64, C7, C71, C74, C77, C79, C82, C83, C84 |  |
| C21190 | 10 | 26,048,858 | Basic | 0603WAF1001T5E / 1k | R100, R105, R2, R25, R3, R67, R72, R78, R80, R96 |  |
| C15849 | 1 | 12,189,355 | Basic | CL10A105KB8NNNC / 1uF | C31 |  |
| C8545 | 1 | 6,118,004 | Basic | 2N7002 / 2N7002 | Q1 |  |
| C2286 | 1 | 6,105,226 | Basic | KT-0603R / Red | D1 |  |
| C1588 | 13 | 6,026,838 | Basic | CL10B102KB8NNNC / 1nF | C23, C27, C45, C49, C59, C67, C68, C70, C89, C90, C91, C92, C93 |  |
| C23345 | 13 | 5,608,007 | Basic | 0603WAF220JT5E / 22 | R1, R13, R14, R15, R16, R17, R18, R26, R27, R28, R42, R43, R79 |  |
| C95872 | 2 | 5,275,911 | Basic | M7 / M7 | D7, D8 |  |
| C2128 | 1 | 4,397,047 | Basic | 1N4148WS / 1N4148WS | D5 |  |
| C19666 | 1 | 3,642,922 | Basic | CL10A475KO8NNNC / 4.7uF | C61 |  |
| C22962 | 5 | 2,569,560 | Basic | 0603WAF2200T5E / 220 | R106, R12, R41, R68, R81 |  |
| C17901 | 1 | 2,069,091 | Basic | 1206W4F1000T5E / 100 | R51 |  |
| C1589 | 6 | 1,817,896 | Extended | CL10B103KB8NNNC / 10nF | C52, C58, C94, C95, C96, C97 |  |
| C2907468 | 3 | 1,411,735 | Extended | FRC1206J2R0 TS / 2 | R101, R74, R98 |  |
| C28646290 | 2 | 1,123,236 | Preferred | DSK22 / DSK22 | D16, D21 |  |
| C17900 | 3 | 1,032,695 | Basic | 1206W4F1003T5E / 100k | R53, R54, R55 |  |
| C84267 | 4 | 1,022,066 | Extended | NCD0603G1 / Green | D10, D15, D2, D20 |  |
| C440198 | 7 | 917,763 | Basic | GRM21BR61H106KE43L / 10uF | C2, C34, C41, C46, C55, C65, C8 |  |
| C1644 | 2 | 772,009 | Basic | CL10C150JB8NNNC / 15pF | C11, C12 |  |
| C23164 | 1 | 760,294 | Basic | 0603WAF470KT5E / 4.7 | R10 |  |
| C61063 | 1 | 476,464 | Basic | XL1509-5.0E1 / XL1509 | U18 |  |
| C1002 | 1 | 414,870 | Basic | GZ1608D601TF / 600R@100MHz | FB2 |  |
| C50254 | 6 | 340,994 | Basic | CL31B225KBHNNNE / 2.2uF | C10, C18, C20, C21, C22, C9 |  |
| C22797 | 1 | 330,879 | Basic | 0603WAF1302T5E / 13k | R91 |  |
| C17928 | 3 | 203,079 | Basic | 1206W4F100KT5E / 1 | R102, R75, R99 |  |
| C454968 | 1 | 191,814 | Extended | BZX384-C12,115 / BZX384‐C12,115 | D6 |  |
| C22912 | 1 | 186,402 | Extended | 0603WAF2372T5E / 23.7k | R73 |  |
| C17954 | 12 | 186,109 | Extended | 1206W4F2003T5E / 200k | R29, R30, R31, R33, R34, R35, R37, R38, R39, R84, R85, R86 |  |
| C2682775 | 1 | 170,879 | Extended | X32258MOB4SI / 8M | Y1 |  |
| C44763 | 3 | 167,061 | Extended | US1J-E3/61T / US1J | D22, D23, D24 |  |
| C2927039 | 1 | 128,917 | Extended | USB-TYPE-C-019 / Connector, USB-TYPE-C-16P | J7 |  |
| C12744 | 4 | 121,593 | Extended | LBAT54HT1G / BAT54J | D11, D25, D26, D27 |  |
| C2894721 | 2 | 81,964 | Extended | SMMS0650-680M / 68uH 2A | L3, L4 |  |
| C5375467 | 1 | 74,157 | Extended | HoYLR2512-3W-20mR-1% / 0.02 | R70 |  |
| C9669 | 1 | 63,079 | Preferred | ADUM1201ARZ-RL7 / ADUM1201ARZ-RL7 | U9 |  |
| C88567 | 1 | 55,299 | Extended | UCC28180DR / UCC28180D | U15 |  |
| C1609 | 2 | 53,145 | Preferred | 0603B272K500NT / 2.7nF | C54, C98 |  |
| C395831 | 1 | 48,751 | Extended | DB2ERC-3.5-4P-GN / CAN | J1 |  |
| C2681226 | 1 | 38,299 | Extended | XL1509-3.3 / XL1509-3.3 | U19 |  |
| C2833485 | 1 | 34,761 | Extended | SMD0805-050-16V / 0.5A | F2 |  |
| C3340 | 7 | 33,050 | Extended | RVT1V221M0810 / 220uF | C78, C80, C81, C85, C86, C87, C88 |  |
| C97489 | 6 | 32,615 | Extended | 74LVC1G66GW,125 / 74LVC1G66 | U10, U11, U12, U13, U14, U17 |  |
| C1596 | 3 | 26,257 | Preferred | 0603B153K500NT / 15nF | C48, C57, C66 |  |
| C22911 | 1 | 17,996 | Extended | 0603WAF2152T5E / 21.5k | R71 |  |
| C2875699 | 2 | 15,743 | Extended | TJA1051TK/3/1J / TJA1051TK-3 | U2, U7 |  |
| C286231 | 1 | 15,494 | Extended | XSD683-022 / XSD683-022 | HS2 |  |
| C489081 | 2 | 14,809 | Extended | MPX684K31D4KN15800 / 0.68uF | C38, C44 |  |
| C2999478 | 4 | 13,303 | Extended | FRC1206F3403TS / 340k | R57, R58, R64, R90 |  |
| C49010117 | 4 | 13,083 | Extended | FRC1206F3323TS / 332k | R62, R63, R88, R89 |  |
| C2934560 | 1 | 12,910 | Extended | ESP32-C3-WROOM-02-N4 / ESP32-C3-WROOM-02 | U8 |  |
| C2919125 | 3 | 11,999 | Extended | DCF222M34Y5UQ6BL7A0 / 2.2nF | C40, C42, C43 |  |
| C52603 | 4 | 11,327 | Extended | 0805W8F3161T5E / 3.16k | R32, R36, R40, R87 |  |
| C1632 | 1 | 8,475 | Extended | 0603B821K500NT / 820pF | C76 |  |
| C376833 | 1 | 7,518 | Extended | TCC0603X7R394K500CT / 390nF | C62 |  |
| C872617 | 5 | 6,766 | Extended | RT1206FRE07221KL / 221k | R60, R92, R93, R94, R95 |  |
| C459527 | 1 | 4,347 | Extended | BAV16W-7-F / BAV16W | D4 |  |
| C22447862 | 1 | 4,256 | Extended | GBU1510 / GBU1510 | D9 |  |
| C116964 | 1 | 3,347 | Extended | G5LE-14 DC12 / G5LE-1 | K1 |  |
| C210689 | 1 | 3,184 | Extended | B72214S2271K101 / B72214S2271K101 | RV1 |  |
| C38409 | 1 | 3,015 | Extended | 1N5406RLG / 1N5406 | D12 |  |
| C27975268 | 3 | 2,935 | Extended | MMSD914 / MMSD914 | D13, D18, D19 |  |
| C2653784 | 1 | 2,896 | Extended | UCC27517ADBVR / UCC27517ADBV | U16 |  |
| C2924779 | 2 | 2,695 | Extended | PDMCAT221413-502MLB / PDMCAT221413-502MLB | FL1, FL2 |  |
| C2086273 | 1 | 2,351 | Extended | CRCW120621K0FKEA / 21k | R59 |  |
| C476130 | 1 | 1,839 | Extended | IKCM30F60GD / IKCM30F60GD | U6 |  |
| C221676 | 2 | 1,724 | Extended | KMR211NGLFS / KMR211NGLFS | SW1, SW2 |  |
| C41371865 | 1 | 956 | Extended | XF-103 / 16A | F3 |  |
| C4656 | 1 | 939 | Extended | 22*10*25 / 22*10*25 | HS1 |  |
| C7211174 | 3 | 901 | Extended | KM450V331SI230*30TA-1A3EL=4.0±0.5t / 330uF | C72, C73, C75 |  |
| C1346458 | 3 | 882 | Extended | INA240A1D / INA240A1D | U3, U4, U5 |  |
| C3796047 | 1 | 728 | Extended | B32653A6474J000 / CAP FILM 470nF ±5% 630V TH | C47 |  |
| C349084 | 1 | 546 | Extended | EWWR0010J10R0T9 / 10 | R52 |  |
| C537028 | 3 | 527 | Extended | IPL60R185C7 / IPL60R185C7 | Q3, Q4, Q5 |  |
| C5121957 | 1 | 326 | Extended | DB2ERM-7.62-3P-GN / 230VAC In | J3 | low stock |
| C5121957 | 1 | 326 | Extended | DB2ERM-7.62-3P-GN / Motor | J5 | low stock |
| C47279087 | 1 | 253 | Extended | JWMPP85-155K630VDCP20E9 / 1.5uF | C51 | low stock |
| C42401690 | 1 | 166 | Extended | BCA65S30D3 / BCA65S30D3 | D14 | low stock |
| C570974 | 1 | 160 | Extended | TAS10-15-NH / TAS10-15-NH | PS1 | low stock |
| C15742 | 1 | 29 | Extended | STM32F405RGT6 / STM32F405RGTx | U1 | **LOW STOCK** |
| C340576 | 1 | 29 | Extended | CS11-E2GA222MYNSA / 2.2nF | C39 | **LOW STOCK** |
| C5422 | 1 | 17 | Extended | CL21F105ZBFNNNE / 1uF | C37 | **LOW STOCK** |
| C52766608 | 1 | 2 | Extended | XR106125T331MV1L2 / 330uH | L2 | **LOW STOCK** |
| — | 1 | — | — | SparkGap | E1 | **NO CODE** |
| — | 3 | — | — | 2mR | R103, R104, R97 | **NO CODE** |
| — | 1 | — | — | 0.2 | R69 | **NO CODE** |

---

## 2. HV bus capacitance

### 2.1 Operating point

The PFC is a UCC28180 boost with a 1.004 MΩ / 13 kΩ feedback divider and the IC's 5.000 V reference:

**V_BUS = 5.000 × (1 + 1004 k/13 k) = 391.2 V** (matches TI's 1 M/13 k = 391 V example).

Bulk bank: **C72 + C73 + C75 = 3 × 330 µF / 450 V = 990 µF**, plus C47 470 nF/630 V film at the inverter.
Stored energy: ½CV² = **75.7 J**, charge 387 mC.

### 2.2 100 Hz ripple current — the actual limit

A PFC delivers pulsating power at 2× line frequency; the capacitor carries

  I_C(rms) = P / (√2 · V_BUS)      (P = inverter load)

The caps are rated at **120 Hz, 105 °C**. The Beryl KM datasheet's frequency coefficient for 315–450 V parts is 0.77 at 50 Hz and 1.00 at 120 Hz, so at 100 Hz use ≈0.95 of the 120 Hz rating. For 450 V/330 µF the datasheet lists 1.08 A (25×45), 1.39 A (30×45), 1.35 A (35×35); your part is the smaller **30×30** case, so budget **≈1.0–1.1 A per cap**, i.e. **≈3.0–3.3 A for the bank**.

| Load | I_C rms total | per cap | ΔV ripple (pp) | ripple % | 20 ms line-drop sag |
|---|---|---|---|---|---|
| 1.0 kW | 1.81 A | 0.60 A | 8.2 V | 2.1 % | 52 V |
| 1.5 kW | 2.71 A | 0.90 A | 12.3 V | 3.2 % | 78 V |
| **1.8 kW** | **3.25 A** | **1.08 A** | 14.8 V | 3.8 % | 93 V |
| **2.0 kW** | **3.62 A** | **1.21 A** | 16.4 V | 4.2 % | 103 V |
| 2.5 kW | 4.52 A | 1.51 A | 20.5 V | 5.3 % | 129 V |

**Verdict: the capacitance value is fine, the ripple current is not.** 990 µF is ample for ~1.5–1.8 kW (and the voltage ripple stays ≈3–4 %). At 2 kW the bank is at 100–120 % of its 100 Hz rating — the caps will run hot and the 2000 h/105 °C life will collapse (life halves per 5 °C). At 2.5 kW it is clearly over. Add a 4th 330 µF (→ 1320 µF, 4.3 A bank) or use a higher-ripple/larger-can part if you intend > 1.8 kW continuous.

Note the inverter's PWM ripple (several A at the switching frequency) also flows in this bank. It is less damaging per amp (the 10 kHz coefficient is ~1.4) but it eats the same thermal margin, so the 100 Hz number above is the optimistic case.

### 2.3 Voltage margin

- Nominal 391 V on a 450 V cap = **87 %** of rating; at 2 kW the ripple peak is **399 V** (89 %).
- UCC28180 OVP: 107 % = 419 V (VCOMP discharge), 109 % = **426 V** (gate off) = **95 % of the cap rating**.
- The IPM's *recommended* DC link maximum is **400 V** (absolute max 450 V, surge 500 V). The 391 V setpoint plus 4 % ripple already touches 399 V, i.e. you are operating at the module's recommended limit, and an OVP event takes it to 426 V.
- Recommendation: either drop the bus setpoint to ~375–380 V (change R91), or move to 500 V bulk caps, if you want real margin at high line / OVP.

### 2.4 Discharge / bleeder

The bleeder is R92/R94 + R93/R95: two strings of 221 k + 221 k, in parallel = **221 kΩ**. With 990 µF, τ = 219 s and the time to 60 V is **≈410 s (6.8 min)**; counting the feedback dividers (1.004 MΩ and 600 kΩ) it is still ≈4.3 min. See §3.2 — this is the worst issue on the HV side after the ripple current.

### 2.5 Other things that bound the power

- **PFC inductor C52766608**, 330 µH, rated **11.3 A**. Peak line current is √2·P/230: 11.07 A at 1.8 kW, **12.30 A at 2 kW**. So the inductor is at/over its rating from ~1.8 kW up — and its stock is 2 pcs.
- **PFC SOC (soft overcurrent)**, ISENSE −0.285 V across 20 mΩ (R70 only, because R69 has no code) = 14.25 A peak → **≈2.32 kW** at 230 V before the PFC starts folding back. With R69 fitted: 15.67 A → 2.55 kW. PCL (−0.4 V) is 20 A / 3.25 kW.
- So the practical continuous ceiling of this PFC is **≈1.8 kW**, set by the inductor and the cap bank — consistent with each other.

### 2.6 Revised verdict at the actual 900 W rating

900 W input (≈3.9 A RMS / 5.5 A peak at 230 V) changes the picture completely — the bank is roughly **twice** what 900 W needs:

| Quantity at 900 W | Value |
|---|---|
| 100 Hz capacitor current | **1.63 A total, 0.54 A per cap** (≈50 % of the ~1.0–1.1 A rating) |
| 100 Hz voltage ripple | **7.4 V pp (1.9 %)** |
| 20 ms line-drop sag | 47 V |
| Per-cap heating | ~25 % of rated ripple power → negligible, long life |

**Verdict: no capacitance problem at 900 W — comfortable margin on both capacitance and ripple current.** If anything you could drop to two 330 µF (660 µF → 11 V pp, 0.8 A/cap) and still be fine; the third cap buys holdup and cooler operation, which is a reasonable trade. No change recommended.

Also at 900 W: PFC inductor peak 5.5 A vs 11.3 A rating (2× margin), SOC limit 14.25 A ≈ 2.6× the operating current. Those findings cease to be limiting.

---

## 3. Other findings

| # | Severity | Finding | Evidence | Suggestion |
|---|---|---|---|---|
| 3.1 | **High (functional)** | **The isolated CAN port cannot work.** U9 is an **ADUM1201ARZ** — a dual-channel *digital* isolator — wired as if it were an isolated CAN transceiver: side 2 `VIA`/`VOB` (pins 7/6) are tied to the transceiver's `CANH`/`CANL`, side 1 `VOA`/`VIB` (pins 2/3) drive `ISO_CAN_H`/`ISO_CAN_L` on J1. Its I/Os are 3.3 V CMOS, not a differential bus; VOB will fight the TJA1051's driver and the far end sees single-ended 3.3 V levels, not CAN. J1's isolated side is also powered from the connector (`ISO_V+` = J1 pin 1), so the far end must supply 3.3 V. | `isolator.kicad_sch`, netlist U9 pins 1–4 / 6–7, ADUM1201 datasheet | Use a real isolated CAN transceiver (ADM3053, ISO1042, or a TJA1051 + isolated DC-DC). If the intent was only to isolate the *logic* side, U9 belongs between the MCU's TX/RX and the transceiver, not on CANH/CANL. |
| 3.2 | **High (safety)** | **HV bus discharge is far too slow.** Bleeders R92/R94 + R93/R95 are 221 kΩ each string (442 kΩ), two strings in parallel = **221 kΩ**. With 990 µF that is τ = 219 s; time to 60 V ≈ **410 s (6.8 min)**, or ≈4.3 min counting the feedback dividers. Stored energy 75.7 J. | PFC sheet, netlist R92–R95 | Add an active discharge (a small MOSFET/relay across a resistor, or a dedicated bleeder IC) or accept a warning label + lockout. A passive resistor that meets a 5 s rule would have to dissipate ~50 W, so passive is not an option at 990 µF. |
| 3.3 | **High (safety)** | **USB-C is on a mains-referenced ground.** Board GND is the PFC return (bridge negative), i.e. it sits at mains potential. J7's GND/shield, the ESP32 and the USB data lines are all on that same domain; only CAN has an isolator. Plugging a laptop into a live board puts mains on the laptop's USB ground. | netlist J7 / U8, GND net = U6.16 / C72.2 / bridge return | Power/program over USB only with mains disconnected (label + interlocks), or add USB isolation (ADuM3160/ADuM4160) or a non-isolated programming header. |
| 3.4 | Medium | **Hardware ITRIP is set at/above the module rating.** The INA240 outputs (gain 20 on 2 mΩ = 40 mV/A, 1.65 V offset) are diode-OR'd through D25–D27 and divided by R105/R106 (1 k/220) into the IPM's ITRIP pin. With the module's 470 mV ±70 mV threshold, the trip lands at **≈20.5 A (min) / 30.2 A (typ) / 39.9 A (max)** — the IPM is rated 30 A. So a hardware overcurrent only acts on hard faults, and its spread is ~2:1. | Phases sheet, R105/R106, IKCM30F60GD VIT,TH+ 400–540 mV | If you want real overload protection, re-scale the divider for ~15–20 A nominal (e.g. smaller R105 or larger R106), and/or rely on the MCU's ITRIP ADC reading (PB1) with a software limit. |
| 3.5 | Medium | **F3 is a fuse clip, not a fuse** (see §1.3). A 16 A fuse also does not protect the 10 A relay K1 in front of it — check coordination. | BOM F3 / C41371865 | Add the 16 A 5×20 mm fuse; consider 10 A or a 12 A fuse to protect the relay and the 15 A connectors. |
| 3.6 | Medium | **PFC inductor is at/over rating at ≥1.8 kW** (11.3 A vs 12.3 A peak at 2 kW) and only 2 pcs in stock. | C52766608 datasheet / DB | Verify Isat; for >1.8 kW pick a larger core or accept the SOC fold-back. |
| 3.7 | Low | **R69 has no LCSC code** while marked fitted — changes PFC current-sense gain by 9 % depending on whether JLC places it. | §1.2 | Assign a code or mark DNP. |
| 3.8 | Low | **C37 is 1 µF Y5V** on the relay-coil node; at 12–15 V it is effectively ~0.3–0.4 µF and drifts with temperature. Works (relay decoupling) but use X5R/X7R. | C5422 | Swap to a 1 µF X5R 25 V 0805. |
| 3.9 | Low | **Orphaned AC-sense / boost-follower block.** R57/R58/R59 + D6/C41/R60 (12 V clamp) and R62/R63/R64 + R65/C46/D11 go nowhere useful: Q2, R66 and R77 are DNP, and neither divider reaches the MCU. It is 6 resistors + 4 caps of dead copper (TP6 is a useful probe, though). | PFC sheet | Delete or repurpose; if you want AC-line sensing at the MCU, wire it to an ADC pin. |
| 3.10 | Low | **CAN termination is 110 Ω** (R12 220 Ω ∥ R41 220 Ω). For a 2-node bus the spec is 60 Ω; 110 Ω is a single-terminator value and will ring at higher bit rates. | can/express sheets | Fit 2 × 120 Ω only if the bus is properly terminated at both ends; otherwise leave one 120 Ω. |
| 3.11 | Low | **No HV-present indicator.** There is no LED on the bus; with a 4–7 min discharge that matters for service. | — | Add an HV LED (or drive the red LED from the bus divider). |
| 3.12 | Doc | README still says *"HV bus ~325 V DC"* and *"IKCM10H60GAXKMA1, 10 A"* — the board is a 391 V bus with an **IKCM30F60GD (30 A)**. The block diagram also calls the isolator "gate-signal and fault isolation", which is not what it does. | README.md | Update before publishing. |

### Things I checked that are **OK** (so you don't have to re-check them)

- INA240 **D-package pinout is correct** (1 = IN−, 3 = REF2, 7 = REF1, 8 = IN+; pin 4 NC tied to GND is allowed). REF1 = GND, REF2 = 3V3 gives the intended 1.65 V mid-scale offset.
- 74LVC1G66 SOT-353 pinout is correct for the symbol used (1/2 = switch, 3 = GND, 4 = E, 5 = VCC); the filter-select trick (shorting the 1 k series resistor) is sound.
- IPM logic inputs: V_IH 2.1 V min, so 3.3 V through the 22 Ω/3.3 k divider (internal 5 k ∥ external 10 k) still gives ≈3.27 V — fine.
- Inrush: R52 10 Ω/10 W across the relay K1, with the relay coil fed from the downstream +15 V rail — the sequence (charge through R52 → PSU boots → MCU closes K1) works.
- The Y-caps are genuine safety parts: C340576 (TDK CS11, X1/Y2) and C2919125 (SHM DCF, X1/Y2, CQC/UL/VDE) — fine for line-to-earth.
- PFC ISENSE 220 Ω + 2.7 nF matches TI's "220 Ω inrush-limiting resistor" recommendation; the light filter is intentional (average-current loop does the rest).
- PFC gate network (2 Ω → 1 Ω with anti-parallel MMSD914, 15 V driver, 3 × IPL60R185C7) is correct.
- Bootstrap: 2.2 µF + 100 nF per phase plus external US1J bootstrap diodes — fine.
- Bulk-cap voltage/capacitance values, film cap C47 630 V on a 391 V bus, X2 caps 310 VAC on 230 V — all correctly rated (the ripple margin is the separate issue in §2.2).
- ERC: the 43 errors are benign (unused MCU/ESP32 pins, no PWR_FLAG on the power symbols, the DNP Q2 open-collector/VSENSE pin-type clash). No connectivity errors beyond the intended unconnected pins.

---

## 4. Suggested order of work

1. ~~**R97/R103/R104** — assign a 2 mΩ shunt code~~ ✅ done (C2904210).
2. **U9** — replace with a proper isolated CAN transceiver (or rework J1's function).
3. **Bleeder** — add active discharge; add an HV LED.
4. **USB** — isolation or a hard "mains off" interlock/documentation.
5. **F3** — add the actual 16 A fuse part; reconsider fuse/relay coordination.
6. ~~**Cap bank** — decide the continuous power target~~ ✅ 900 W confirmed → no change needed (§2.6).
7. **ITRIP** — re-scale to ~15–20 A trip, or implement the software limit.
8. **PFC inductor** — verify Isat and secure stock before ordering.

> Note: `production/bom.csv` and the position files were generated before these edits — regenerate them before ordering.

---

*Generated from the schematic, PCB and the refreshed JLCPCB database. Netlist extracted with `kicad-cli` 10.0.6; calculations in this report are reproducible from the component values listed.*
