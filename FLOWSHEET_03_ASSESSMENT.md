# Flowsheet 03 assessment — next-milestone audit

Audit date: 2026-09-27. Scope: read-only assessment; no migration or implementation.

Legacy root (`L`): `/Users/giovaninunes/Folders/FieldDesignCode/Simulation Repository/Learning Flash/Flowsheet 03`.

Current root (`R`): `/Users/giovaninunes/Folders/RioGineer/riogineer-website`.

Paths prefixed `L/` and `R/` below resolve against those roots. Function/class names are source locators. JSON equipment IDs and keys are exact locators within `L/flowsheet_03.json`. The audit read `R/AGENTS.md`, `R/docs/RIOGINEER_MASTER_CONTEXT.md`, `R/MILESTONE_3.md` and `R/MILESTONE_3_1.md` first. Source code and configuration, rather than diagram appearance or README claims alone, determine the conclusions.

## 1. Executive summary

Flowsheet 03 was successfully accessed and recursively inventoried. There are **23 relevant files**: **18 Python, 2 JSON, 1 Markdown, 1 draw.io XML and 1 SVG XML**. One `.DS_Store` is irrelevant metadata. There are no HTML files, standalone `.xml` files, dependency manifests, separate equipment XML libraries, additional case inputs or original reference images in this directory.

The configured process has **31 active equipment objects**, **44 named material streams**, **one external feed**, **eight external products**, and **multiple coupled recycles with five manually selected tear streams**. Nine equipment types are used; the dispatcher implements eleven, also including pump and two-sided heat exchanger. Source/sink boundaries are configuration/drawing entities, not executable equipment classes. A standby flare knockout and relief lines are annotations, not active equipment or a calculated relief system. No hydrocyclone, flotation or TEG model exists here. Evidence: `L/flowsheet_03.json`; `L/engine/models.py::EQUIPMENT_MODELS`; `L/engine/flowsheet.py::PORTS`; `L/engine/flowsheet_drawio.py::scene`.

The highest-value reuse is the **component-rate conservation pattern, explicit port validation, dependency scheduling and separation of tear guesses from produced stream states**. These are useful algorithms, not an invitation to copy the legacy stream representation or combined configuration/result architecture.

The recycle algorithm is **generic across the supported port-based equipment graph**, but only partly complete as a reusable solver subsystem: tears are selected manually, scheduling ties depend on input array order, and robust multi-case qualification, automatic cycle analysis, persistent failure diagnostics and thermodynamic-state convergence are absent. The supplied example reproduces exactly in memory: 40 iterations, maximum external component residual `8.96818619366968e-9 kmol/h`. This demonstrates numerical bookkeeping under the demo assumptions, not physical validation.

Energy calculations exist locally: constant-Cp mixing/heating/cooling, ideal-gas compression, unused incompressible pumping and unused two-sided sensible heat exchange. **A complete plant energy balance is explicitly not calculated.** The separation calculation is a specified-K Rachford–Rice split of nonwater components with nonvolatile, immiscible water; it is not EOS-based equilibrium or rigorous VLLE. Do not import it as the next thermodynamic model.

Recommend **Milestone 4: an acyclic separator → splitter → mixer demonstration**, retaining the current prescribed-recovery separator and constant-Cp development basis. This proves multiple internal numbered streams, branching/rejoining, port connectivity and deterministic execution with minimal new physics. No recycle or compressor is needed for its first acceptance gate. The alternative separator/heater/second-separator/compressor chain adds qualification work without being necessary to prove topology. Details and acceptance gates are in sections 18–20.

## 2. Complete relevant file inventory and audit method

Every relevant file was read as text, parsed as JSON/XML, or inspected through its source and data structure. Generated outputs were retained as audit evidence, not dismissed as caches. No legacy runner was invoked because it writes/replaces outputs. No files were copied between repositories. Python imports used `-B`; calculations and drawing exports used memory only.

| Legacy-relative file                | Type / role                                                                   | Principal source locators                                                                                                     |
| ----------------------------------- | ----------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `README.md`                         | Documentation, commands, assumptions, reported test/demo results              | Specified conditions; Connections; Demonstration inputs; Verification                                                         |
| `flowsheet_03.json`                 | Sole input case; graph, specifications, tears, presentation and provenance    | `feeds`, `equipment`, `products`, `solver`, `drawing`, `safety_circuit`, `control_signals`                                    |
| `Run_Flowsheet.py`                  | CLI orchestrator and output writer                                            | `main`                                                                                                                        |
| `engine/material_balance.py`        | Mutable material stream and specified-K split                                 | `Stream`, unused `diagram`, `flash`                                                                                           |
| `engine/equipment_common.py`        | Shared guards, rate construction and balance checks                           | `finite`, `fraction`, `amounts`, `make_stream`, `mixture_cp`, `check_balance`                                                 |
| `engine/flowsheet.py`               | Topology validation, scheduling and recycle solver                            | `PORTS`, `inlets`, `validate_topology`, `read_stream`, `simulate`                                                             |
| `engine/models.py`                  | Eleven-model callable registry and balance wrapper                            | `EQUIPMENT_MODELS`, `execute`                                                                                                 |
| `engine/mixer.py`                   | Component-rate and sensible-temperature mixer                                 | `execute`                                                                                                                     |
| `engine/splitter.py`                | Proportional splitter                                                         | `execute`                                                                                                                     |
| `engine/valve.py`                   | Prescribed pressure, unchanged temperature                                    | `execute`                                                                                                                     |
| `engine/heater.py`                  | Specified-T sensible heater                                                   | `execute`                                                                                                                     |
| `engine/cooler.py`                  | Specified-T sensible cooler                                                   | `execute`                                                                                                                     |
| `engine/three_phase_separator.py`   | Nonwater flash / water split, separate low-level energy modes                 | `ThreePhaseSeparatorSpec`, `ThreePhaseSeparatorResult`, `calculate_three_phase_separator`, `three_phase_separator`, `execute` |
| `engine/two_phase_separator.py`     | Gas/liquid adapter retaining all water in liquid                              | `execute`                                                                                                                     |
| `engine/electrostatic_treater.py`   | Prescribed water removal                                                      | `execute`                                                                                                                     |
| `engine/compressor.py`              | Ideal-gas constant-Cp compressor and zero-flow adapter                        | `CompressorSpec`, `CompressorResult`, `calculate_compressor`, `compressor`, `execute`                                         |
| `engine/pump.py`                    | Constant-density liquid pump; registered, unused in case                      | `PumpSpec`, `PumpResult`, `calculate_pump`, `pump`, `execute`                                                                 |
| `engine/heat_exchanger.py`          | Two-sided constant-Cp exchanger; registered, unused in case                   | `HeatExchangerSpec`, `HeatExchangerResult`, `effectiveness`, `calculate_heat_exchanger`, `heat_exchanger`, `execute`          |
| `engine/flowsheet_drawio.py`        | Native XML and SVG generators                                                 | `scene`, `title`, `export_flowsheet`, `export_svg`                                                                            |
| `engine/test_flowsheet.py`          | Sole automated test file, 13 methods                                          | `Flowsheet03Tests`                                                                                                            |
| `outputs/flowsheet_03_results.json` | Saved demo calculation; 44 streams, 31 equipment results, convergence history | `streams`, `equipment`, `solver`, `products`, `provenance`                                                                    |
| `outputs/flowsheet_03.drawio`       | Saved editable XML drawing with embedded engineering metadata                 | `object`, `stream_name`, `stream_json`, `configuration_json`, `calculation_results_json`                                      |
| `outputs/flowsheet_03.svg`          | Saved 2700×1650 XML preview                                                   | SVG nodes, polylines and text                                                                                                 |

The input SHA-256 is `37477f7138280979950d165e5c74aa7b87fc572f1de59cec55b86d1740024a87`. All 24 legacy files, including metadata, were fingerprinted for final read-only verification. The README's references to an earlier image and `Templates Final/Compressor_Package/compressor.py` are provenance claims; those originals are not present in this directory and their equivalence was not independently audited.

**Saved-drawing discrepancy:** the saved draw.io has only **43 material edges** against 44 configured/result streams: `treater_water` is missing. It also contains an extra boundary object `89LA48TEDsz7bNHUmfOe-2` labelled “Água — treater”, in addition to `product_treater_water`. All other named material edges have the expected endpoints. The current exporter produces all 44 material edges and 42 scene nodes in memory; the saved draw.io has 43 object vertices. The saved SVG contains 48 polylines (44 material + 4 safety), matching the current scene's count. XML evidence cannot establish when or why the draw.io diverged; do not treat it as authoritative topology or an untouched regression snapshot. No visual/browser inspection or draw.io application round-trip is claimed in this audit.

