# GreenOps Refactor — Complete Technical & Faculty Documentation

This document explains **what each part of the project does**, **why design choices were made**, and **the formulas and parameters** implemented in code. Use it for viva preparation alongside `README.md`.

---

## 1. Project goal (one paragraph)

**GreenOps Refactor** is a web application that takes Python source code, extracts **static** energy-relevant features, predicts **estimated runtime energy** (kWh) with a **machine-learned regressor**, combines that with **grid carbon intensity** (Electricity Maps API for zone `IN-WE` by default), and computes a **Green Score (0–100)** plus **CO₂e footprint**. Optional **Ollama** calls provide AI suggestions and refactored code. Nothing measures actual CPU power on the user’s machine during analysis; energy is a **model-based estimate** from syntax and training data.

---

## 2. End-to-end pipeline (conceptual)

```
Source code
    → feature_extractor.py (libcst + ast) → feature vectors
    → training_model1.py (loaded .pkl)   → raw predicted kWh (expm1 of log target)
    → structural scaling                  → adjusted “effective” kWh for display
    → context_integrator.py               → PUE × hardware factor, carbon API, Green Score
    → app.py + templates                  → HTTP UI / JSON API
```

---

## 3. File-by-file responsibilities

| File | Role |
|------|------|
| **`app.py`** | Flask app: `/`, `/analyze`, `/api/analyze`, `/api/optimize`, `/health`. Orchestrates `extract_features` → `predict_energy` / fallback → `build_context_report`. Ollama helpers for suggestions and optimized code. Loads `.env` with `load_dotenv(override=True)` and strips `ELECTRICITY_MAPS_API_KEY`. |
| **`feature_extractor.py`** | Parses Python with **libcst** (fallback: **ast**). Counts loops, nesting, I/O, recursion flags, NumPy/Pandas usage, etc. Exposes `CodeFeatures` and `to_model_features()` which feeds the regressor (logical LOC excludes comments and docstring lines from the LOC used for ML). |
| **`training_model1.py`** | Builds or loads `training_data.csv`, preprocesses (outliers, `log1p` target), trains **multiple candidate regressors**, selects best by **5-fold CV R²** on the training split (with **simplicity tie-break**). Saves `energy_predictor.pkl`, `feature_columns.json`, `model_metrics.json`. Implements `predict_energy()` and `apply_structural_energy_scale()`. |
| **`context_integrator.py`** | Fetches **carbon intensity** (Electricity Maps API + cache + Maharashtra fallback), **hardware** detection and TDP, **PUE**, **structural_load_factor**, **Green Score** math (`calculate_green_score`), **carbon footprint** in grams CO₂e, formatting helpers. |
| **`benchmark.py`** | (If used) Generates workloads and can integrate with CodeCarbon-style measurements to build `training_data.csv` — ties **measured** energy to **static** features for supervised learning. |
| **`templates/index.html`** | Landing page and analysis form (`POST /analyze`). |
| **`templates/result.html`** | Results: score, metrics, AI section, optimize button, client-side chips for score/energy after `/api/optimize`. |
| **`.env` / `.env.example`** | API keys, `OLLAMA_*`, `ELECTRICITY_MAPS_*`, optional `GREENOPS_OLLAMA_AVG_POWER_WATTS`. |
| **`model_metrics.json`** | Produced by training: selected model name, R², CV R², feature importances, `structural_burden_norm`, etc. |
| **`energy_predictor.pkl`** | Serialized sklearn (or pipeline) model predicting `log1p(energy_kwh)`. |
| **`Dockerfile` / `docker-compose.yml`** | Containerized deployment (app + optional Ollama). |

---

## 4. Features used by the energy model (14 columns)

Defined in `training_model1.py` as `FEATURE_COLS`:

`loc`, `blank_lines`, `comment_lines`, `num_functions`, `num_classes`, `num_loops`, `nested_loops`, `list_comprehensions`, `num_imports`, `try_except_blocks`, `has_recursion`, `io_operations`, `uses_numpy`, `uses_pandas`.

**Inference note (`feature_extractor.py` → `to_model_features`):**

- **`loc`** for the model is **logical LOC**:  
  \(\text{logical\_loc} = \max(1,\; \text{loc} - \text{comment\_lines} - \text{docstring\_lines})\)  
  **Reason:** Comments and docstrings inflate line count but add negligible runtime cost; excluding them avoids penalizing documented code.

---

## 5. Energy prediction — training mathematics

### 5.1 Target transformation

- Raw target in CSV: **`energy_kwh`** (or mapped from `energy_consumed`, etc., in `preprocess()`).
- Training uses **`log_energy = log1p(energy_kwh)`** so the regressor fits in log-space (stabilizes variance across orders of magnitude).
- Predictions convert back with **`expm1`**:  
  \(\hat{E}_{\text{raw}} = \exp(\hat{y}_{\log}) - 1\)

### 5.2 Candidate models (not fixed to XGBoost)

