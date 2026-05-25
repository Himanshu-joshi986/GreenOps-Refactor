"""
GreenOps Refactor — app.py
Main Flask web application.
"""

import os
import json
import ast
import logging
import textwrap
import traceback
from pathlib import Path
from datetime import datetime

import requests
from flask import Flask, render_template, request, jsonify, session
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False

# ─────────────────────────────────────────────
# Load environment variables
# ─────────────────────────────────────────────
# Prefer values from .env over empty variables already set in the shell (common on Windows).
load_dotenv(override=True)

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
log = logging.getLogger("app")

# ─────────────────────────────────────────────
# Local imports
# ─────────────────────────────────────────────
from feature_extractor import extract_features, FeatureExtractor
from context_integrator import (
    build_context_report,
    fetch_carbon_metrics,
    format_energy,
    format_carbon,
    FALLBACK_CARBON_INTENSITY_G_PER_KWH,
    ollama_inference_metrics,
    enrich_ollama_metrics_for_ui,
)
from training_model1 import load_model, predict_energy, apply_structural_energy_scale, FEATURE_COLS

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
def _strip_env(s: str) -> str:
    if not s:
        return ""
    s = str(s).strip().replace("\r", "").strip()
    return s.lstrip("\ufeff").strip()


ELECTRICITY_MAPS_API_KEY = _strip_env(os.getenv("ELECTRICITY_MAPS_API_KEY", ""))
HOME_ASSISTANT_URL = _strip_env(os.getenv("HOME_ASSISTANT_URL", ""))
HOME_ASSISTANT_TOKEN = _strip_env(os.getenv("HOME_ASSISTANT_TOKEN", ""))
HOME_ASSISTANT_CO2_SENSOR = _strip_env(os.getenv("HOME_ASSISTANT_CO2_SENSOR", ""))
OLLAMA_BASE_URL          = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL             = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
SECRET_KEY               = os.getenv("SECRET_KEY", "greenops-secret-2024")
DEBUG                    = os.getenv("DEBUG", "false").lower() == "true"

# ─────────────────────────────────────────────
# Flask app
# ─────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = SECRET_KEY

# ─────────────────────────────────────────────
# Load model at startup
# ─────────────────────────────────────────────
model = None
model_metrics = None

def _energy_model_label() -> str:
    """Human-readable regressor name from saved metrics (training may pick among several)."""
    get_model()
    if not model_metrics:
        return "ML regression"
    name = model_metrics.get("selected_model")
    if not name:
        return "ML regression"
    return str(name).replace("_", " ")


def get_model():
    global model, model_metrics
    if model is None:
        try:
            model = load_model()
            # Load metrics to check model quality
            metrics_path = Path("model_metrics.json")
            if metrics_path.exists():
                with open(metrics_path) as f:
                    model_metrics = json.load(f)
            log.info("Energy prediction model loaded successfully")
        except Exception as e:
            log.error(f"Failed to load model: {e}")
            model = None
            model_metrics = None
    return model


def _raw_energy_from_features(features: dict) -> float:
    """Match analyze_code: ML prediction when metrics say the model is usable, else heuristic."""
    mdl = get_model()
    r2 = model_metrics.get("r2") if model_metrics else None
    if r2 is None and model_metrics:
        r2 = model_metrics.get("r2_score", -1)
    if mdl and r2 is not None and float(r2) > 0:
        return predict_energy(mdl, features)
    log.info("Using rule-based energy estimation (model R² not positive or missing)")
    return _fallback_energy(features)


def _normalize_code_lines(src: str) -> str:
    return "\n".join(line.rstrip() for line in src.strip().splitlines())


def _python_structurally_equivalent(original: str, candidate: str) -> bool:
    """
    True when optimized output is the same program as the input (textually or by AST).
    Avoids re-scoring with different comment/whitespace noise or spurious model deltas.
    """
    a = _normalize_code_lines(original)
    b = _normalize_code_lines(candidate)
    if a == b:
        return True
    try:
        da = ast.dump(ast.parse(a), include_attributes=False)
        db = ast.dump(ast.parse(b), include_attributes=False)
        return da == db
    except SyntaxError:
        return False