## 3. Reconstructed actual topology

The graph is **cyclic**, not a simple separation/compression train. The oil path passes through primary separation, sensible heating, letdown, mixing, a 5-bar gas/liquid separator, prescribed water removal, sensible cooling, another letdown/mixer and a 1-bar gas/liquid separator. Gas from the lower separators is boosted back to the main suction system. Three condensate-return lines close upstream feedback paths; the two additional gas tears decouple the coupled calculation. Two other condensate drains terminate externally. The network has explicit branching at separators and `S-GAS`, and four explicit mixers; implicit fan-out is prohibited.

Source: `well_feed`, 1000 kmol/h, mole fractions `[0.25, 0.45, 0.30]` on ordered basis `[LightHC, HeavyHC, Water]`, 313.15 K, 10 bar absolute. These are fictitious demo inputs, distinct from Treinamento Bia. Assumed MWs are `[44, 200, 18.01528] kg/kmol`; component Cps `[60, 60, 75.3] kJ/(kmol K)`.

Eight sinks are the `products` dictionary entries: `primary_water`, `treater_water`, `oil_to_tanks`, `interstage_condensate`, `mp_condensate`, `gas_export`, `fuel_gas`, `gas_lift`. Their labels and connections are enumerated below. Source/sink drawing IDs use `feed_`/`product_` prefixes; they are not active-model IDs.

## 4. Equipment table

All rows below come directly from `L/flowsheet_03.json::equipment`. Port contracts are in `L/engine/flowsheet.py::PORTS`; each model's behavior is detailed in section 7. P is bar absolute, T is K. “Calculated T” means the provisional model's prediction, not validated real-fluid behavior.

| Tag        | Configured label           | Type                    | Inlet ports                  | Outlet ports       | Case specification                                     |
| ---------- | -------------------------- | ----------------------- | ---------------------------- | ------------------ | ------------------------------------------------------ |
| `SEP-10`   | Separador trifásico        | `three_phase_separator` | inlet                        | gas, oil, water    | P=10; T=313.15; K=[5, 0.1]; water recovery=0.95        |
| `M-GAS-10` | M-GAS-10                   | `mixer`                 | primary, booster, condensate | outlet             | P=10                                                   |
| `KO-10`    | Main suction scrubber      | `two_phase_separator`   | inlet                        | gas, liquid        | P=10; T=313.15; K=[8, 0.15]                            |
| `K-1`      | Main compressor 1          | `compressor`            | inlet                        | outlet             | ratio=4; calculated T; Cp=60; efficiencies .75/.98/.96 |
| `AC-1`     | Main aftercooler 1         | `cooler`                | inlet                        | outlet             | T=313.15; ΔP=0                                         |
| `KO-40`    | Interstage scrubber        | `two_phase_separator`   | inlet                        | gas, liquid        | P=40; T=313.15; K=[3, 0.05]                            |
| `K-2`      | Main compressor 2          | `compressor`            | inlet                        | outlet             | ratio=4; calculated T; Cp=60; efficiencies .75/.98/.96 |
| `AC-2`     | Main aftercooler 2         | `cooler`                | inlet                        | outlet             | T=313.15; ΔP=0                                         |
| `KO-160`   | Final gas scrubber         | `two_phase_separator`   | inlet                        | gas, liquid        | P=160; T=313.15; K=[1.3, 0.015]                        |
| `S-GAS`    | Gas distribution           | `splitter`              | inlet                        | export, fuel, lift | export/fuel/lift=.7/.1/.2                              |
| `LV-KO10`  | LV-KO10                    | `valve`                 | inlet                        | outlet             | P=5                                                    |
| `LV-KO40`  | LV-KO40                    | `valve`                 | inlet                        | outlet             | P=40                                                   |
| `LV-KO160` | LV-KO160                   | `valve`                 | inlet                        | outlet             | P=10                                                   |
| `H-OIL`    | Oil heating to 100°C       | `heater`                | inlet                        | outlet             | T=373.15; ΔP=0                                         |
| `V-OIL5`   | V-OIL5                     | `valve`                 | inlet                        | outlet             | P=5                                                    |
| `M-OIL5`   | M-OIL5                     | `mixer`                 | primary, condensate          | outlet             | P=5                                                    |
| `SEP-5`    | Separator above treater    | `two_phase_separator`   | inlet                        | gas, liquid        | P=5; T=373.15; K=[10, 0.3]                             |
| `ET`       | Tratador eletrostático     | `electrostatic_treater` | inlet                        | oil_out, water_out | P=5; water recovery=0.995                              |
| `C-OIL`    | Oil cooling to 40°C        | `cooler`                | inlet                        | outlet             | T=313.15; ΔP=0                                         |
| `V-OIL1`   | V-OIL1                     | `valve`                 | inlet                        | outlet             | P=1                                                    |
| `M-OIL1`   | M-OIL1                     | `mixer`                 | oil, condensate              | outlet             | P=1                                                    |
| `SEP-1`    | Final horizontal separator | `two_phase_separator`   | inlet                        | gas, liquid        | P=1; T=313.15; K=[20, 0.6]                             |
| `K-LP`     | Low pressure booster       | `compressor`            | inlet                        | outlet             | Pout=5; calculated T; Cp=60; efficiencies .75/.98/.96  |
| `AC-LP`    | LP aftercooler             | `cooler`                | inlet                        | outlet             | T=313.15; ΔP=0                                         |
| `KO-LP`    | LP booster scrubber        | `two_phase_separator`   | inlet                        | gas, liquid        | P=5; T=313.15; K=[10, 0.3]                             |
| `LV-KOLP`  | LV-KOLP                    | `valve`                 | inlet                        | outlet             | P=1                                                    |
| `M-GAS5`   | M-GAS5                     | `mixer`                 | process, booster             | outlet             | P=5                                                    |
| `K-MP`     | Medium pressure booster    | `compressor`            | inlet                        | outlet             | Pout=10; calculated T; Cp=60; efficiencies .75/.98/.96 |
| `AC-MP`    | MP aftercooler             | `cooler`                | inlet                        | outlet             | T=313.15; ΔP=0                                         |
| `KO-MP`    | MP booster scrubber        | `two_phase_separator`   | inlet                        | gas, liquid        | P=10; T=313.15; K=[8, 0.15]                            |
| `LV-KOMP`  | LV-KOMP                    | `valve`                 | inlet                        | outlet             | P=10                                                   |

Active counts: 1 three-phase separator, 7 two-phase separators (5 vertical knockout vessels and 2 horizontal process separators), 4 compressors, 5 coolers, 1 heater, 7 valves, 4 mixers, 1 splitter and 1 treater = 31. Pump and two-sided heat exchanger are implemented but have **zero instances** in this case.

Inactive annotation: `FLARE-KO`, type label `two_phase_separator`, unspecified P/T, zero normal-operation relief flow. Sources `KO-10`, `KO-40`, `KO-160` connect by dashed safety annotations to this symbol, then to `flare_boundary` / “Flare”. Neither vessel nor relief flows enter `simulate`. Five `control_signals` entries pair KO-10/40/160/MP/LP with their LV valves; they carry no controller equations and `scene` does not iterate that array to generate control edges. Do not count these as material streams.

## 5. Complete stream/connectivity table

The **44 rows** are stream names used as dictionary keys, not engineering numbers. Endpoint notation is `equipment.port`. External source/sink ports below are conceptual boundary endpoints: the legacy input stores feeds/products by name rather than explicit boundary-port objects. Every other port is the exact JSON key. “Tear” identifies the configured numerical tear; it is not an external feed.

