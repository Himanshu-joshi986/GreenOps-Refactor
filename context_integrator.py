"""
GreenOps Refactor — context_integrator.py
Fetches grid carbon intensity (Home Assistant sensors when configured, else optional
legacy HTTP carbon API, else regional fallback) and integrates hardware context
with energy predictions.
"""

import os
import math
import re
import time
import logging
import platform
import requests
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
from typing import Optional
from urllib.parse import quote

log = logging.getLogger("context_integrator")

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────
ELECTRICITY_MAPS_ZONE = "IN-WE"  # Maharashtra, India — legacy API zone code only
ELECTRICITY_MAPS_URL = "https://api.electricitymap.org/v3/carbon-intensity/latest"
ELECTRICITY_MAPS_FREE_URL = "https://api.electricitymap.org/v3/carbon-intensity/latest"

# Fallback carbon intensity (gCO₂/kWh) for Maharashtra grid
# Based on 2023 CEA data: ~820 gCO₂eq/kWh (coal-heavy grid)
FALLBACK_CARBON_INTENSITY_G_PER_KWH = 820.0

# Hardware TDP estimates (watts)
HARDWARE_TDP = {
    "x86":      95.0,   # Intel/AMD typical server
    "graviton": 60.0,   # AWS Graviton2/3 typical
    "apple_m":  30.0,   # Apple M-series
    "arm":      45.0,   # Generic ARM
    "unknown":  80.0,
}

# PUE (Power Usage Effectiveness) estimates
PUE = {
    "local": 1.6,       # Typical on-prem
    "cloud": 1.2,       # Modern cloud DC
    "home":  2.0,       # Home server
}


# ─────────────────────────────────────────────
# Result dataclass
# ─────────────────────────────────────────────
@dataclass
class CarbonMetrics:
    """Live / fallback grid carbon numbers used by the context report."""
    intensity_g_per_kwh: float
    source: str
    fossil_fuel_percent: Optional[float] = None
    observed_at: Optional[str] = None


@dataclass
class ContextReport:
    # Carbon
    carbon_intensity_g_per_kwh: float = FALLBACK_CARBON_INTENSITY_G_PER_KWH
    carbon_source: str = "fallback"
    carbon_zone: str = "Maharashtra grid"
    carbon_timestamp: Optional[str] = None
    carbon_is_stale: bool = True
    grid_fossil_fuel_percent: Optional[float] = None

    # Hardware
    hardware_type: str = "x86"
    hardware_tdp_w: float = 95.0
    pue: float = 1.6

    # Adjusted energy & emissions
    raw_energy_kwh: float = 0.0
    adjusted_energy_kwh: float = 0.0
    carbon_footprint_g: float = 0.0
    carbon_footprint_kg: float = 0.0

    # Green Score
    green_score: float = 0.0
    score_breakdown: dict = field(default_factory=dict)

    # Context
    deployment_env: str = "local"
    analysis_timestamp: str = ""

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


# ─────────────────────────────────────────────
# Carbon fetcher
# ─────────────────────────────────────────────
_carbon_metrics_cache: dict[str, tuple[CarbonMetrics, float]] = {}
_cache_ttl_s = 600  # 10 minutes


def _normalize_api_key(raw: Optional[str]) -> str:
    """Strip BOM/CRLF/quotes — common reasons a valid key fails in .env on Windows."""
    if not raw:
        return ""
    s = str(raw).strip().replace("\r", "").strip().lstrip("\ufeff").strip()
    if len(s) >= 2 and ((s[0] == s[-1] == '"') or (s[0] == s[-1] == "'")):
        s = s[1:-1].strip()
    return s


def em_zone_code_from_env() -> str:
    """Zone code for the optional legacy carbon HTTP API (not shown in UI)."""
    z = os.getenv("ELECTRICITY_MAPS_ZONE", ELECTRICITY_MAPS_ZONE)
    z = (z or ELECTRICITY_MAPS_ZONE).strip()
    return z or ELECTRICITY_MAPS_ZONE


def carbon_zone_from_env() -> str:
    """Display label for grid / region in UI (backwards-compatible name)."""
    return display_grid_region_label()


def display_grid_region_label() -> str:
    """
    Human-readable grid label for reports and templates.
    """
    custom = os.getenv("GREENOPS_GRID_LABEL", "").strip()
    if custom:
        return custom
        
    # If Home Assistant is working, we can use its location or a generic label
    if _home_assistant_configured():
        # You could dynamically fetch the HA location name here if needed
        return "Maharashtra grid (Live HA)"
        
    return "Maharashtra grid (Fallback)"