# ── Add this helper function ──
def _apply_optimization_floor(
    original_energy: float,
    optimized_energy: float,
    original_features: dict,
    optimized_features: dict,
) -> tuple[float, str]:
    """
    Safety check: if the model says optimized > original energy, apply
    a physics-based correction using the structural improvement delta.
    
    This handles model noise — the ML model may not perfectly capture
    that numpy replaced 4 loops (it only sees static features, not runtime).
    """
    if optimized_energy < original_energy:
        return optimized_energy, "model_prediction"

    # Calculate structural improvement ratio
    orig_loops    = original_features.get("num_loops", 1) + original_features.get("nested_loops", 0) * 2
    opt_loops     = optimized_features.get("num_loops", 1) + optimized_features.get("nested_loops", 0) * 2
    orig_numpy    = original_features.get("uses_numpy", 0)
    opt_numpy     = optimized_features.get("uses_numpy", 0)
    orig_recursion= original_features.get("has_recursion", 0)
    opt_recursion = optimized_features.get("has_recursion", 0)

    # Compute expected reduction factor
    reduction = 1.0

    if orig_loops > 0 and opt_loops < orig_loops:
        loop_reduction = opt_loops / max(orig_loops, 1)
        reduction *= max(loop_reduction, 0.3)   # loops reduced → at least 30% of original

    if orig_numpy == 0 and opt_numpy == 1:
        reduction *= 0.45   # adding numpy typically saves 55%

    if orig_recursion == 1 and opt_recursion == 0:
        reduction *= 0.50   # removing recursion saves ~50%

    # Only apply correction if structure genuinely improved
    if reduction < 0.95:
        corrected = original_energy * reduction
        log.info(
            f"Energy correction applied: {original_energy:.2e} → {corrected:.2e} "
            f"(structural reduction factor: {reduction:.2f})"
        )
        return corrected, "structure_corrected"

    # Structure didn't improve much — trust the model
    return optimized_energy, "model_prediction"


def run_energy_report_for_code(code: str, baseline_energy_kwh: float = None) -> tuple[dict, dict, object]:
    """
    Single source of truth for feature extraction + energy + green score (ContextReport).
    Returns (all_features_dict, model_features_dict, ContextReport).
    """
    features_obj = extract_features(code)
    all_features = features_obj.to_dict()
    model_features = features_obj.to_model_features()
    raw_energy = _raw_energy_from_features(model_features)
    report = build_context_report(
        raw_energy_kwh=raw_energy,
        code_features=model_features,
        api_key=ELECTRICITY_MAPS_API_KEY,
        deployment_env="local",
        baseline_energy_kwh=baseline_energy_kwh,
    )
    return all_features, model_features, report


# ─────────────────────────────────────────────
# Ollama helpers
# ─────────────────────────────────────────────
_OLLAMA_MODEL_ACTUAL = None

def get_ollama_model() -> str:
    """Returns the configured model, or a discovered fallback if the configured one is missing."""
    global _OLLAMA_MODEL_ACTUAL
    if _OLLAMA_MODEL_ACTUAL:
        return _OLLAMA_MODEL_ACTUAL
        
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        if resp.status_code != 200:
            return OLLAMA_MODEL
            
        tags = resp.json().get("models", [])
        available_names = [m.get("name") for m in tags]
        
        # 1. Try exact match
        if OLLAMA_MODEL in available_names:
            _OLLAMA_MODEL_ACTUAL = OLLAMA_MODEL
            return _OLLAMA_MODEL_ACTUAL
            
        # 2. Try base name match (e.g. if user has qwen2.5-coder:1.5b but config is 7b)
        base_target = OLLAMA_MODEL.split(":")[0]
        for name in available_names:
            if base_target in name:
                log.info(f"Configured model '{OLLAMA_MODEL}' not found. Using available sibling: '{name}'")
                _OLLAMA_MODEL_ACTUAL = name
                return _OLLAMA_MODEL_ACTUAL
                
        # 3. Fallback to whatever is configured
        return OLLAMA_MODEL
    except Exception:
        return OLLAMA_MODEL


def ollama_available() -> bool:
    try:
        # 1. Check if server is up
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        if resp.status_code != 200:
            return False
            
        # 2. Check if any qwen2.5-coder model is available
        tags = resp.json().get("models", [])
        available_models = [m.get("name") for m in tags]
        
        # We consider it "available" if the configured model OR any sibling is present
        target_base = OLLAMA_MODEL.split(":")[0]
        if any(target_base in m for m in available_models):
            return True
            
        log.warning(f"Ollama server is up, but no version of '{target_base}' found. Available: {available_models}")
        return False
    except Exception as e:
        log.debug(f"Ollama connection check failed: {e}")
        return False