| Stream key/name             | Source                     | Destination                                            | Role             |
| --------------------------- | -------------------------- | ------------------------------------------------------ | ---------------- |
| `well_feed`                 | External source: well_feed | SEP-10.inlet                                           | External feed    |
| `primary_gas`               | SEP-10.gas                 | M-GAS-10.primary                                       | Internal         |
| `primary_oil`               | SEP-10.oil                 | H-OIL.inlet                                            | Internal         |
| `primary_water`             | SEP-10.water               | External sink: Água — primary separator                | External product |
| `main_suction_feed`         | M-GAS-10.outlet            | KO-10.inlet                                            | Internal         |
| `main_stage1_gas`           | KO-10.gas                  | K-1.inlet                                              | Internal         |
| `main_suction_liquid`       | KO-10.liquid               | LV-KO10.inlet                                          | Internal         |
| `main_stage1_hot`           | K-1.outlet                 | AC-1.inlet                                             | Internal         |
| `main_stage1_cooled`        | AC-1.outlet                | KO-40.inlet                                            | Internal         |
| `main_stage2_gas`           | KO-40.gas                  | K-2.inlet                                              | Internal         |
| `interstage_liquid`         | KO-40.liquid               | LV-KO40.inlet                                          | Internal         |
| `main_stage2_hot`           | K-2.outlet                 | AC-2.inlet                                             | Internal         |
| `main_stage2_cooled`        | AC-2.outlet                | KO-160.inlet                                           | Internal         |
| `dry_gas`                   | KO-160.gas                 | S-GAS.inlet                                            | Internal         |
| `hp_liquid`                 | KO-160.liquid              | LV-KO160.inlet                                         | Internal         |
| `gas_export`                | S-GAS.export               | External sink: Exportação de gás                       | External product |
| `fuel_gas`                  | S-GAS.fuel                 | External sink: Consumo de gás                          | External product |
| `gas_lift`                  | S-GAS.lift                 | External sink: Gas lift                                | External product |
| `suction_condensate_return` | LV-KO10.outlet             | M-OIL5.condensate                                      | Internal; tear   |
| `interstage_condensate`     | LV-KO40.outlet             | External sink: Unconnected interstage condensate drain | External product |
| `hp_condensate_return`      | LV-KO160.outlet            | M-GAS-10.condensate                                    | Internal; tear   |
| `heated_primary_oil`        | H-OIL.outlet               | V-OIL5.inlet                                           | Internal         |
| `oil_at_5bar`               | V-OIL5.outlet              | M-OIL5.primary                                         | Internal         |
| `separator5_feed`           | M-OIL5.outlet              | SEP-5.inlet                                            | Internal         |
| `separator5_gas`            | SEP-5.gas                  | M-GAS5.process                                         | Internal         |
| `separator5_liquid`         | SEP-5.liquid               | ET.inlet                                               | Internal         |
| `treated_oil`               | ET.oil_out                 | C-OIL.inlet                                            | Internal         |
| `treater_water`             | ET.water_out               | External sink: Água — treater                          | External product |
| `cooled_treated_oil`        | C-OIL.outlet               | V-OIL1.inlet                                           | Internal         |
| `oil_at_1bar`               | V-OIL1.outlet              | M-OIL1.oil                                             | Internal         |
| `separator1_feed`           | M-OIL1.outlet              | SEP-1.inlet                                            | Internal         |
| `separator1_gas`            | SEP-1.gas                  | K-LP.inlet                                             | Internal         |
| `oil_to_tanks`              | SEP-1.liquid               | External sink: Óleo → tanques                          | External product |
| `lp_hot_gas`                | K-LP.outlet                | AC-LP.inlet                                            | Internal         |
| `lp_cooled_gas`             | AC-LP.outlet               | KO-LP.inlet                                            | Internal         |
| `lp_gas_return`             | KO-LP.gas                  | M-GAS5.booster                                         | Internal; tear   |
| `lp_liquid`                 | KO-LP.liquid               | LV-KOLP.inlet                                          | Internal         |
| `lp_condensate_return`      | LV-KOLP.outlet             | M-OIL1.condensate                                      | Internal; tear   |
| `mp_suction_gas`            | M-GAS5.outlet              | K-MP.inlet                                             | Internal         |
| `mp_hot_gas`                | K-MP.outlet                | AC-MP.inlet                                            | Internal         |
| `mp_cooled_gas`             | AC-MP.outlet               | KO-MP.inlet                                            | Internal         |
| `mp_gas_return`             | KO-MP.gas                  | M-GAS-10.booster                                       | Internal; tear   |
| `mp_liquid`                 | KO-MP.liquid               | LV-KOMP.inlet                                          | Internal         |
| `mp_condensate`             | LV-KOMP.outlet             | External sink: Unconnected MP condensate drain         | External product |

## 6. ASCII flowsheet

Arrows below denote actual material connections; numbers are intentionally absent because the legacy does not assign engineering stream numbers. Refer to section 5 for all exact stream and port names.

```text
well_feed -> SEP-10
               |gas -> M-GAS-10 <--------------------------- mp_gas_return
               |          ^  <----------------------------- hp_condensate_return
               |          |
               |          v
               |        KO-10 --gas--> K-1 -> AC-1 -> KO-40 --gas--> K-2 -> AC-2 -> KO-160
               |          |liquid                       |liquid                         |gas
               |          v                             v                               v
               |       LV-KO10                       LV-KO40                          S-GAS
               |          |                             |                       export / fuel / lift
               |          |                             +-> interstage_condensate      (sinks)
               |          +-> suction_condensate_return -> M-OIL5
               |                                                               ^
               |oil -> H-OIL -> V-OIL5 ------------------------------------------+
               |                                                               |
               |water -> primary_water (sink)                                   v
               |                                                             SEP-5
               |                                           gas ----------------+--liquid
               |                                            |                      v
               |                                            |                      ET -> treater_water (sink)
               |                                            |                      |oil
               |                                            |                      v
               |                                            |                  C-OIL -> V-OIL1 -> M-OIL1
               |                                            |                                      ^  |
               |                                            |                lp_condensate_return --+  v
               |                                            |                                      SEP-1
               |                                            |                         oil_to_tanks <-+ |gas
               |                                            |                              (sink)    v
               |                                            |                         K-LP -> AC-LP -> KO-LP
               |                                            |                                          |liquid
               |                                            |                                          v
               |                                            |                                       LV-KOLP
               |                                            |                                          |
               |                                            |                              lp_condensate_return
               |                                            v
               |                                          M-GAS5 <---- lp_gas_return <---- KO-LP.gas
               |                                            |
               |                                            v
               |                                         K-MP -> AC-MP -> KO-MP
               |                                                           |gas -> mp_gas_return -> M-GAS-10
               |                                                           |liquid
               |                                                           v
               |                                                        LV-KOMP -> mp_condensate (sink)

KO-160.liquid -> LV-KO160 -> hp_condensate_return -> M-GAS-10

Inactive only: KO-10 / KO-40 / KO-160 - - -> FLARE-KO - - -> Flare
```

The long left vertical guide is visual alignment only; SEP-10 has exactly the three outlet branches stated in section 5. Representative directed cycles are M-GAS-10 → KO-10 → main compression/scrubbing → KO-160 → LV-KO160 → M-GAS-10; M-OIL1 → SEP-1 → K-LP → AC-LP → KO-LP → LV-KOLP → M-OIL1; and M-GAS-10 → KO-10 → LV-KO10 → M-OIL5 → SEP-5 → M-GAS5 → K-MP → AC-MP → KO-MP → M-GAS-10. Additional longer coupled paths follow the oil train. Five tears must not be described as five independent physical feed streams or proof of exactly five simple directed loops.

## 7. Equipment models: implemented behavior and limits

Common contract: `L/engine/models.py::execute(unit, inputs, config)` dispatches by type and calls `equipment_common.check_balance` on all outlets. Adapters return new `Stream` objects plus a results dictionary. Ordered components and units are global. `finite` rejects booleans, nonnumeric/nonfinite values and invalid ranges; `fraction` enforces [0,1]. Topology guards are separate from numerical guards. Model validity is explicitly restricted; successful balances alone do not qualify physical assumptions.

### Source and sink

`flowsheet.read_stream` loads `feeds` and tear guesses: finite nonnegative molar flow, positive T/P, matching nonnegative mole fractions summing to one within `1e-10`; zero flow may have null composition. `products` identifies terminal streams and supplies display labels. There is no source/sink `execute`, outlet-property prediction or sink back-pressure solution. Feed enthalpy/density fields are not loaded; only the optional phase label survives `read_stream`.

### Mixer

`mixer.execute`: arbitrary named inlet ports → `outlet`; requires specified positive pressure and component Cp list. Sums component molar rates; computes `Tmix = Σ(F Cp_mix T)/Σ(F Cp_mix)`. All-zero flow uses the first inlet's T. Pressure may not exceed any active inlet by more than `1e-8 bar`. Output flow/composition come from summed rates; no component is dropped. It marks `energy_status=not_calculated` despite this sensible-temperature calculation. No flash, heat/work result, phase inference, common enthalpy-reference check or pressure-equalization thermodynamics. `make_stream` leaves the outlet phase null here, which weakens subsequent declared-phase checking.

### Splitter