def _strip_base_url(raw: str) -> str:
    if not raw:
        return ""
    s = str(raw).strip().rstrip("/")
    return s


def _home_assistant_configured() -> bool:
    base = _strip_base_url(os.getenv("HOME_ASSISTANT_URL", ""))
    token = _normalize_api_key(os.getenv("HOME_ASSISTANT_TOKEN", ""))
    entity = os.getenv("HOME_ASSISTANT_CO2_SENSOR", "").strip()
    return bool(base and token and entity)


def _parse_numeric_sensor_state(state_raw: object) -> Optional[float]:
    """Parse Home Assistant state string into a float (handles '724', '88.26 %', etc.)."""
    if state_raw is None:
        return None
    s = str(state_raw).strip()
    if not s or s.lower() in ("unknown", "unavailable", "none"):
        return None
    try:
        return float(s)
    except (TypeError, ValueError):
        pass
    m = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", s.replace(",", ""))
    if m:
        try:
            return float(m.group(0))
        except ValueError:
            return None
    return None


def _fetch_home_assistant_state(base: str, entity_id: str, token: str) -> Optional[dict]:
    """GET /api/states/<entity_id>. Returns JSON dict or None."""
    eid = entity_id.strip()
    if not eid:
        return None
    url = f"{base}/api/states/{quote(eid, safe=':')}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "GreenOpsRefactor/1.0",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=8)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as ex:
        log.warning(f"Home Assistant: connection failed at {base} ({ex})")
        return None
        
    if resp.status_code == 401:
        log.warning("Home Assistant: Unauthorized (401). Check your HOME_ASSISTANT_TOKEN in .env")
        return None
    elif resp.status_code == 404:
        log.warning(f"Home Assistant: Entity '{eid}' not found (404). Check your entity ID.")
        return None
    elif resp.status_code != 200:
        log.warning(f"Home Assistant: HTTP {resp.status_code} for {eid}")
        return None
        
    try:
        return resp.json()
    except ValueError:
        log.warning(f"Home Assistant: Invalid JSON response for {eid}")
        return None


def _home_assistant_fetch_live() -> Optional[CarbonMetrics]:
    """Read CO₂ intensity (and optional fossil %) from Home Assistant sensor entities (no cache)."""
    base = _strip_base_url(os.getenv("HOME_ASSISTANT_URL", ""))
    token = _normalize_api_key(os.getenv("HOME_ASSISTANT_TOKEN", ""))
    co2_entity = os.getenv("HOME_ASSISTANT_CO2_SENSOR", "").strip()
    fossil_entity = os.getenv("HOME_ASSISTANT_FOSSIL_SENSOR", "").strip()
    if not base or not token or not co2_entity:
        return None

    co2_payload = _fetch_home_assistant_state(base, co2_entity, token)
    if not co2_payload:
        return None
    ci = _parse_numeric_sensor_state(co2_payload.get("state"))
    if ci is None or ci < 0:
        log.warning("Home Assistant: no usable CO₂ value from %s", co2_entity)
        return None

    observed = co2_payload.get("last_changed") or co2_payload.get("last_updated")

    fossil_pct: Optional[float] = None
    if fossil_entity:
        fp = _fetch_home_assistant_state(base, fossil_entity, token)
        if fp:
            fossil_pct = _parse_numeric_sensor_state(fp.get("state"))

    log.info(
        "Carbon intensity (Home Assistant): %.1f gCO₂/kWh [%s]",
        ci,
        co2_entity,
    )
    return CarbonMetrics(
        intensity_g_per_kwh=ci,
        source="home_assistant_live",
        fossil_fuel_percent=fossil_pct,
        observed_at=str(observed) if observed else None,
    )


def _ha_cache_key() -> str:
    co2 = os.getenv("HOME_ASSISTANT_CO2_SENSOR", "").strip()
    fos = os.getenv("HOME_ASSISTANT_FOSSIL_SENSOR", "").strip()
    return f"ha:{co2}:{fos or '-'}"