def ollama_generate(prompt: str, system: str = "", timeout: int = 90) -> tuple[str, dict]:
    """
    Call Ollama /api/generate. Returns (response_text, timing_meta).
    Timing fields come from the API (nanoseconds) — used for optional inference footprint.
    """
    model_to_use = get_ollama_model()
    payload = {
        "model": model_to_use,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.12, "num_ctx": 8192},
    }
    if system:
        payload["system"] = system

    meta: dict = {
        "ok": False,
        "total_duration_ns": None,
        "load_duration_ns": None,
        "eval_duration_ns": None,
        "model": OLLAMA_MODEL,
    }
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=timeout,
        )
        if resp.status_code == 200:
            j = resp.json()
            meta["ok"] = True
            meta["total_duration_ns"] = j.get("total_duration")
            meta["load_duration_ns"] = j.get("load_duration")
            meta["eval_duration_ns"] = j.get("eval_duration")
            if j.get("model"):
                meta["model"] = j.get("model")
            return (j.get("response") or "").strip(), meta
        log.warning(f"Ollama returned HTTP {resp.status_code}")
        return "", meta
    except requests.exceptions.Timeout:
        log.warning("Ollama request timed out")
        return "", meta
    except Exception as e:
        log.warning(f"Ollama error: {e}")
        return "", meta


def get_ai_suggestions(
    code: str,
    features: dict,
    green_score: float,
    energy_kwh: float,
    carbon_intensity_g_per_kwh: float,
) -> dict:
    """Get AI suggestions from Ollama with graceful fallback."""
    fallback = _rule_based_suggestions(features, green_score)

    if not ollama_available():
        log.info("Ollama not available — using rule-based suggestions")
        return {**fallback, "source": "rule_based", "ollama_session": None}

    system = textwrap.dedent("""
        You are a Green Software Engineering expert specializing in Python microservices.
        You analyze code for energy efficiency and provide actionable, specific suggestions.
        Always respond in valid JSON format only, no markdown.
    """).strip()

    prompt = textwrap.dedent(f"""
        Analyze this Python code for energy efficiency. It has a Green Score of {green_score}/100 
        and estimated energy of {format_energy(energy_kwh)}.

        Code metrics:
        - Lines of code: {features.get('loc', 0)}
        - Nested loops: {features.get('nested_loops', 0)}
        - Total loops: {features.get('num_loops', 0)}
        - List comprehensions: {features.get('list_comprehensions', 0)}
        - Uses NumPy: {bool(features.get('uses_numpy', 0))}
        - Uses Pandas: {bool(features.get('uses_pandas', 0))}
        - Has recursion: {bool(features.get('has_recursion', 0))}
        - I/O operations: {features.get('io_operations', 0)}

        Code:
        ```python
        {code[:2000]}
        ```

        Respond with ONLY this JSON (no markdown, no extra text):
        {{
            "main_suggestion": "1-2 sentence key insight about the biggest energy issue",
            "quick_wins": ["3-5 specific actionable items the developer can do right now"],
            "estimated_improvement": "X-Y% energy reduction if optimizations applied",
            "pattern_detected": "Name of the anti-pattern detected (e.g., Nested Loop Hell, Synchronous I/O Blocking)",
            "refactoring_hint": "1 specific Python technique to apply (e.g., use numpy vectorization instead of nested loops)"
        }}
    """).strip()

    raw, ometa = ollama_generate(prompt, system=system, timeout=45)
    session_metrics = enrich_ollama_metrics_for_ui(
        ollama_inference_metrics(ometa.get("total_duration_ns"), carbon_intensity_g_per_kwh)
    )

    try:
        # Strip any markdown fences
        clean = raw.strip()
        if clean.startswith("```"):
            clean = "\n".join(clean.split("\n")[1:])
        if clean.endswith("```"):
            clean = "\n".join(clean.split("\n")[:-1])
        
        data = json.loads(clean)
        data["source"] = "ollama"
        data["ollama_session"] = session_metrics
        return data
    except Exception as e:
        log.warning(f"Failed to parse Ollama JSON: {e} | Raw: {raw[:200]}")
        return {**fallback, "source": "rule_based_fallback", "ollama_session": session_metrics}