`splitter.execute`: `inlet` → arbitrary named outlet ports; requires one [0,1] fraction per port with sum within `1e-10` of one. Every component is multiplied by the same fraction. T, P and optional phase label are preserved; absent output composition is null. No phase-selective splitting, duty/work or absolute enthalpy propagation; `energy_status=not_calculated`. This is a proportional flow splitter, distinct from a separator.

### Valve

`valve.execute`: `inlet` → `outlet`; requires `model=specified_pressure_no_flash` and positive outlet pressure no greater than inlet plus `1e-8 bar`. Conserves all component rates and carries T/phase through unchanged. Energy is unavailable. No PH/isenthalpic flash, Joule–Thomson effect, Cv, choking or hydraulic sizing. Zero-drop valves LV-KO40/LV-KOMP represent unknown receiving conditions, not calculated valve performance.

### Heater and cooler

`heater.execute` / `cooler.execute`: `inlet` → `outlet`; require `constant_cp_outlet_temperature`, positive specified T, component Cp and nonnegative pressure drop (default zero). Reject opposite duty direction for present flow and nonpositive resulting P. Preserve component rates/phase; compute `Q = F Cp_mix (Tout−Tin)/3600 kW`, positive into fluid. No latent heat, flash, utility side, UA or phase-stability verification. Results explicitly state sensible heat only. They do not propagate an absolute enthalpy field. These are not two-sided heat exchangers.

### Three-phase separator

`ThreePhaseSeparatorSpec`, `calculate_three_phase_separator` and `three_phase_separator` in `three_phase_separator.py` validate component basis, positive P/T/K, pressure not above feed, unique output names and required nonwater K mapping. The low-level function isolates nonvolatile water, flashes the remaining mixture via `material_balance.flash`, creates `gas/oil/water` streams at specified P/T and checks component and optional MW-based mass balances. It assumes ideal removal of all water at that low level.

The integrated `execute` requires `model=specified_K_immiscible_water`, outlet P, optional T (defaults to feed), nonwater K values and `water_recovery`. It always calls the low-level function in **material_only** mode, then moves unrecovered water into the oil stream. SEP-10 uses 95% water recovery. Outlet ports are `gas`, `oil`, `water`; duty is null. No rigorous aqueous equilibrium, dissolution, entrainment, emulsion, salinity, sizing or electrostatic physics.

Low-level-only energy modes `duty_from_enthalpies` and `adiabatic_check` accept supplied feed/outlet molar enthalpies with the same explicit reference. They calculate duty or reject a specified state inconsistent with zero duty; they do not solve outlet T or calculate enthalpies. Those capabilities are **not wired into the flowsheet adapter**. Adapter reconstruction also discards the low-level optional property metadata.

### Two-phase separator

`two_phase_separator.execute`: `inlet` → `gas`, `liquid`; same specified P/T/nonwater K model and low-level validation. It reuses the three-phase calculation but combines all isolated water with nonwater liquid (recovery to a separate water outlet is zero). No water disappears. T/P are imposed, and duty is null; no PH flash or EOS. Seven configured units use this adapter. Distinguish the vertical/horizontal drawing orientation from the unchanged calculation model.

### Electrostatic treater

`electrostatic_treater.execute`: `inlet` → `oil_out`, `water_out`; requires `specified_water_recovery_no_flash`, water-component identity, positive P equal to inlet within `1e-8 bar`, and recovery in [0,1]. Removes only the specified fraction of inlet water, preserving all other components and residual water in oil. Both outlets retain inlet T. ET uses 0.995 recovery. Electrical power is null and energy unavailable; no predicted efficiency, electric field, emulsion treatment, gas separation or sizing.

### Compressor

`CompressorSpec`, `calculate_compressor`, `compressor`, `execute` in `compressor.py`: `inlet` → `outlet`; declared dry-gas `ideal_gas_constant_cp`, molar Cp > R, three efficiencies in (0,1], MW/component basis, positive flow/T/P and exactly one pressure closure (outlet P or pressure ratio > 1). Rejects known liquid/wet feed; unknown/unspecified phase is permitted rather than independently checked.

It conserves molar flow/composition; predicts discharge T from isentropic ideal-gas constant-Cp compression, then gas/shaft/electric powers, losses, ideal-gas actual volumes, entropy-generation rate and local energy/component/mass residuals. Optional supplied inlet enthalpy plus a reference permits an outlet enthalpy increment. No performance map, real-gas compressibility, EOS, condensation or mechanical design. The absent-flow adapter evaluates a synthetic 1 kmol/h first-component gas, then zeros extensive power/flow results; its finite discharge T remains model-derived even with no material present.

### Pump — implemented, unused in the supplied network

`PumpSpec`, `calculate_pump`, `pump`, `execute` in `pump.py`: `inlet` → `outlet`; declared constant-density single-phase liquid, density, mass Cp, MWs, pump/motor efficiencies, positive state/flow and exactly one outlet-P, pressure-rise or head closure. Rejects known gas/vapor, invalid efficiencies and nonpositive rise. Conserves flow/composition; calculates head, volume, hydraulic/shaft/electric power, motor losses, pressure work and irreversible temperature rise. Uses `Δh_rev=ΔP/ρ`, `Δh_actual=Δh_rev/η`, `ΔT=(Δh_actual−Δh_rev)/Cp`; checks reconstructed local energy residual. Optional reference enthalpy is advanced by shaft energy to the fluid. Density is specified, not correlated. NPSH, curves, cavitation, multiphase and equilibrium checks are absent. Zero-flow adapter uses a synthetic water composition to validate/evaluate then zeros extensive results. No pump regression is present in this directory's test suite.

### Two-sided heat exchanger — implemented, unused in the supplied network

`HeatExchangerSpec`, `calculate_heat_exchanger`, `effectiveness`, `heat_exchanger`, `execute` in `heat_exchanger.py`: `hot_in/cold_in` → `hot_out/cold_out`, no mixing. Low level accepts exactly one duty, UA, hot-outlet-T or cold-outlet-T closure, explicit constant-Cp single-phase model, arrangement parallel/countercurrent, Cps, drops and minimum approach. Calculates Q, outlet T/P, effectiveness, terminal approach, LMTD, required UA and independent per-side component and energy residuals. Rejects invalid composition/state, capacity-limit violation, reversed heat transfer, invalid pressure and approach/pinch violations. Does not prove the sides remain single-phase or propagate absolute enthalpy/phase metadata.

The integrated adapter supports **UA mode only**, obtains side Cps from the global mixture list and special-cases an absent side to no heat transfer while retaining pressure drops. That branch performs fewer model/approach/arrangement checks than the positive-flow low-level path. No heat-exchanger regression exists here. Presence of the module does not establish Flowsheet 03 operational use or qualification.

## 8. Material-stream architecture

`material_balance.Stream` stores `name`, `flow` (kmol/h), ordered mole-fraction `composition`, `temperature` (K), `pressure` (bar absolute). `equipment_common.make_stream` derives flow and fractions from component rates and dynamically attaches `phase`. Core identity is an explicit **name/key**; there is no separate immutable software ID, service name or engineering stream number. Source/destination are reconstructed by scanning equipment `inlet/inlets/outputs`, not stored on the Stream.

Component molar rates are derived as F×z; total mass and component masses require the global MW basis. `Run_Flowsheet.main` adds `flow_kg_h` on serialization. Dynamic properties differ by model: compressor may attach vapor_fraction, mass and referenced molar/flow enthalpy; pump may attach density; the low-level separator attaches phase/mass/enthalpy fields. There is no universal typed property/status/unit contract, and no common density/viscosity/property provider. Most active-case streams have no enthalpy fields; splitter, mixer, heater, cooler, valve and separator adapters reconstruct streams and can lose dynamic metadata.

`simulate` associates results by `streams[name]`, overwriting the previous guess/produced object. Each equipment run allocates outlet objects anew; no identity object is retained across sweeps. The name is stable by graph convention, not enforced as a distinct engineering identity field in an immutable structure. Exported `edge_0`, etc. are drawing-order IDs, not engineering numbers.

By contrast, `R/engine/riogineer_engine/core.py::build_flowsheet` and `streams.py::number_streams` define stable stream IDs, separate service labels and deterministic stored engineering numbers; connections explicitly store owner/port endpoints. `core.calculate` returns values keyed by stable IDs; `R/src/lib/digital-engineer/workflow.ts::workflowReducer` retains original stream objects; `stream-table.ts::streamColumns` joins current results by ID/fingerprints. Future reuse must enrich those streams, never replace them with legacy name-only objects.

## 9. Flowsheet/network architecture