def _parse_carbon_intensity(data: object) -> Optional[float]:
    """Extract gCO₂/kWh from legacy grid HTTP API JSON (handles minor schema variants)."""
    if isinstance(data, list) and data:
        data = data[0]
    if not isinstance(data, dict):
        return None
    for k in ("carbonIntensity", "carbon_intensity", "intensity"):
        v = data.get(k)
        if v is not None and v != "":
            try:
                return float(v)
            except (TypeError, ValueError):
                continue
    nested = data.get("data")
    if isinstance(nested, dict):
        return _parse_carbon_intensity(nested)
    return None


def _request_legacy_http_carbon_intensity(zone: str, headers: dict) -> tuple[Optional[float], int, str]:
    """
    One HTTP GET. Returns (parsed intensity or None, status_code, response_text_prefix for logs).
    """
    req_headers = {
        "User-Agent": "GreenOpsRefactor/1.0 (https://github.com/green-software)",
        **headers,
    }
    resp = requests.get(
        ELECTRICITY_MAPS_URL,
        params={"zone": zone},
        headers=req_headers,
        timeout=12,
    )
    preview = (resp.text or "")[:200]
    if resp.status_code != 200:
        return None, resp.status_code, preview
    try:
        payload = resp.json()
    except ValueError:
        log.warning("Grid carbon HTTP API: response was not JSON (status 200): %s", preview)
        return None, resp.status_code, preview
    ci = _parse_carbon_intensity(payload)
    return ci, resp.status_code, preview


def fetch_carbon_metrics(
    api_key: Optional[str] = None,
    zone: Optional[str] = None,
) -> CarbonMetrics:
    """
    Resolve grid carbon intensity: Home Assistant sensors (if configured), else optional
    legacy grid HTTP API when ``ELECTRICITY_MAPS_API_KEY`` is set, else Maharashtra fallback.

    ``zone`` applies only to the legacy HTTP API path (defaults from ``ELECTRICITY_MAPS_ZONE``).
    """
    now = time.time()
    z = (zone or em_zone_code_from_env()).strip() or ELECTRICITY_MAPS_ZONE

    # 1) Home Assistant (preferred when URL + token + CO₂ entity are set)
    if _home_assistant_configured():
        ck = _ha_cache_key()
        if ck in _carbon_metrics_cache:
            cached_m, cached_time = _carbon_metrics_cache[ck]
            if now - cached_time < _cache_ttl_s:
                return CarbonMetrics(
                    intensity_g_per_kwh=cached_m.intensity_g_per_kwh,
                    source="home_assistant_cached",
                    fossil_fuel_percent=cached_m.fossil_fuel_percent,
                    observed_at=cached_m.observed_at,
                )
        live = _home_assistant_fetch_live()
        if live is not None:
            _carbon_metrics_cache[ck] = (live, now)
            return live
        log.warning(
            "Home Assistant failed (check logs above). Falling back to Maharashtra grid data..."
        )

    # 2) Legacy grid HTTP API (optional)
    em_key = f"em:{z}"
    if em_key in _carbon_metrics_cache:
        em_m, em_t = _carbon_metrics_cache[em_key]
        if now - em_t < _cache_ttl_s:
            log.info(
                "Carbon intensity (grid API cached): %.1f gCO₂/kWh [%s]",
                em_m.intensity_g_per_kwh,
                z,
            )
            return CarbonMetrics(
                intensity_g_per_kwh=em_m.intensity_g_per_kwh,
                source="grid_http_cached",
                fossil_fuel_percent=em_m.fossil_fuel_percent,
                observed_at=em_m.observed_at,
            )

    key = _normalize_api_key(api_key or os.getenv("ELECTRICITY_MAPS_API_KEY", ""))
    if not key:
        log.warning("No grid carbon source available — using Maharashtra fallback (820 gCO₂/kWh)")
        return CarbonMetrics(
            FALLBACK_CARBON_INTENSITY_G_PER_KWH,
            "fallback_maharashtra_grid",
        )

    try:
        ci, status, preview = _request_legacy_http_carbon_intensity(z, {"auth-token": key})
        if ci is not None:
            m = CarbonMetrics(ci, "grid_http_live")
            _carbon_metrics_cache[em_key] = (m, now)
            log.info(f"Carbon intensity (grid HTTP): {ci:.1f} gCO₂/kWh [{z}]")
            return m

        if status == 200:
            log.warning(
                "Grid carbon HTTP API: 200 OK but no parsable intensity for zone %s — %s",
                z,
                preview[:160],
            )
        elif status in (401, 403):
            log.info("Grid carbon HTTP API: retrying with Authorization: Bearer …")
            ci2, status2, preview2 = _request_legacy_http_carbon_intensity(
                z, {"Authorization": f"Bearer {key}"}
            )
            if ci2 is not None:
                m = CarbonMetrics(ci2, "grid_http_live")
                _carbon_metrics_cache[em_key] = (m, now)
                log.info(f"Carbon intensity (grid HTTP, Bearer): {ci2:.1f} gCO₂/kWh [{z}]")
                return m
            log.warning(
                "Grid carbon HTTP API: auth failed (%s / %s) — verify ELECTRICITY_MAPS_API_KEY in .env",
                status,
                status2,
            )
            if preview2:
                log.warning("Grid carbon HTTP API (Bearer) response: %s", preview2[:200])
        elif status == 429:
            log.warning("Grid carbon HTTP API: rate limited, using fallback")
        elif status == 204:
            log.warning("Grid carbon HTTP API: 204 No Content for zone %s, using fallback", z)
        else:
            log.warning(
                "Grid carbon HTTP API: HTTP %s for zone %s — using fallback. Body: %s",
                status,
                z,
                preview[:200],
            )

    except requests.exceptions.Timeout:
        log.warning("Grid carbon HTTP API: timeout, using fallback")
    except requests.exceptions.ConnectionError:
        log.warning("Grid carbon HTTP API: connection error, using fallback")
    except Exception as e:
        log.warning("Grid carbon HTTP API: unexpected error (%s), using fallback", e)

    return CarbonMetrics(FALLBACK_CARBON_INTENSITY_G_PER_KWH, "fallback_maharashtra_grid")