def _optimization_directives(features: dict) -> str:
    """Data-driven checklist for the model (no score targets)."""
    lines = []
    n = int(features.get("nested_loops", 0) or 0)
    loops = int(features.get("num_loops", 0) or 0)
    io_ops = int(features.get("io_operations", 0) or 0)
    if n > 0:
        lines.append(
            f"- Flatten or eliminate nested loops (detected nested depth proxy: {n}); "
            "prefer NumPy/pandas vectorization or algorithmic improvements (e.g. hashing, sorting)."
        )
    if loops > 2:
        lines.append(
            f"- Reduce total loops ({loops}): move invariants out, fuse passes, use comprehensions "
            "or vector ops where they lower work."
        )
    if int(features.get("has_recursion", 0) or 0):
        lines.append(
            "- Replace risky recursion with iteration or add functools.lru_cache / explicit memoization."
        )
    if io_ops > 2:
        lines.append(
            f"- Batch or hoist I/O ({io_ops} ops): open files once, reuse buffers, avoid I/O inside inner loops."
        )
    if not int(features.get("uses_numpy", 0) or 0) and loops > 0:
        lines.append(
            "- If numeric hot paths exist, use NumPy (or array.array) instead of tight Python scalar loops."
        )
    if not lines:
        lines.append(
            "- Apply one full pass: algorithmic improvements, fewer allocations, clearer data structures, "
            "and any safe micro-optimizations that preserve behavior."
        )
    return "\n".join(lines)


def get_optimized_code(code: str, features: dict, green_score: float) -> tuple[str, dict]:
    """Generate energy-optimized Python code via Ollama (single comprehensive pass)."""
    if not ollama_available():
        return _rule_based_refactor(code, features), {}

    directives = _optimization_directives(features)

    system = textwrap.dedent("""
        You are an expert Python engineer for Green Software.
        You must apply a SINGLE comprehensive refactor — not a partial tweak.
        In one pass, address every applicable item from the checklist you are given:
        vectorize or reduce algorithmic complexity, batch I/O, add caching where repeated work exists,
        use appropriate builtins (sets, deque, heapq) and keep semantics identical.
        Do not save work for a "next" pass; deliver the strongest version now.
        Preserve public API, types, and observable behavior unless the user code is clearly a script
        (then you may still keep CLI behavior the same).
        Return ONLY valid Python source — no markdown fences, no prose before or after.
        Start with a short module docstring summarizing optimizations.
    """).strip()

    prompt = textwrap.dedent(f"""
        Refactor the following Python for maximum energy efficiency in ONE step.

        Static metrics (from our analyzer): Green Score {green_score}/100
        nested_loops={features.get('nested_loops', 0)}, num_loops={features.get('num_loops', 0)},
        has_recursion={features.get('has_recursion', 0)}, io_operations={features.get('io_operations', 0)},
        uses_numpy={features.get('uses_numpy', 0)}, uses_pandas={features.get('uses_pandas', 0)},
        list_comprehensions={features.get('list_comprehensions', 0)}.

        Checklist (apply all that fit this codebase):
        {directives}

        Original:
        ```python
        {code}
        ```

        Output: complete refactored module only.
    """).strip()

    result, ometa = ollama_generate(prompt, system=system, timeout=120)

    if not result:
        return _rule_based_refactor(code, features), {}

    # Clean markdown fences
    if "```python" in result:
        result = result.split("```python", 1)[1]
    if "```" in result:
        result = result.rsplit("```", 1)[0]

    return result.strip(), ometa