The legacy is **JSON-defined, port-referenced and graph-scheduled**, implemented with dictionaries/lists rather than a graph library. It is neither a fixed script that invokes 31 hard-coded units nor an object-linked network. Equipment dictionaries mix engineering parameters, label/orientation/position and later results. The callable registry (`models.EQUIPMENT_MODELS`) and the separately maintained `flowsheet.PORTS` table can drift; model IDs are strings without independent version/capability metadata.

`validate_topology` constructs producer/consumer maps, checks unique nonempty components/equipment IDs, water-component presence, at least one feed, supported types, exact fixed port sets, matching splitter port/fraction keys, unique producer and consumer for each stream, known inputs and terminal-products equality. It requires tears to be internal produced-and-consumed streams. Multiple consumers are rejected with “insert a splitter”.

Execution availability starts with feed names plus tears. Repeatedly select the **first** pending unit whose input names are available; append it and expose its output names. If none is ready, reject an unbroken cycle. Thus dependencies are generic and explicit; tie-breaking follows the equipment array rather than canonical stable-ID order. There is no automatic SCC decomposition, tear selection, nonlinear block solution or pressure-network solver. Model numerical validation occurs during execution. The input `schema_version: 1` and `units` metadata are not enforced by a strict JSON schema; unit conventions live in code. JSON duplicate keys are not explicitly rejected by the runner.

The drawing code reconstructs endpoints again, depends on required positions, infers service colors from names and contains tag-specific routing/orientation rules (SEP-1, K-LP, K-MP) and a mandatory flare layout. It writes editable XML, but there is no importer that turns edits back into a validated engineering model. The saved-drawing discrepancy illustrates that distinction.

## 10. Material-balance architecture

1. `flowsheet.read_stream` validates F/z and converts to rates; `equipment_common.amounts` supplies component vectors, including zeros for absent composition.
2. Mixers sum vectors; splitters scale vectors; valves/heaters/coolers/pumps/compressors/HX sides conserve their component vectors.
3. Separator low-level logic flashes nonwater components; adapters distribute water explicitly. Treater removes only prescribed water. These are equipment-specific distributions.
4. `models.execute` always invokes `check_balance`: component residual = Σin−Σout. Reject if maximum magnitude exceeds `1e-9 * max(1, total inlet kmol/h)`. Report component residuals and their MW-weighted mass residual. The global wrapper checks component conservation, not a separately tolerance-tested mass residual; low-level separator/pump have additional checks.
5. After tear convergence, `simulate` compares external feed and product vectors, excluding internal tears. It checks a common component tolerance scaled by tear count and reports MW-weighted external mass residual. It does not add tears as external supply.

Conservation concepts and explicit absent-stream handling are generic. K splitting and prescribed water recoveries are model-specific. A vanishing component has only the total-flow-scaled local guard, so future qualification should include trace-component and large-scale tests. Reuse with RioGineer's mass basis requires deliberate unit/component mapping, not direct molar-array copying.

## 11. Energy-balance architecture

Local equations exist; there is **no consistent network-wide enthalpy transport**. `simulate` explicitly returns `plant_energy_balance_status=not_calculated_no_consistent_phase_enthalpy_model` and the CLI prints that limitation.

| Model                     | Implemented energy behavior                                                                                | Important boundary                                                                          |
| ------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| Mixer                     | Cp-weighted sensible T                                                                                     | No emitted energy closure or phase change; status stays not_calculated                      |
| Heater/cooler             | F Cp_mix ΔT / 3600 kW                                                                                      | Sensible-only, no latent heat or referenced h                                               |
| Compressor                | T2s=T1(P2/P1)^(R/Cp); T2=T1+(T2s−T1)/η; fluid power=F Cp ΔT/3600; shaft=fluid/ηmech; electric=shaft/ηmotor | Adiabatic ideal gas; losses outside fluid; local residuals do not prove whole-plant closure |
| Pump, unused              | Hydraulic ΔP/ρ; shaft adds fluid enthalpy; inefficiency heats fluid; motor loss external                   | Specified incompressible density/Cp                                                         |
| HX, unused                | Ch=Fh Cph/3600; Cc=Fc Cpc/3600; Th,out=Th,in−Q/Ch; Tc,out=Tc,in+Q/Cc                                       | Two sensible sides, no phase change; UA effectiveness/LMTD calculations                     |
| Separator low level       | Hin=Fhin/3600; Hout=ΣFjhj/3600; Q=Hout−Hin, or check Hin−Hout≈0                                            | Supplied phase enthalpies and matching explicit reference required                          |
| Active separator adapters | Imposed T/P, duty null                                                                                     | Always material_only; imposed temperatures need not satisfy energy balance                  |
| Treater, valve, splitter  | No energy calculation                                                                                      | Treater electrical power also null; valve is not isenthalpic                                |

Global Cps are constant, mole-based and composition-weighted; there is no declared common Tref for absolute network enthalpy. Optional low-level enthalpy reference identifiers are supplied by callers, not calculated. Feed loading does not retain those optional attributes. Ideal-gas compressor pressure effects and incompressible pump pressure work are the only such local energy models; the nonwater K values are not functions of P/T.

RioGineer currently has a narrower but internally consistent declared constant-Cp reference-temperature accounting model (`R/engine/fixtures/treinamento-bia-110000/recovery_model.py::evaluate`). Preserve it rather than replacing it with a larger network that lacks energy closure.

## 12. Thermodynamic/property functionality

**Present:** `material_balance.flash` solves Rachford–Rice for supplied positive K values and a normalized nonwater feed. Tests for endpoint liquid/vapor states precede 100 bisection iterations on vapor fraction β; two-phase compositions follow `xi=zi/[1+β(Ki−1)]`, `yi=Ki xi`. All K=1 is rejected as undetermined. The low-level routine is not itself a comprehensive nonfinite guard; integrated separator validation supplies that guard. There is no convergence tolerance/error estimate on the 100-step flash bisection.

**Present but provisional:** fixed-K phase flows/compositions, categorical phase labels; constant Cp mixtures; ideal-gas compressor power/T/entropy and actual volumes; specified-density pump volume/work/heating; HX effectiveness–NTU and LMTD. Flash vapor fraction exists internally as V/F, not as a universally stored stream property. Compressor's outlet vapor fraction is declared 1, not the result of a stability calculation.

**Absent:** EOS-based equilibrium/property package, fugacity coefficients, temperature/pressure-dependent K generation, rigorous aqueous phase equilibrium/VLLE, PH or PS flash, latent heat, phase-consistent enthalpy model, density correlations, viscosity, transport-property package, phase stability and real-fluid compressor behavior. The ideal-gas volume relation is implemented locally, but must not be described as an integrated EOS equilibrium package. Water is nonvolatile/immiscible and hydrocarbons do not dissolve in the water outlet.

No provisional property model should be imported just because it exists. Topology and stable stream architecture come first; qualified EOS-based equilibrium belongs to a later, independently benchmarked property-model milestone.

## 13. Recycles and convergence

`L/engine/flowsheet.py::simulate` is a relaxed successive-substitution solver with **manually declared tears** in `flowsheet_03.json::solver.tear_streams`. No tags or Flowsheet 03-specific stream names are embedded in its iteration algorithm.

| Tear                        | Producer → consumer                   | Initial F (kmol/h) | Initial z (LightHC, HeavyHC, Water) |  T (K) | P (bar abs) |
| --------------------------- | ------------------------------------- | -----------------: | ----------------------------------- | -----: | ----------: |
| `mp_gas_return`             | KO-MP.gas → M-GAS-10.booster          |                100 | [0.9, 0.1, 0]                       | 313.15 |          10 |
| `lp_gas_return`             | KO-LP.gas → M-GAS5.booster            |                 50 | [0.8, 0.2, 0]                       | 313.15 |           5 |
| `hp_condensate_return`      | LV-KO160.outlet → M-GAS-10.condensate |                 30 | [0.5, 0.5, 0]                       | 313.15 |          10 |
| `suction_condensate_return` | LV-KO10.outlet → M-OIL5.condensate    |                 15 | [0.2, 0.8, 0]                       | 313.15 |           5 |
| `lp_condensate_return`      | LV-KOLP.outlet → M-OIL1.condensate    |                 10 | [0.1, 0.9, 0]                       | 313.15 |           1 |

Case settings: relaxation α=0.5; maximum 1000 iterations; component absolute tolerance `1e-8 kmol/h`; relative tolerance `1e-10`; T absolute tolerance `1e-7 K`; P absolute tolerance `1e-8 bar`. Code defaults match except maximum defaults to 500. Only `relaxed_successive_substitution` is accepted; relaxation must be in (0,1], iteration count a positive nonboolean integer, absolute tolerances positive and relative tolerance nonnegative.