def fetch_carbon_intensity(api_key: Optional[str] = None, zone: Optional[str] = None) -> tuple[float, str]:
    """Returns (gCO₂/kWh, source id). Prefer :func:`fetch_carbon_metrics` for fossil % and timestamps."""
    m = fetch_carbon_metrics(api_key=api_key, zone=zone)
    return m.intensity_g_per_kwh, m.source


# ─────────────────────────────────────────────
# Hardware detector
# ─────────────────────────────────────────────
def detect_hardware() -> tuple[str, float]:
    """
    Detect current hardware type and return (type_str, tdp_watts).
    """
    cpu_info = platform.processor().lower()
    machine = platform.machine().lower()

    if "graviton" in cpu_info or ("aarch64" in machine and "aws" in cpu_info):
        return "graviton", HARDWARE_TDP["graviton"]
    elif "apple" in cpu_info or "arm" in cpu_info and platform.system() == "Darwin":
        return "apple_m", HARDWARE_TDP["apple_m"]
    elif "aarch64" in machine or "arm" in machine:
        return "arm", HARDWARE_TDP["arm"]
    elif "intel" in cpu_info or "amd" in cpu_info or "x86" in machine:
        return "x86", HARDWARE_TDP["x86"]
    else:
        return "x86", HARDWARE_TDP["x86"]


# ─────────────────────────────────────────────
# Green Score calculator
# ─────────────────────────────────────────────
def structural_load_factor(code_features: dict) -> float:
    """
    Dimensionless multiplier derived only from static features (no score targets).
    Higher → more estimated operational burden (nesting, loops, I/O, recursion);
    lower when list comprehensions or NumPy/Pandas suggest less scalar work.

    Used to scale regressor kWh so that when structure improves, effective energy
    and carbon move in the same direction as the Green Score's energy component.
    """
    nested = float(code_features.get("nested_loops", 0) or 0)
    loops = float(code_features.get("num_loops", 0) or 0)
    io_ops = float(code_features.get("io_operations", 0) or 0)
    comps = float(code_features.get("list_comprehensions", 0) or 0)

    # Static I/O call count is per source occurrence; scale by nesting/loops for likely dynamic cost.
    io_burden = io_ops * (1.0 + 0.52 * nested + 0.18 * max(0.0, loops - 1.0))

    m = 1.0
    m += 0.11 * nested
    m += 0.038 * max(0.0, loops - 1.0)
    m += 0.055 * max(0.0, io_burden - 0.25)
    if int(code_features.get("has_recursion", 0) or 0):
        m += 0.09
    m -= min(0.055 * comps, 0.32)
    if int(code_features.get("uses_numpy", 0) or 0):
        m *= 0.86
    if int(code_features.get("uses_pandas", 0) or 0):
        m *= 0.90

    return float(max(0.28, min(m, 5.0)))


