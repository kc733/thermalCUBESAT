# 2U CubeSat Thermal Model · Málaga Space Team

A local, interactive Python/Streamlit graphical interface for a **preliminary 11-node steady-state** thermal model of a 2U CubeSat.

The interface is intentionally simple: edit input parameters in the sidebar and examine **sunlight versus eclipse** temperatures, heat flows, and optional one-parameter sweeps. **MÁLAGA SPACE TEAM** appears in the lower-right corner of the app.

## Launching the graphical interface

**Python 3.10+ recommended.** Open a terminal in this folder and run:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Streamlit opens a browser tab on your local machine (normally `http://localhost:8501`). The thermal calculations run locally on your computer; the dashboard does not require an online backend.

On macOS/Linux you can alternatively run `bash launch_gui.sh`, or on Windows run `launch_gui.bat`, after installing Python.

## What you can change

- Orbital altitude, Sun direction, direct solar irradiance, Earth infrared flux, albedo
- Aluminum and PV solar absorptivity and infrared emissivity
- PV effective thermal resistance (unverified, default **2 K/W**), Al thickness
- Effective PV extraction efficiency (default 29%)
- Assumed constant internal heat input (default **1.5 W**)
- Optional extra equivalent coupling resistances to test idealized interior-boundary sensitivity

The default input values are **preliminary engineering assumptions**, not verified material specifications. Altering the 1.5 W internal load is a sensitivity experiment, not the agreed baseline case.

## Dashboard views

1. **Temperatures** — all 11 node temperatures, sunlight/eclipsed comparison, downloadable CSV.
2. **Heat balance** — absorbed solar, reflected Earth albedo, Earth IR, PV electrical extraction, internal heat, emitted infrared, geometry factors and per-node balances.
3. **Sensitivity** — one-parameter sweep comparing predicted internal temperatures under sunlight and eclipse.

Use the expandable **Model assumptions** section to download the current input parameters as JSON.

## Batch mode (without the GUI)

```bash
python main.py
python main.py --pv-resistance 5 --pv-efficiency 0.10 --sun-angle 0
python -m pytest tests -q
```

Batch mode saves `outputs/temperature_comparison.png`, `outputs/power_budget.png`, CSV results and a JSON summary.

## Included project structure

```text
CubeSat_Thermal_Model/
├── parameters.py       Geometry, material, environmental and power data
├── radiation.py        Sun incidence, Lambertian Earth albedo, Earth IR and emission
├── conduction.py       One-dimensional equivalent thermal resistances
├── thermal_balance.py  Ten surface equations + one interior balance
├── solver.py           Robust numerical root solve; residual check
├── scenarios.py        Sunlight and eclipse conditions
├── plots.py            Batch-mode plots
├── main.py             Batch-mode command line
├── app.py              Streamlit graphical user interface
├── requirements.txt    Python dependencies
├── .streamlit/          UI visual theme
├── tests/              Automated physics/energy checks
├── docs/               Uploaded thermal model reference
└── outputs/            Generated example results
```

## Model definition and sign convention

Four lateral faces have *separate* aluminum and PV exterior temperatures. Two end faces have aluminum exterior temperatures. All ten connect to one equivalent internal node, yielding **11 temperature unknowns**. Conduction is defined positive **from the interior toward the exterior**. The electronic heat input is **1.5 W constant in both cases**, representing the estimated *orbit-averaged* electrical consumption.

The face heat balance is:

$$
\dot Q_{\mathrm{solar},j}+\dot Q_{\mathrm{albedo},j}
+\dot Q_{\mathrm{IR},j}+\dot Q_{\mathrm{cond},j}
-P_{\mathrm{el},j}=\dot Q_{\mathrm{rad,out},j}.
$$

The internal balance is:

$$
\dot Q_{\mathrm{gen}}=\sum_j\dot Q_{\mathrm{cond},j}.
$$

With:

$$
\dot Q_{\mathrm{cond},j} = \frac{T_{\mathrm{int}}-T_{s,j}}{R_j},
\qquad \dot Q_{\mathrm{rad,out},j}=\varepsilon_j\sigma A_jT_{s,j}^4.
$$

The code implements the same **11 equations**, solved efficiently by eliminating the ten external temperatures for each trial interior temperature, then solving the final interior balance. It verifies every local balance and the global energy residual.

### Orbit geometry

- `+Y` is **nadir** (toward Earth); `-Y` is **zenith**.
- The Sun direction in the baseline sunlight case is `+X`.
- The adjustable Sun angle rotates within the X–Y plane; a nonzero angle changes the incidence and effective Earth albedo.
- Earth view factors are obtained by a numerical solid-angle integral over the visible Earth disk.
- Albedo uses a **uniform, Lambertian reflecting Earth approximation** with the sunlit Earth surface weighted by local solar incidence. This is more self-consistent than setting the albedo factor equal to the Earth view factor, but it is still not a high-fidelity orbital radiance model.
- The eclipse case forces direct solar irradiation, albedo and direct-solar PV extraction to zero, retaining Earth IR and the constant 1.5 W thermal load.

**Sunlight feasibility warning:** Certain Sun/nadir angle combinations correspond to the Sun being behind Earth. The GUI warns about these geometric cases; it does not model actual orbital eclipse entry/exit in sunlight mode.

### Major physical limitations

- The PV assemblies are placed in openings, with **no aluminum backing**. Their effective 1D conduction connection to the interior is a deliberately **idealized boundary condition**; the actual rear-side radiation, mechanical interfaces and lateral spreading are not modeled.
- Default PV resistance **2 K/W is illustrative** and must be replaced with a justified value or sensitivity range.
- The present model is **steady-state**, so calculated eclipse/sunlit equilibria are **not** actual temperature extremes during a finite orbit.
- The 1.5 W internal load is fixed at the estimated orbit-averaged consumption; real operating-mode peaks and low periods are not simulated.
- Nominal 29% PV extraction efficiency represents an **assumed actual electrical operating point**. It must not be interpreted as verified panel output under all electrical loads.
- Optical properties, panel dimensions, aluminum finish, thermal coupling, and actual attitude/orbit parameters need confirmation.

## Reference document

The uploaded report is copied into `docs/Thermal_Analysis_2U_CubeSat_Revised.md`. The program is an implementation of the agreed **simplified 11-node** equations and explicitly documented additional numerical approximations. See the report for the derivations and external references.