Algorithm trace:

1. Deep-copy configuration; validate topology, global MW/Cp arrays, feeds, guesses and solver settings.
2. Build the dependency schedule after treating tears as available.
3. At each sweep initialize streams from feeds and previous guesses. Every tear consumer uses `guesses[name]` throughout that sweep, even if the producer already ran. Producers write their new outlet to `streams[name]`. This avoids accidental in-sweep updating of a tear.
4. Execute each unit, validate returned stream F/z/T/P via `read_stream`, attach material-balance residuals and collect equipment results.
5. For each tear compare **unrelaxed produced values** with the old guess: component-rate vector, T and P. For component i the scaled residual is `abs(nnew−nold)/(atol + rtol*max(abs(nnew),abs(nold)))`; T/P residuals use their absolute tolerances. Take the maximum across components, T/P and all tears.
6. Append iteration number and maximum scaled residual to history. Accept only when the global maximum ≤1 **and** external component balance passes. External tolerance is `max(1, number_of_tears)*(atol+rtol*max(1, incoming_components, outgoing_components))`.
7. Otherwise relax component rates (not mole fractions), T and P: new guess=(1−α)old+αproduced. Reconstruct fractions from the relaxed vector; copy the produced phase label.
8. On success return streams, equipment and final per-tear residuals/history, external material residuals and explicit unavailable plant energy status. On exhaustion raise `RuntimeError` with maximum scaled residual; there is no successful result. Invalid unit calculations are wrapped with the equipment ID.

For an acyclic case with no tears this reduces to one sweep and the external material check. There is no acceleration, adaptive damping, automatic tear choice, Jacobian, Newton/Wegstein/Broyden solver, phase/enthalpy convergence variable, or persistent failed-iteration report. The success history records only each maximum, not full per-tear history. Failure raises before the runner writes new outputs, but **old output files remain on disk**, so users must not mistake them for a successful new run.

Reusability verdict: the substitution/update and residual concepts are generic; the surrounding solver is **partly reusable**, needing adaptation to versioned stable-ID contracts and stronger diagnostics/tests. A generic algorithm passing one demo plus guess/order variations does not establish reliability for arbitrary strongly coupled networks. At convergence, producer states and downstream states used in the last sweep differ by the accepted tear tolerances; there is no exact-consistency final sweep.

## 14. Exact execution sequence

Documented normal command (not invoked by this audit):

```sh
cd "/Users/giovaninunes/Folders/FieldDesignCode/Simulation Repository/Learning Flash/Flowsheet 03"
python3 -B Run_Flowsheet.py
```

Python 3.10+ is required by union type annotations. Imports use standard library only. `Run_Flowsheet.main` disables bytecode and prepends the local `engine` directory to `sys.path`. Optional positional case defaults to adjacent `flowsheet_03.json`; no other input file is required.

1. Parse CLI and JSON with `json.load`; run `validate_topology`.
2. `--validate-topology` prints unit/tear counts and exits without calculation/output. Its print expression expects a `solver.tear_streams` object even though validator defaults allow its absence.
3. `--diagram-only` skips process calculation and uses configured equipment; it still validates topology and then writes topology diagrams. It is not a no-write option.
4. Normal mode calls `simulate`: deep-copy, validate again, validate numerical data, schedule, iterate, execute, convergence/external-balance checks.
5. Print case status, iterations, each product's molar flow/T/P/z, external residuals and unavailable plant energy warning.
6. Create `outputs/` beside the case unless `--output-dir` is supplied. Write `<case-stem>_results.json` with streams plus computed mass totals, equipment including results, solver report, product labels and provenance; JSON disallows NaN on output.
7. Export `<case-stem>.drawio` and `<case-stem>.svg`. Diagram-only adds `_topology` and writes no results JSON.
8. Errors of supported IO/data/calculation types print to stderr and return exit code 1. Normal completion returns 0. Output writing is not transactional across all three files.

The exact configured execution order returned during this audit was:

```text
SEP-10, M-GAS-10, KO-10, K-1, AC-1, KO-40, K-2, AC-2,
KO-160, S-GAS, LV-KO10, LV-KO40, LV-KO160, H-OIL, V-OIL5,
M-OIL5, SEP-5, ET, C-OIL, V-OIL1, M-OIL1, SEP-1, K-LP,
AC-LP, KO-LP, LV-KOLP, M-GAS5, K-MP, AC-MP, KO-MP, LV-KOMP
```

This order is a result of the dependency scan and configured tears, not an equipment-tag sequence hard-coded in the solver. The README describes manual JSON editing and opening diagrams; there is no web review workflow, LLM extraction or evidence anchoring.

## 15. Tests and reference cases

The sole automated suite is `L/engine/test_flowsheet.py::Flowsheet03Tests`, with 13 methods. The documented command is `python3 -B -m unittest discover -s engine -p 'test_*.py' -v`. It uses the supplied JSON as a synthetic demo fixture. There is no independent vendor/field benchmark, golden-file test against the saved result JSON, pump/HX-specific test suite, or separate flash numerical benchmark in this directory.

| Test method (prefix `test_`)                          | Assertions / expected result                                                                                                                                        | Audit execution                                                                                           |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `user_conditions_and_compressor_efficiency_equations` | Stage P/T, compressor analytical T/P, cooler T=313.15 K, external residual <5e-8, unit residual <1e-8, compressor energy residual and nonnegative entropy tolerance | Passed                                                                                                    |
| `original_compressor_analytical_reversible_result`    | 100 kmol/h gas, 300 K, ratio 2, Cp=3.5R, all efficiencies 1: T=300×2^(2/7), analytical electric power, zero entropy generation                                      | Passed                                                                                                    |
| `efficiency_changes_temperature_not_pressure`         | K-1 efficiency .6 raises discharge T, leaves P and cooled T unchanged                                                                                               | Passed                                                                                                    |
| `invalid_compressor_efficiency`                       | Efficiency 1.1 rejected                                                                                                                                             | Passed                                                                                                    |
| `known_liquid_rejected_by_compressor`                 | Explicit liquid phase rejected                                                                                                                                      | Passed                                                                                                    |
| `zero_flow_compressor_adapter`                        | Zero flow/null z, Pout=40 bar and electric power zero                                                                                                               | Passed                                                                                                    |
| `guess_independence_and_input_immutability`           | Original config unmodified; doubled tear guesses plus reversed equipment order give product flows equal to 6 places                                                 | Passed                                                                                                    |
| `nonconvergence_rejected`                             | Two iterations and α=1e-12 raise RuntimeError                                                                                                                       | Passed                                                                                                    |
| `unbroken_recycle_rejected`                           | Removing all tears causes topology rejection                                                                                                                        | Passed                                                                                                    |
| `invalid_gas_split`                                   | Export fraction .9 with other fractions unchanged rejected                                                                                                          | Passed                                                                                                    |
| `vertical_vessels_and_flare_boundary`                 | Five vertical two-phase units, zero safety flow, no Flare product                                                                                                   | Passed                                                                                                    |
| `drawing_edges_and_recycle_destinations`              | Unique XML IDs, all stream edges, valid endpoints, three condensate destinations, four safety edges                                                                 | Same assertions passed on in-memory export; original method not run because it writes a temporary diagram |
| `duplicate_material_consumption`                      | Reusing main_stage1_gas as K-2 feed rejected                                                                                                                        | Passed                                                                                                    |

**Audit verification:** 12 existing test methods executed unchanged and passed. Drawing assertions were performed separately against `io.BytesIO` output from the actual exporter. The in-memory simulation's complete serialized stream data, equipment results and solver report equalled the saved JSON exactly. No legacy output was regenerated on disk. The saved draw.io completeness assertion failed for the missing `treater_water` edge; that discrepancy remains untouched and is explicitly recorded in section 2.

Saved reference values (`outputs/flowsheet_03_results.json`; figures below rounded for reading):

| Product                 |        kmol/h |            kg/h |
| ----------------------- | ------------: | --------------: |
| `primary_water`         | 285.000000000 |  5134.354800000 |
| `treater_water`         |  14.925000000 |   268.878054000 |
| `oil_to_tanks`          | 410.424556489 | 80751.375210600 |
| `interstage_condensate` |  38.583385154 |  5778.352393536 |
| `mp_condensate`         |  23.725947323 |  4344.417411642 |
| `gas_export`            | 159.138777732 |  7089.044291788 |
| `fuel_gas`              |  22.734111105 |  1012.720613113 |
| `gas_lift`              |  45.468222209 |  2025.441226225 |