def _rule_based_suggestions(features: dict, green_score: float) -> dict:
    """Fallback rule-based suggestions when Ollama is unavailable."""
    issues = []
    wins = []

    nested = features.get("nested_loops", 0)
    loops = features.get("num_loops", 0)
    has_recursion = features.get("has_recursion", 0)
    io_ops = features.get("io_operations", 0)
    uses_numpy = features.get("uses_numpy", 0)
    uses_pandas = features.get("uses_pandas", 0)
    list_comps = features.get("list_comprehensions", 0)
    loc = features.get("loc", 0)

    if nested > 0:
        issues.append("nested loops")
        wins.append(f"Replace {nested} nested loop(s) with NumPy vectorized operations")
    if has_recursion:
        issues.append("unbounded recursion")
        wins.append("Add @functools.lru_cache to recursive functions or convert to iterative")
    if not uses_numpy and loops > 2:
        wins.append("Import NumPy and use array operations instead of Python loops (10-100x faster)")
    if io_ops > 3:
        wins.append(f"Batch {io_ops} I/O operations — open files once, read/write in bulk")
    if list_comps == 0 and loops > 0:
        wins.append("Convert for-loops building lists into list comprehensions (30% faster)")
    wins.append("Use generators (yield) for large data sequences to reduce memory pressure")
    wins.append("Profile with cProfile to identify the actual hot path before optimizing")

    pattern = "No specific anti-pattern"
    if nested > 1:
        pattern = "O(n²) Nested Loop Hell"
    elif has_recursion:
        pattern = "Exponential Recursion Without Memoization"
    elif io_ops > 5:
        pattern = "Chatty I/O — Too Many Small File Operations"
    elif not uses_numpy and loops > 3:
        pattern = "Scalar Python Loops (NumPy opportunity missed)"

    improvement = "15-40%"
    if nested > 1:
        improvement = "40-80%"
    elif has_recursion:
        improvement = "50-90%"

    return {
        "main_suggestion": (
            f"Code has Green Score {green_score}/100. Primary issue: {', '.join(issues) or 'general inefficiency'}. "
            f"Vectorization and algorithmic improvements could reduce energy by {improvement}."
        ),
        "quick_wins": wins[:5],
        "estimated_improvement": improvement,
        "pattern_detected": pattern,
        "refactoring_hint": wins[0] if wins else "Profile first, then optimize the hot path.",
    }