`training_model1.py` evaluates several sklearn / XGBoost models (see `_candidate_models()`), including:

- XGBoost regressor  
- `LinearRegression`  
- `RidgeCV` (with `StandardScaler` pipeline)  
- `HistGradientBoosting`, `GradientBoosting`, `RandomForest`, `ExtraTrees`

**Selection rule:**

1. 5-fold **cross_val_score** on **training split only** (targets leakage) → mean CV R² per model.  
2. Sort by **highest CV R² mean**, then by **lower complexity** (`_MODEL_COMPLEXITY_RANK`) to break ties (prefer simpler models when scores are close).  
3. `_assess_fit()` labels generalization (`balanced`, `likely_overfit`, etc.). If diagnosis is **`likely_overfit`**, the code may **swap to a simpler** candidate that reduces train–test gap.

**Why this matters for viva:** The “best” model is **data-driven**, not a fixed brand name. On a typical run, **`model_metrics.json`** may show **`LinearRegression`** selected because it had the best CV performance on that dataset (see current `selected_model` field).

### 5.3 Structural energy scaling (after ML prediction)

Raw model output is scaled so **static structure** (loops, I/O, NumPy, etc.) adjusts effective kWh in a way that aligns with the Green Score’s structure component:

1. **`structural_load_factor(features)`** in `context_integrator.py` returns a multiplier \(m \in [0.28,\, 5.0]\) based on nested loops, loop count, I/O burden, recursion, comprehensions, NumPy/Pandas.

2. **`structural_burden_norm`** = mean load factor over training rows (saved in `model_metrics.json`, often capped at `5.0` in metadata).

3. **Final predicted kWh** (`training_model1.apply_structural_energy_scale`):

\[
E_{\text{eff}} = \max\left(\frac{E_{\text{raw}} \cdot m}{\text{norm}},\, 10^{-12}\right)
\]

where `norm` = `structural_burden_norm` from metrics (fallback 1.0 if missing).

**Reason:** The regressor alone maps features → energy; the load factor ties **visible complexity** to **effective** energy so refactors that reduce nesting/I/O move energy and score coherently.

### 5.4 Fallback when model is unusable

In `app.py`, if the model is missing or **`r2 ≤ 0`** in `model_metrics.json`, energy uses a **heuristic** `_fallback_energy()` (linear mix of LOC, loops, nesting) then the same structural scaling.

---

## 6. Context integration — PUE, hardware, carbon

### 6.1 Adjusted energy before Green Score

\[
E_{\text{adj}} = E_{\text{eff}} \times \text{PUE}(\text{deployment\_env}) \times \text{hw\_multiplier}(\text{hardware})
\]

- **`PUE`**: e.g. `local` → 1.6, `cloud` → 1.2 (`context_integrator.PUE`).  
- **`hw_multiplier`**: e.g. `apple_m` → 0.40, `graviton` → 0.60, `x86` → 1.00.

**Reason:** Data-center overhead (PUE) and chip efficiency are **multiplicative proxies** for operational electricity; they are **not** measured live in this project.

### 6.2 Carbon footprint

- **`ci`** = carbon intensity in **gCO₂e per kWh** (from API or fallback **820** g/kWh for Maharashtra grid when API fails).  
- **Mass CO₂e (grams):**

\[
\text{CO}_2\text{e (g)} = E_{\text{adj}} \times ci
\]

(Display may show mg/µg for very small values — see `format_carbon()`.)

### 6.3 Electricity Maps API

- Endpoint: `GET https://api.electricitymap.org/v3/carbon-intensity/latest?zone=<ZONE>`  
- Auth: header **`auth-token`**, with **Bearer** retry on 401/403.  
- Zone default **`IN-WE`**; override with **`ELECTRICITY_MAPS_ZONE`** in `.env`.  
- In-memory cache **10 minutes**.  
- **`carbon_is_stale`** in UI is `True` only when source is **`fallback_maharashtra_grid`**.

---

## 7. Green Score — complete breakdown (matches README lines 147–150)

Total score \(G \in [0,100]\):

\[
G = s_{\text{energy}} + s_{\text{structure}} + s_{\text{CI}} + s_{\text{quality}}
\]

All implemented in `context_integrator.calculate_green_score()`.

### 7.1 Energy score — max **40** points

Uses **`_energy_score_continuous(E_adj)`**: maps **adjusted kWh** to 0–40 using **piecewise linear interpolation in log₁₀(energy)** between anchors:

| Upper bound of energy (kWh) | Points at/below |
|----------------------------:|----------------:|
| 1e-8 | 40 |
| 1e-6 | 35 |
| 1e-5 | 30 |
| 1e-4 | 20 |
| 1e-3 | 10 |
| 1e-2 | 2 |

Below the lowest anchor, score is 40; above the highest band, score approaches 2.

**Reason:** Energy spans many orders of magnitude; **log spacing** avoids cliff effects and matches “lower energy → higher score” monotonically.

### 7.2 Structure score — max **30** points