Saved/audit solver: 40 iterations; final maximum scaled residual `0.6309685636086948`; external residual vector `[-8.96818619366968e-9, -2.5413555704290047e-9, 0] kmol/h`; external component tolerance `2.7500000000127067e-7 kmol/h`; mass residual `-9.028713066072669e-7 kg/h`. Feed mass is 106404.584 kg/h from the fictitious MW basis. README compressor outlet temperatures/electrical powers are rounded demo outputs (K-1 128.43°C/470.85 kW, K-2 128.43°C/410.40 kW, K-LP 144.32°C/114.91 kW, K-MP 132.34°C/105.86 kW), not independent expected-value fixtures.

The JSON is useful as a future _software_ regression snapshot with its exact inputs, model assumptions and code version; it is not a validated physical benchmark. README observations and editable drawings are examples/documentation. Current RioGineer suites were not rerun for this report-only audit; their last recorded correction results in `R/MILESTONE_3_1.md` are 178 TypeScript, 20 Python and 17 browser tests, distinct from the legacy checks executed here.

## 16. Comparison with current RioGineer

| Area                   | Current RioGineer                                                                                                                      | Flowsheet 03                                                                            | Reuse potential                                          | Recommendation                                                                          |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- | -------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Requirements           | Strict 1.0 contract, explicit units and approved synthetic assumptions (`R/src/lib/digital-engineer/contracts.ts::requirementsSchema`) | One case dictionary, mixed requirements/graph/layout                                    | Case inputs as examples                                  | Keep reviewed requirements distinct from built graph                                    |
| Flowsheet              | 1.1 stable streams/numbers, explicit boundaries, owner/port connections; one separator/four streams (`core.build_flowsheet`)           | Multi-unit JSON ports mapped to stream names                                            | Connectivity/validation concepts                         | Extend versioned model deliberately in future; do not drop in legacy JSON               |
| Results                | 1.1 IDs, run identity, hashes/model version, balance status and explicit unavailable properties (`core.calculate`)                     | Mutable streams, embedded equipment results and solver report; no freshness fingerprint | Residual/history fields                                  | Preserve result association and add future solver metadata with versioning              |
| Engine                 | Strict schema/semantic validation around unchanged Bia evaluator                                                                       | Registry of 11 models; generic dependency scan                                          | Dispatcher/execution concepts                            | Separate equipment type, model and capability; retain evaluator regression              |
| Stream identity        | Stable ID ≠ engineering number ≠ service                                                                                               | Name serves as key and label; object recreated                                          | Weak direct reuse                                        | Retain current identity contract and enrich properties                                  |
| Engineering numbering  | Stored deterministic graph-based number (`streams.number_streams`)                                                                     | None; XML edge index is a drawing ID                                                    | None needed                                              | Keep current number assignments independent of layout/calculation                       |
| Ports                  | Explicit typed material in/out port objects                                                                                            | Fixed PORTS sets plus variadic mixer/splitter names                                     | Cardinality and fan-out checks                           | One authoritative registry and typed endpoints                                          |
| Network/execution      | Fixed supported topology, single pass; numbering helper does not enable other graphs                                                   | Dependency-driven execution after manual tears                                          | Strong algorithmic reuse                                 | Begin acyclic execution with canonical tie-breaking                                     |
| Validation             | Strict unknown-field/unit/finite/duplicate-key and semantic checks                                                                     | Useful graph and numerical guards, looser case envelope                                 | Negative-case concepts                                   | Preserve stricter current boundary; add graph-specific checks                           |
| Material balance       | Component mass basis kg/h; prescribed recoveries                                                                                       | Component molar basis kmol/h + MW conversion                                            | Conservation algorithms                                  | Explicit basis adapter/design, no silent conversion/default MW                          |
| Energy                 | Consistent declared constant-Cp/reference-T separator accounting                                                                       | More local models, incomplete enthalpy transport/plant closure                          | Selected equations only after qualification              | Keep current basis for topology milestone                                               |
| Recycles               | Unsupported and blocked                                                                                                                | Manual tears, generic relaxed substitution                                              | Future algorithm/reference                               | Defer first recycle until acyclic graph/identity acceptance                             |
| PFD                    | Read-only SVG view from structured connections (`R/src/app/digital-engineer/pfd.tsx`)                                                  | XML/SVG exports, tag-specific layout, no editing round-trip                             | Structured-to-view principle                             | Do not copy layout heuristics or read drawing as engineering truth                      |
| Stream Table           | Number/service/ID plus units, ID-joined results and “—” for unavailable                                                                | No dedicated Engineering Stream Table; embedded stream_json and result JSON             | Saved values as audit examples                           | Extend current generic projection, keep null/status semantics                           |
| Human review           | Reviewed facts, blockers, assumption approval, mandatory validation (`interpretation/review.ts::blockers/finalizeRequirements`)        | Manual file editing/provenance narrative                                                | No replacement capability                                | Preserve review/approval and invalidation                                               |
| Evidence               | Exact-source anchoring (`interpretation/anchoring.ts::anchorEvidence`, `validation.ts::validateProviderEvidence`)                      | Provenance strings, no source offsets or unique anchors                                 | Documentation only                                       | Retain current controls unchanged                                                       |
| Topology normalization | Conservative one-feed/one-separator grammar (`interpretation/topology.ts::normalizeTopology`)                                          | Explicit graph input, no natural-language parser                                        | No normalization implementation                          | Future reviewed capability expansion; never bypass old blockers silently                |
| Tests                  | Contracts, numerical snapshots, provenance/review, HTTP and browser layers                                                             | 13 legacy tests, one coupled demonstration, no pump/HX qualification                    | Negative cases, analytical compressor and recycle checks | Reimplement tests against new contracts, distinguish synthetic from physical validation |

## 17. Reuse classification and technical risks

“A” means reuse the **concept/algorithm**, not unreviewed source copying. No migration occurred in this audit.

| Group                                       | Element and exact evidence                                                                                                               | Rationale / boundary                                                                                                                              |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| A — reuse concept/algorithm directly        | Component-rate addition/scaling and residual construction: `equipment_common.amounts/check_balance`, `mixer.execute`, `splitter.execute` | Basis-independent bookkeeping with explicit tolerances; implement on current identity/unit contract                                               |
| A                                           | Producer/consumer uniqueness, exact ports, terminal-product matching and dependency readiness: `flowsheet.validate_topology`             | Good generic graph invariants; preserve explicit splitters and missing-dependency rejection                                                       |
| A                                           | Old-guess/new-production separation; unrelaxed component/T/P residual; rate-vector damping: `flowsheet.simulate`                         | Prevents false convergence caused by damping; useful later for qualified recycle support                                                          |
| B — reimplement within current architecture | Registry and dependency executor: `models.EQUIPMENT_MODELS`, `flowsheet.PORTS/simulate`                                                  | Useful design but duplicate registries, array-order scheduling and case dictionaries must not replace typed/versioned contracts                   |
| B                                           | Mixer/splitter as explicit equipment with balances                                                                                       | Best first extension; use current mass/Cp basis, known zero-flow behavior and immutable identities                                                |
| B                                           | Future recycle reporting, solver settings and structured failure                                                                         | Algorithm exists; needs stable-ID states, fingerprinted settings, cycle diagnostics and independent small-loop tests                              |
| B                                           | Sensible heater/cooler and local energy-equation adapters                                                                                | Useful later, after consistent enthalpy/reference/unit propagation and tests; no silent phase assumptions                                         |
| C — reference only                          | `flowsheet_03.json`, saved result JSON and README demo values                                                                            | Fictitious composition, MW/K/Cp/efficiencies, assumed routes; software benchmark, not field validation                                            |
| C                                           | Specified-K flash/immiscible-water separator and prescribed treater recovery                                                             | Demonstrates splits and water inventory; not next rigorous separator/treater model                                                                |
| C                                           | Ideal-gas compressor, incompressible pump, constant-Cp HX                                                                                | Explicit restricted models; compressor has some analytical coverage, pump/HX lack local tests and are unused; qualify separately before any reuse |
| C                                           | Existing test cases and editable diagrams                                                                                                | Useful requirements/examples; tests need new contract fixtures; saved drawing is inconsistent                                                     |
| D — do not reuse                            | Name-only mutable Stream with ad hoc attributes; array-index component identity without typed basis                                      | Loses independent IDs/numbers/property guarantees and risks metadata loss                                                                         |
| D                                           | Implicit name-based service coloring, tag-specific drawing rules and edge_i as identity                                                  | Presentation must not decide equipment/stream semantics or numbering                                                                              |
| D                                           | Combined config/layout/results as primary contract; unrestricted unit labels                                                             | Conflicts with deterministic validated engineering state and results freshness                                                                    |
| D                                           | Fixed-K demo as rigorous equilibrium; constant-T valve as PH throttling; imposed separator T as energy closure                           | These interpretations are not implemented or justified; retain explicit unavailable status                                                        |
| D                                           | Reusing old output files after a failed run as current results, or trusting the saved drawing over graph data                            | No freshness/transaction guarantee; observed missing material edge                                                                                |