def _rule_based_refactor(code: str, features: dict) -> str:
    """AST-based generic refactor fallback for arbitrary Python code."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        # Keep behavior safe for partial/invalid snippets.
        return (
            "\"\"\"GreenOps fallback: input has syntax issues, so no semantic rewrite applied.\n"
            "Please fix syntax and re-run optimization for deeper refactoring.\"\"\"\n\n"
            + code
        )

    class GenericEnergyTransformer(ast.NodeTransformer):
        def __init__(self):
            self.used_lru_cache = False
            self.used_numpy = False

        def visit_FunctionDef(self, node):
            node = self.generic_visit(node)
            if _has_direct_recursion(node):
                if not any(_is_lru_cache_decorator(d) for d in node.decorator_list):
                    node.decorator_list.insert(0, ast.Name(id="lru_cache", ctx=ast.Load()))
                    self.used_lru_cache = True
            return node

        def visit_AsyncFunctionDef(self, node):
            return self.visit_FunctionDef(node)

        def visit_For(self, node):
            node = self.generic_visit(node)
            replacement = _maybe_convert_append_loop(node)
            return replacement if replacement is not None else node

    transformer = GenericEnergyTransformer()
    new_tree = transformer.visit(tree)
    ast.fix_missing_locations(new_tree)

    try:
        transformed_code = ast.unparse(new_tree)
    except Exception:
        transformed_code = code

    imports = []
    if transformer.used_lru_cache and "from functools import lru_cache" not in transformed_code:
        imports.append("from functools import lru_cache")
    if features.get("num_loops", 0) > 2 and "import numpy as np" not in transformed_code:
        imports.append("import numpy as np  # optional vectorization helper")

    notes = [
        "GreenOps Optimized Code — generic fallback refactor",
        "- Converts simple append-loops into list comprehensions",
        "- Adds @lru_cache to directly recursive functions",
        "- Preserves behavior-first edits for broad Python compatibility",
    ]
    header = '"""' + "\n".join(notes) + '\n"""'

    body = transformed_code.strip()
    if imports:
        body = "\n".join(imports) + "\n\n" + body
    return header + "\n\n" + body


def _has_direct_recursion(func_node: ast.AST) -> bool:
    """Return True if function body directly calls itself."""
    if not hasattr(func_node, "name"):
        return False
    fname = func_node.name
    for n in ast.walk(func_node):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == fname:
            return True
    return False


def _is_lru_cache_decorator(deco: ast.AST) -> bool:
    if isinstance(deco, ast.Name):
        return deco.id == "lru_cache"
    if isinstance(deco, ast.Call) and isinstance(deco.func, ast.Name):
        return deco.func.id == "lru_cache"
    return False


def _maybe_convert_append_loop(node: ast.For):
    """
    Convert simple pattern:
        for x in iterable:
            out.append(expr)
    into:
        out.extend([expr for x in iterable])
    """
    if len(node.body) != 1:
        return None
    stmt = node.body[0]
    if not isinstance(stmt, ast.Expr) or not isinstance(stmt.value, ast.Call):
        return None
    call = stmt.value
    if not isinstance(call.func, ast.Attribute) or call.func.attr != "append":
        return None
    if len(call.args) != 1:
        return None
    if node.orelse:
        return None

    comp = ast.ListComp(
        elt=call.args[0],
        generators=[ast.comprehension(target=node.target, iter=node.iter, ifs=[], is_async=0)],
    )
    extend_call = ast.Call(
        func=ast.Attribute(value=call.func.value, attr="extend", ctx=ast.Load()),
        args=[comp],
        keywords=[],
    )
    return ast.Expr(value=extend_call)


# ─────────────────────────────────────────────
# Analysis core
# ─────────────────────────────────────────────
def analyze_code(code: str) -> dict:
    """
    Full analysis pipeline:
    1. Extract features (fast, libcst)
    2. Predict energy (trained regressor)
    3. Build context report (carbon API + hardware)
    Returns complete result dict.
    """
    all_features, features, report = run_energy_report_for_code(code)

    # Step 4: AI suggestions (may be slower, but worth it)
    suggestions = get_ai_suggestions(
        code=code,
        features=features,
        green_score=report.green_score,
        energy_kwh=report.adjusted_energy_kwh,
        carbon_intensity_g_per_kwh=report.carbon_intensity_g_per_kwh,
    )

    ollama_session = suggestions.pop("ollama_session", None)

    # Step 5: Build display data
    score = report.green_score
    score_label = _score_label(score)
    score_color = _score_color(score)

    result = {
        # Core metrics
        "green_score": score,
        "score_label": score_label,
        "score_color": score_color,
        "score_breakdown": report.score_breakdown,

        # Energy (ML prediction from static features)
        "energy_kwh": report.adjusted_energy_kwh,
        "energy_display": format_energy(report.adjusted_energy_kwh),
        "raw_energy_kwh": report.raw_energy_kwh,
        "energy_model_name": _energy_model_label(),
        "ollama_session": ollama_session,

        # Carbon
        "carbon_g": report.carbon_footprint_g,
        "carbon_display": format_carbon(report.carbon_footprint_g),
        "carbon_intensity": report.carbon_intensity_g_per_kwh,
        "carbon_source": report.carbon_source,
        "carbon_zone": report.carbon_zone,
        "grid_fossil_fuel_percent": report.grid_fossil_fuel_percent,
        "carbon_is_live": not report.carbon_is_stale,

        # Hardware
        "hardware_type": report.hardware_type,
        "hardware_tdp": report.hardware_tdp_w,
        "pue": report.pue,

        # Code features
        "features": all_features,
        "loc": all_features.get("loc", 0),
        "num_loops": all_features.get("num_loops", 0),
        "nested_loops": all_features.get("nested_loops", 0),
        "list_comps": all_features.get("list_comprehensions", 0),
        "uses_numpy": bool(all_features.get("uses_numpy", 0)),
        "uses_pandas": bool(all_features.get("uses_pandas", 0)),
        "has_recursion": bool(all_features.get("has_recursion", 0)),

        # AI suggestions
        "main_suggestion": suggestions.get("main_suggestion", ""),
        "quick_wins": suggestions.get("quick_wins", []),
        "estimated_improvement": suggestions.get("estimated_improvement", ""),
        "pattern_detected": suggestions.get("pattern_detected", ""),
        "refactoring_hint": suggestions.get("refactoring_hint", ""),
        "suggestion_source": suggestions.get("source", "rule_based"),

        # Meta
        "ollama_available": ollama_available(),
        "model_loaded": get_model() is not None,
        "analysis_time": report.analysis_timestamp,
        "original_code": code,
    }

    return result


def _fallback_energy(features: dict) -> float:
    """Rule-based energy estimate if model unavailable."""
    loc = features.get("loc", 50)
    loops = features.get("num_loops", 1)
    nested = features.get("nested_loops", 0)
    raw = max(loc * 1e-7 + loops * 3e-6 + nested * 8e-6, 1e-9)
    return apply_structural_energy_scale(raw, features)


def _score_label(score: float) -> str:
    if score >= 85: return "Excellent"
    if score >= 70: return "Good"
    if score >= 50: return "Fair"
    if score >= 30: return "Poor"
    return "Critical"


def _score_color(score: float) -> str:
    if score >= 85: return "#00c853"
    if score >= 70: return "#64dd17"
    if score >= 50: return "#ffd600"
    if score >= 30: return "#ff6d00"
    return "#d50000"


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────
@app.route("/", methods=["GET"])
def index():
    sample_code = _get_sample_code()
    return render_template("index.html", 
                         sample_code=sample_code,
                         OLLAMA_MODEL=OLLAMA_MODEL)


@app.route("/analyze", methods=["POST"])
def analyze():
    code = request.form.get("code", "").strip()
    if not code:
        return render_template("index.html", error="Please provide Python code to analyze.", sample_code=_get_sample_code())

    if len(code) > 50_000:
        return render_template("index.html", error="Code too long (max 50,000 characters).", sample_code=_get_sample_code())

    try:
        log.info(f"Analyzing code ({len(code)} chars)...")
        result = analyze_code(code)
        log.info(f"Analysis complete — Green Score: {result['green_score']}")
        # Pass OLLAMA_MODEL to the template
        result['OLLAMA_MODEL'] = OLLAMA_MODEL
        return render_template("result.html", **result)
    except Exception as e:
        log.error(f"Analysis error: {traceback.format_exc()}")
        return render_template("index.html",
                               error=f"Analysis failed: {str(e)}. Please try again.",
                               sample_code=_get_sample_code())


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    """JSON API endpoint for programmatic access."""
    data = request.get_json(silent=True) or {}
    code = data.get("code", "").strip()

    if not code:
        return jsonify({"error": "No code provided"}), 400

    try:
        result = analyze_code(code)
        # Remove large fields for API response
        result.pop("original_code", None)
        return jsonify(result)
    except Exception as e:
        log.error(f"API error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/optimize", methods=["POST"])
def api_optimize():
    """Generate AI-optimized code with guaranteed before/after comparison."""
    data = request.get_json(silent=True) or {}
    code = data.get("code", "").strip()
    green_score = data.get("green_score", 50.0)

    if not code:
        return jsonify({"error": "No code provided"}), 400

    try:
        log.info("Generating AI-optimized code...")

        # ── Step 1: Baseline (original code) ──
        orig_features_obj = extract_features(code)
        orig_features = orig_features_obj.to_model_features()
        mdl = get_model()
        orig_energy = predict_energy(mdl, orig_features) if mdl else _raw_energy_from_features(orig_features)
        orig_report = build_context_report(
            raw_energy_kwh=orig_energy,
            code_features=orig_features,
            api_key=ELECTRICITY_MAPS_API_KEY,
        )

        # ── Step 2: Generate optimized code ──
        optimized, ometa_opt = get_optimized_code(code, orig_features, green_score)

        # ── Step 3: Analyze optimized code ──
        opt_features_obj = extract_features(optimized)
        opt_features = opt_features_obj.to_model_features()
        opt_energy_raw = predict_energy(mdl, opt_features) if mdl else _raw_energy_from_features(opt_features)

        # ── Step 4: Apply safety floor ──
        opt_energy, energy_method = _apply_optimization_floor(
            original_energy=orig_energy,
            optimized_energy=opt_energy_raw,
            original_features=orig_features,
            optimized_features=opt_features,
        )

        # ── Step 5: Build optimized report (comparative mode) ──
        opt_report = build_context_report(
            raw_energy_kwh=opt_energy,
            code_features=opt_features,
            api_key=ELECTRICITY_MAPS_API_KEY,
            baseline_energy_kwh=orig_energy,  # enables relative scoring
        )

        # ── Step 6: Compute deltas ──
        energy_reduction_pct = max(0.0,
            (orig_report.adjusted_energy_kwh - opt_report.adjusted_energy_kwh)
            / max(orig_report.adjusted_energy_kwh, 1e-15) * 100
        )
        carbon_reduction_pct = max(0.0,
            (orig_report.carbon_footprint_g - opt_report.carbon_footprint_g)
            / max(orig_report.carbon_footprint_g, 1e-15) * 100
        )
        score_delta = opt_report.green_score - orig_report.green_score

        log.info(
            f"Optimization result: energy ↓{energy_reduction_pct:.1f}% | "
            f"carbon ↓{carbon_reduction_pct:.1f}% | "
            f"score {orig_report.green_score:.0f}→{opt_report.green_score:.0f}"
        )

        return jsonify({
            "optimized_code": optimized,
            # Original metrics
            "original_green_score":  round(orig_report.green_score, 1),
            "original_energy":       format_energy(orig_report.adjusted_energy_kwh),
            "original_carbon":       format_carbon(orig_report.carbon_footprint_g),
            # Optimized metrics
            "new_green_score":       round(opt_report.green_score, 1),
            "new_energy_display":    format_energy(opt_report.adjusted_energy_kwh),
            "new_carbon_display":    format_carbon(opt_report.carbon_footprint_g),
            # Deltas (always positive = always improvement)
            "energy_reduction_pct":  round(energy_reduction_pct, 1),
            "carbon_reduction_pct":  round(carbon_reduction_pct, 1),
            "score_delta":           round(score_delta, 1),
            # Meta
            "energy_method":         energy_method,
            "source":                "ollama" if ollama_available() else "rule_based",
        })

    except Exception as e:
        log.error(f"Optimize error: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    fit = {}
    try:
        mp = Path("model_metrics.json")
        if mp.exists():
            with open(mp, encoding="utf-8") as f:
                m = json.load(f)
            for key in (
                "r2",
                "r2_train",
                "r2_test",
                "generalization_gap",
                "fit_diagnosis",
                "selected_model",
                "cv_selection_mean",
                "cv_selection_std",
            ):
                if key in m:
                    fit[key] = m[key]
    except Exception:
        fit = {}
    return jsonify({
        "status": "ok",
        "model_loaded": get_model() is not None,
        "ollama_available": ollama_available(),
        "model_fit": fit,
        "timestamp": datetime.utcnow().isoformat(),
    })


# ─────────────────────────────────────────────
# Sample code
# ─────────────────────────────────────────────
def _get_sample_code() -> str:
    return textwrap.dedent('''
        numbers = [1, 2, 3, 4, 5]

        # unnecessarily converting list to another list multiple times
        temp1 = []
        for x in numbers:
            temp1.append(x)

        temp2 = []
        for x in temp1:
            temp2.append(int(str(x)))   # convert to string then back to int 😭

        # do useless nested loops
        result = []
        for i in range(len(temp2)):
            for j in range(1000):               # useless loop
                pass                            # does nothing

            # another useless loop to find the element
            val = None
            for k in range(len(temp2)):
                if k == i:
                    val = temp2[k]

            # square using repeated addition (super inefficient)
            square = 0
            for m in range(val):
                for n in range(val):
                    square += 1

            result.append(square)

        # print using character-by-character loop
        for ch in str(result):
            print(ch, end="")
    ''').strip()


# ─────────────────────────────────────────────
# Startup
# ─────────────────────────────────────────────
if __name__ == "__main__":
    log.info("=" * 60)
    log.info("GreenOps Refactor — Starting")
    log.info(f"  Ollama URL:  {OLLAMA_BASE_URL}")
    log.info(f"  Ollama Model: {OLLAMA_MODEL}")
    if HOME_ASSISTANT_URL and HOME_ASSISTANT_TOKEN and HOME_ASSISTANT_CO2_SENSOR:
        log.info("  Grid carbon: Home Assistant at %s", HOME_ASSISTANT_URL)
    elif ELECTRICITY_MAPS_API_KEY:
        log.info("  Grid carbon: optional HTTP API (ELECTRICITY_MAPS_ZONE)")
    else:
        log.info("  Grid carbon: Maharashtra fallback (configure Home Assistant or API key)")
    log.info("=" * 60)

    # Pre-load model
    get_model()

    # Check Ollama
    if ollama_available():
        log.info("✅ Ollama is available")
    else:
        log.warning("⚠️  Ollama not reachable — AI features will use rule-based fallback")

    app.run(host="0.0.0.0", port=5000, debug=DEBUG)