def _energy_score_continuous(energy_kwh: float) -> float:
    """
    Map adjusted energy (kWh) to 0–40 points, monotonic in log-space.
    Uses the same anchor energies as the legacy step function, but linear in log10
    between anchors so small prediction changes do not sit on artificial cliffs.
    """
    e = max(float(energy_kwh), 1e-16)
    le = math.log10(e)
    # (energy_kwh, score_at_or_below) — upper band starts at each energy
    anchors = (
        (1e-8, 40.0),
        (1e-6, 35.0),
        (1e-5, 30.0),
        (1e-4, 20.0),
        (1e-3, 10.0),
        (1e-2, 2.0),
    )
    if e <= anchors[0][0]:
        return anchors[0][1]
    for i in range(len(anchors) - 1):
        e0, s0 = anchors[i]
        e1, s1 = anchors[i + 1]
        le0, le1 = math.log10(e0), math.log10(e1)
        if e <= e1:
            t = (le - le0) / (le1 - le0) if le1 > le0 else 0.0
            return s0 + t * (s1 - s0)
    return anchors[-1][1]


def calculate_green_score(
    energy_kwh: float,
    code_features: dict,
    carbon_intensity: float,
    baseline_energy_kwh: float = None,   # ← NEW PARAMETER
) -> tuple[float, dict]:
    """
    Calculate Green Score (0–100).
    
    KEY FIX: Uses smooth log-scale for energy scoring so any energy
    reduction always produces a score increase. No more step-function
    buckets that can cause flat or reversed scores.
    
    If baseline_energy_kwh is provided (comparative mode), the energy
    score reflects improvement over baseline rather than absolute value.
    """
    import math
    breakdown = {}

    # ── 1. Energy Score (0–40 pts) ──
    # Use smooth log scale: score = 40 * (1 - clamp(log10(E/E_ref) / range, 0, 1))
    # E_ref = 1e-8 kWh (reference "perfect" energy for a small function)
    # range = 5 orders of magnitude (1e-8 to 1e-3)
    E_MIN = 1e-9   # effectively 0 energy = 40 pts
    E_REF = 1e-8   # reference minimum (perfect score)
    E_MAX = 5e-3   # worst case

    if baseline_energy_kwh is not None and baseline_energy_kwh > 0:
        # COMPARATIVE MODE: score reflects % improvement vs original
        ratio = baseline_energy_kwh / max(energy_kwh, 1e-12)
        if ratio >= 1.0:
            # Optimized is better — reward proportionally
            # log2(2) = 1 → 2x better → +10 pts bonus over baseline midpoint
            improvement_bonus = min(math.log2(ratio) * 8.0, 40.0)
            energy_score = min(20.0 + improvement_bonus, 40.0)
        else:
            # Optimized is worse — penalize (but gently, model noise)
            penalty = min(math.log2(1 / ratio) * 5.0, 15.0)
            energy_score = max(20.0 - penalty, 0.0)
    else:
        # ABSOLUTE MODE: smooth log scale
        e = max(energy_kwh, E_MIN)
        if e <= E_REF:
            energy_score = 40.0
        else:
            log_pos = math.log10(e / E_REF)         # 0 at E_REF, 5 at E_MAX
            log_range = math.log10(E_MAX / E_REF)   # ~5.7
            energy_score = 40.0 * max(0.0, 1.0 - log_pos / log_range)

    breakdown["energy_score"] = round(energy_score, 1)

    # ── 2. Code Structure Score (0–30 pts) ──
    structure_score = 30.0
    nested  = code_features.get("nested_loops", 0)
    loops   = code_features.get("num_loops", 0)
    comps   = code_features.get("list_comprehensions", 0)
    gen_exp = code_features.get("generator_expressions", 0)

    # Penalties
    structure_score -= min(nested * 5.0, 15.0)      # nested loops: -5 each, max -15
    structure_score -= min(max(loops - 2, 0) * 1.0, 8.0)  # excess loops: -1 each

    # Bonuses
    structure_score += min(comps * 2.5, 8.0)         # list comps: +2.5 each
    structure_score += min(gen_exp * 1.5, 5.0)        # generators: +1.5 each

    if code_features.get("has_recursion", 0):
        structure_score -= 6.0
    if code_features.get("uses_numpy", 0):
        structure_score += 5.0                        # vectorization bonus
    if code_features.get("uses_pandas", 0):
        structure_score += 2.0

    structure_score = max(0.0, min(30.0, structure_score))
    breakdown["structure_score"] = round(structure_score, 1)

    # ── 3. Carbon Intensity Score (0–20 pts) ──
    # Smooth: full 20 at 0 g/kWh, 0 at 1000 g/kWh
    ci_score = 20.0 * max(0.0, 1.0 - carbon_intensity / 1000.0)
    breakdown["carbon_intensity_score"] = round(ci_score, 1)

    # ── 4. Code Quality Score (0–10 pts) ──
    quality_score = 8.0   # start generous
    try_blocks = code_features.get("try_except_blocks", 0)
    io_ops     = code_features.get("io_operations", 0)
    quality_score += min(try_blocks * 0.5, 2.0)
    quality_score -= min(max(io_ops - 3, 0) * 0.5, 4.0)
    quality_score = max(0.0, min(10.0, quality_score))
    breakdown["quality_score"] = round(quality_score, 1)

    total = round(
        max(0.0, min(100.0,
            energy_score + structure_score + ci_score + quality_score
        )), 1
    )
    return total, breakdown