Starts at **30**, then:

| Rule | Effect |
|------|--------|
| Nested loops | \(-\min(4 \times \text{nested\_loops},\, 12)\) |
| Many loops | \(-\min(\max(\text{num\_loops}-2,0),\, 8)\) |
| List comprehensions | \(+\min(2 \times \text{list\_comprehensions},\, 6)\) |
| Recursion flag | \(-5\) |
| NumPy used | \(+3\) |
| Pandas used | \(+2\) |

Clamped to **[0, 30]**.

**Reason:** Rewards **vectorization** and **shallower** control flow; penalizes **nested** and **recursive** patterns that often imply more CPU work.

### 7.3 Carbon intensity score — max **20** points

Depends only on **grid gCO₂/kWh** (location-based operational emissions proxy):

| Carbon intensity (gCO₂/kWh) | Points |
|----------------------------:|-------:|
| ≤ 200 | 20 |
| ≤ 400 | 15 |
| ≤ 600 | 10 |
| ≤ 820 | 5 |
| > 820 | 2 |

**Reason:** Same code on a **cleaner grid** gets a higher sub-score; coal-heavy regions (e.g. Maharashtra) cap this component unless intensity drops.

### 7.4 Quality score — max **10** points

Starts at **4.25**, then adjusts with try/except blocks, comprehensions, nesting, recursion, and I/O counts (see code for exact coefficients). Clamped to **[0, 10]**.

**Reason:** Small nudge toward **defensive** code (try/except) and away from **chatty I/O** in static analysis, without dominating the score.

---

## 8. AI layer (Ollama)

- **`get_ai_suggestions`**: JSON-oriented prompt; parses model output for main suggestion, quick wins, pattern name.  
- **`get_optimized_code`**: Single refactor pass; output re-analyzed with `run_energy_report_for_code`.  
- **`/api/optimize`**: Returns new score/energy displays; handles “same AST” and “score unchanged” cases for UX.  
- Optional **inference timing / energy** from Ollama API responses is implemented for transparency; **Green Score** remains based on **static ML + grid**, not LLM power.

---

## 9. Metrics you may be asked about (from `model_metrics.json`)

Example values from a project run (yours may differ after retraining):

| Metric | Example | How to explain |
|--------|---------|----------------|
| **`selected_model`** | `LinearRegression` | Best performer in 5-fold CV (R² ~0.997). |
| **`r2` / `r2_test`** | 0.9994 | Hold-out \(R^2\) on log-target pipeline evaluated in kWh. |
| **`cv_r2_mean`** | 0.9976 | 5-fold CV on full data for reporting. |
| **`generalization_gap`** | 0.0005 | Train vs test gap; extremely small, indicating a very stable fit. |
| **`fit_diagnosis`** | `balanced` | From `_assess_fit()`. |

**If asked “Is 0.99 R² overfitting?”**

- Overfitting usually shows **high train, much lower test/CV**. Here **CV and test are both high** and **gap is small** → strong fit **on the benchmark distribution**.  
- Honest caveat: generalization to **arbitrary production code** is limited by **domain shift** (real workloads vs training generator); recommend **profiling** or **measurement** as future work.

---

## 10. Configuration reference (examination checklist)

| Variable | Purpose |
|----------|---------|
| `ELECTRICITY_MAPS_API_KEY` | Live carbon data; stripped of BOM/whitespace in code. |
| `ELECTRICITY_MAPS_ZONE` | Grid zone (default `IN-WE`). |
| `OLLAMA_BASE_URL`, `OLLAMA_MODEL` | Local LLM for suggestions/refactor. |
| `GREENOPS_OLLAMA_AVG_POWER_WATTS` | Optional measured watts for inference energy estimates. |
| `DEBUG`, `SECRET_KEY` | Flask. |

---

## 11. Quick “viva” question bank (short answers)

1. **Why static features instead of measuring power?**  
   *Instant feedback without instrumentation; trade-off is approximation error.*

2. **Why log1p on energy?**  
   *Stabilizes regression across small kWh values and heavy-tailed noise.*

3. **Why four Green Score components?**  
   *Separates **estimated energy**, **code shape**, **grid carbon**, and **quality/I/O** so no single proxy dominates by accident.*

4. **Why Electricity Maps?**  
   *Location-based grid intensity aligns with common Scope 2 / SCI-style reporting at regional granularity.*

5. **What validates the model?**  
   *Train/test split, CV, `fit_diagnosis`, and saved `model_metrics.json`; optional real CodeCarbon runs via `benchmark.py`.*

---

## 12. How to regenerate artifacts before a demo

```bash
python benchmark.py          # optional: build training_data.csv
python training_model1.py    # retrains, writes pkl + model_metrics.json
python app.py
```

Always show **`model_metrics.json` → `selected_model`** and **`r2`** during evaluation so claims match files.

---

*Document generated to mirror the implementation in this repository. If code changes, update the corresponding section or regenerate metrics after training.*