Principal engineering/software risks:

1. **Model qualification:** demonstration K values, nonvolatile water and ideal gas up to 160 bar are assumptions, not validated fluid behavior. Source: separator/compressor modules and JSON provenance.
2. **Energy gaps:** fixed-temperature separation and stream reconstruction break common enthalpy accounting. Do not infer whole-plant closure from compressor or heat-exchanger local residuals.
3. **Identity loss:** new Stream allocation and dynamic attributes can discard h/reference, phase, density and vapor fraction. `read_stream` ignores optional feed properties; `make_stream` does not generically preserve them. Unknown phase can pass compressor/pump declaration checks.
4. **Unit/basis mismatch:** legacy kmol/h, bar, kW, ordered z/MW/Cp arrays versus current kg/h, Pa, W and keyed component data. Do not transplant the fictitious MWs or confuse mole and mass fractions.
5. **Recycle qualification:** no proof of convergence for arbitrary graphs, automatic tears or failed-run history; one coupled example can conceal sensitivity. Accepted tolerance depends on component scale/tear count; add trace-component and ill-conditioned tests before reuse.
6. **Schema and model-capability drift:** PORTS/dispatcher duplication, loosely validated envelope, unknown metadata and different zero-flow validation paths. Some absent-flow adapters evaluate synthetic compositions to obtain T/P; do not present those states as physically observed material properties.
7. **Drawing divergence:** saved draw.io missing `treater_water` and carrying a duplicate boundary. Current generation and drawing edits must remain subordinate to the structured graph.
8. **Stale artifacts and partial writes:** runner writes files sequentially and leaves previous output on failure. Future results must be bound to immutable input/model/solver hashes.
9. **Test coverage:** active demo exercises nine types, but not a broad matrix of each model; pump/HX, standalone flash edge cases, zero-flow thermal variants and multiple independent recycle benchmarks are missing locally.
10. **Scope creep:** a 31-unit offshore-looking drawing can falsely imply a qualified facility simulator, relief design or TEG/water-treatment capability. None follows from this directory.

## 18. Recommended Milestone 4 — smallest conservative multi-equipment proof

**Recommend an acyclic splitter/mixer branch on the existing separator oil outlet.** This recommendation follows the generic, non-flashing material distribution in `L/engine/splitter.py::execute` and `mixer.py::execute`, and reuses the already qualified-for-development RioGineer separator/Cp basis rather than the legacy fixed-K model.

```text
SOURCE -> SEP-A --gas------------------------------> GAS sink
              |--water----------------------------> WATER sink
              |--oil--> SPLIT-A --branch A--+
                               --branch B--+--> MIX-A --> OIL sink
```

There are **three equipment objects, seven material streams and three internal streams** (separator-to-splitter and the two splitter-to-mixer branches). Branches are independent directed connections to separate mixer ports, not multiple consumers of one stream. This is a DAG with reconvergence, **not a recycle**. The split/rejoin is an intentionally small architecture demonstration, not a claim of necessary industrial processing equipment.

For a proposed synthetic acceptance case, retain the current reference separator unchanged; explicitly review a positive split such as 40%/60%. On the reference 77550 kg/h oil stream, branches would be 31020 and 46530 kg/h, recombining to 77550 kg/h. Those are proposed test expectations, not newly implemented or executed RioGineer results. Preserve component proportions, T/P and the same declared Cp/reference state; add explicit component, total mass and sensible-energy checks at each unit and externally. No phase prediction, density or latent heat is necessary. Keep feed/gas/oil/water totals and separator duty at the existing reference values.

Engineering stream numbers must come from the existing deterministic structured numbering policy for the new graph, never hard-coded as these seven display columns or derived from service names. Retain any existing assignments when extending a persisted graph; assert matching ID→number maps in PFD, Stream Table, results association and downloads through calculation/layout/regeneration. More than one stream may now have the same service name, so future contracts must separate that label from unique IDs and connection semantics.

Why not the suggested larger chain first? A second **legacy** separator introduces specified-K physics different from the current prescribed-recovery model; a compressor adds dry-phase/property assumptions; the two-sided HX exists but is unused and untested here and adds a second material side. A heater → second current prescribed-recovery separator could be a later acyclic extension after additional model-specific tests, but it is not needed to establish multi-unit graph execution. This audit does not authorize any of those implementations.

Why no initial recycle? The old algorithm is sufficiently generic to justify a **subsequent narrowly qualified recycle experiment**, but not necessary for this first topology gate. First prove stream identity, scheduling and balances in a DAG; then consider exactly one mixer/splitter feedback loop with an analytical geometric-series reference, independent guesses, nonconvergence tests and structured failure diagnostics. Do not import Flowsheet 03's five-tear system as the first integrated case.

Preserve the product workflow: **LLM interprets requirements → human reviews/approves → deterministic builder defines topology → engine calculates → PFD and Stream Table view the structured model**. A future approved milestone must extend capability declarations/contracts/review for the bounded new graph without weakening existing evidence anchoring or accepting arbitrary topology. Missing split fractions, model assumptions or boundary states must block approval rather than be defaulted silently.

## 19. Functionality that should not yet be migrated

- The full 31-unit network, five-tear solution and its assumed condensate routings.
- Specified-K flash as a replacement for the current separator or a supposed rigorous equilibrium model.
- EOS/VLLE/PH/PS functionality: it is absent here, not available to migrate.
- Compressor, pump and two-sided HX implementations before independent capability/test qualification.
- Treater physics, efficiency prediction or electrical power; only prescribed removal exists.
- Valve temperature carry-through as an isenthalpic throttling model.
- Demo MWs, Cps, K values, efficiencies, feed composition or distribution fractions as production defaults.
- Flare/relief sizing or hydraulics, level-controller dynamics, hydrocyclones, flotation or TEG equipment.
- Dynamic name-only stream objects, arbitrary property metadata and drawing index IDs.
- Tag-specific drawing geometry, implicit service-name heuristics, diagram-to-engine editing, or the inconsistent saved draw.io as a topology source.
- Whole-plant energy closure or phase-property availability claims not supported by a common model.

## 20. Proposed next implementation sequence and audit closure

These are proposed future gates, **not work performed by this audit**:

1. Approve the bounded acyclic milestone and explicit demonstration assumptions; freeze the existing Bia reference tests and current ID/number invariants.
2. Design versioned multi-equipment requirements, graph and results contracts with stable IDs, distinct service names, typed ports, model versions/capabilities, explicit unavailable properties and freshness hashes. Keep old reference compatibility deliberate.
3. Implement one deterministic DAG validator/scheduler from explicit owner/port connections, with canonical tie-breaking and clear duplicate, disconnected, invalid-port and cycle rejection. Unify capability/port registration.
4. Add only qualified proportional splitter and sensible mixer adapters on the current mass/Cp basis; retain the separator evaluator unchanged. Define zero-flow and pressure behavior explicitly and test material/energy propagation independently.
5. Build the seven-stream branch/rejoin fixture and analytical assertions; verify node-order/layout independence, service-name duplication without ID collision, unchanged numbers across calculation and stale-result rejection.
6. Extend PFD layout and Stream Table for arbitrary approved stream counts while keeping both read-only projections of the same model. Test all internal stream identities and result associations.
7. Extend review/capability interpretation only for the approved graph; preserve unique exact evidence anchors, missing-data blockers, human approval and deterministic validation. Use controlled interpretation fixtures before any separately authorized live run.
8. Run the full current validation suite plus new graph/model regressions. Qualify a single analytical recycle only in a subsequent explicit gate; develop EOS-based thermodynamics separately, after topology/stream architecture.

Audit closure: only `R/FLOWSHEET_03_ASSESSMENT.md` was created. No RioGineer source, contracts, engine or reference values were changed; no legacy files were modified/copied, no process outputs were written, no equipment was implemented and no live LLM/provider request was made. Verification consisted of static inspection, JSON/XML parsing, in-memory simulation/export and the read-only legacy checks described in section 15. This report does not claim implementation or physical validation of the recommended milestone.