# ─────────────────────────────────────────────
# Main integration function
# ─────────────────────────────────────────────
def build_context_report(
    raw_energy_kwh: float,
    code_features: dict,
    api_key: Optional[str] = None,
    deployment_env: str = "local",
    hardware_override: Optional[str] = None,
    baseline_energy_kwh: float = None,   # ← ADD THIS
) -> ContextReport:
    """
    Build a full context report combining energy prediction with
    real carbon data, hardware info, and green score.
    """
    report = ContextReport()
    report.analysis_timestamp = datetime.now(timezone.utc).isoformat()
    report.raw_energy_kwh = raw_energy_kwh
    report.deployment_env = deployment_env

    # 1. Carbon intensity (Home Assistant when configured, else optional grid HTTP API, else fallback)
    report.carbon_zone = display_grid_region_label()
    metrics = fetch_carbon_metrics(api_key, zone=em_zone_code_from_env())
    ci = metrics.intensity_g_per_kwh
    source = metrics.source
    report.carbon_intensity_g_per_kwh = ci
    report.carbon_source = source
    report.grid_fossil_fuel_percent = metrics.fossil_fuel_percent
    report.carbon_is_stale = source == "fallback_maharashtra_grid"
    report.carbon_timestamp = metrics.observed_at or datetime.now(timezone.utc).isoformat()

    # 2. Hardware
    if hardware_override and hardware_override in HARDWARE_TDP:
        report.hardware_type = hardware_override
        report.hardware_tdp_w = HARDWARE_TDP[hardware_override]
    else:
        hw_type, hw_tdp = detect_hardware()
        report.hardware_type = hw_type
        report.hardware_tdp_w = hw_tdp

    # 3. PUE adjustment
    report.pue = PUE.get(deployment_env, 1.6)
    report.adjusted_energy_kwh = raw_energy_kwh * report.pue

    # Hardware efficiency multiplier
    hw_multiplier = {
        "graviton": 0.60,
        "apple_m":  0.40,
        "arm":      0.70,
        "x86":      1.00,
        "unknown":  1.00,
    }.get(report.hardware_type, 1.0)
    report.adjusted_energy_kwh *= hw_multiplier

    # 4. Carbon footprint (physical units: kWh × gCO₂e/kWh → gCO₂e)
    report.carbon_footprint_g = report.adjusted_energy_kwh * ci
    report.carbon_footprint_kg = report.carbon_footprint_g / 1000.0

    # 5. Green Score
    report.green_score, report.score_breakdown = calculate_green_score(
        report.adjusted_energy_kwh,
        code_features,
        ci,
        baseline_energy_kwh=baseline_energy_kwh,   # ← PASS IT
    )

    log.info(
        f"Context: energy={report.adjusted_energy_kwh:.4e} kWh | "
        f"carbon={report.carbon_footprint_g:.4f} gCO₂ | "
        f"score={report.green_score}"
    )

    return report


# ─────────────────────────────────────────────
# Utility: human-readable energy formatting
# ─────────────────────────────────────────────
def format_energy(kwh: float) -> str:
    """Human-readable energy formatting (input is kWh)."""
    if kwh < 1e-12:
        return f"{kwh * 1e15:.3f} pWh"
    elif kwh < 1e-9:
        return f"{kwh * 1e12:.3f} nWh"
    elif kwh < 1e-6:
        return f"{kwh * 1e9:.3f} μWh"
    elif kwh < 1e-3:
        return f"{kwh * 1e6:.3f} mWh"
    elif kwh < 1.0:
        return f"{kwh * 1e3:.4f} Wh"
    else:
        return f"{kwh:.6f} kWh"


def format_carbon(g: float) -> str:
    """Human-readable carbon formatting (input is grams)."""
    if g < 1e-6:
        return f"{g * 1e9:.3f} ngCO₂"
    elif g < 1e-3:
        return f"{g * 1e6:.3f} μgCO₂"
    elif g < 1.0:
        return f"{g * 1000:.4f} mgCO₂"
    elif g < 1000:
        return f"{g:.4f} gCO₂"
    else:
        return f"{g/1000:.4f} kgCO₂"


def format_duration_s(seconds: Optional[float]) -> str:
    """Human-readable duration for UI (measurement comes from Ollama API)."""
    if seconds is None:
        return ""
    try:
        s = float(seconds)
    except (TypeError, ValueError):
        return ""
    if s < 0:
        return ""
    if s < 1.0:
        return f"{s * 1000.0:.0f} ms"
    if s < 60.0:
        return f"{s:.2f} s"
    m = int(s // 60)
    r = s - m * 60
    return f"{m}m {r:.1f}s"


def avg_ollama_power_watts_from_env() -> Optional[float]:
    """
    Optional average system/GPU draw during Ollama inference (watts).
    Set GREENOPS_OLLAMA_AVG_POWER_WATTS in .env — measure with a plug meter,
    Intel XTU, HWiNFO, or vendor tools; no default (avoids fake precision).
    """
    raw = os.getenv("GREENOPS_OLLAMA_AVG_POWER_WATTS", "").strip()
    if not raw:
        return None
    try:
        p = float(raw)
    except ValueError:
        log.warning("GREENOPS_OLLAMA_AVG_POWER_WATTS is not a valid number — ignoring")
        return None
    if p <= 0:
        return None
    return p


def ollama_inference_metrics(
    total_duration_ns: Optional[float],
    carbon_intensity_g_per_kwh: float,
) -> dict:
    """
    Optional energy/CO₂ for an Ollama /api/generate call from wall time (ns) and
    GREENOPS_OLLAMA_AVG_POWER_WATTS if set. Used for API payloads and compact UI hints.
    """
    out: dict = {
        "total_duration_ns": total_duration_ns,
        "duration_s": None,
        "avg_power_watts": avg_ollama_power_watts_from_env(),
        "energy_kwh": None,
        "carbon_g": None,
    }
    if total_duration_ns is None:
        return out
    try:
        td = float(total_duration_ns)
    except (TypeError, ValueError):
        return out
    if td < 0:
        return out
    duration_s = td / 1e9
    out["duration_s"] = duration_s
    power_w = out["avg_power_watts"]
    if power_w:
        # J = W·s; kWh = J / 3.6e6
        energy_kwh = (power_w * duration_s) / 3_600_000.0
        out["energy_kwh"] = energy_kwh
        try:
            ci = float(carbon_intensity_g_per_kwh)
        except (TypeError, ValueError):
            ci = FALLBACK_CARBON_INTENSITY_G_PER_KWH
        out["carbon_g"] = energy_kwh * ci
    return out


def enrich_ollama_metrics_for_ui(m: dict) -> dict:
    """Add display strings for templates / JSON (does not mutate input)."""
    if not m:
        return {}
    d = dict(m)
    ds = d.get("duration_s")
    d["duration_display"] = format_duration_s(ds) if ds is not None else ""
    ek = d.get("energy_kwh")
    cg = d.get("carbon_g")
    d["energy_display"] = format_energy(ek) if ek is not None else ""
    d["carbon_display"] = format_carbon(cg) if cg is not None else ""
    d["power_configured"] = d.get("avg_power_watts") is not None
    return d


if __name__ == "__main__":
    import json

    sample_features = {
        "loc": 80, "num_loops": 4, "nested_loops": 2,
        "list_comprehensions": 1, "has_recursion": 0,
        "uses_numpy": 1, "uses_pandas": 0,
        "try_except_blocks": 2, "io_operations": 3,
    }
    report = build_context_report(
        raw_energy_kwh=2.5e-5,
        code_features=sample_features,
    )
    print(json.dumps(report.to_dict(), indent=2, default=str))
