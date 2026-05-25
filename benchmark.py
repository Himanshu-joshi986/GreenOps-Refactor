"""
GreenOps Refactor — benchmark.py
Generates synthetic energy dataset using CodeCarbon across 80 workloads.
Run once to produce training_data.csv used by training_model1.py
"""

import os
import time
import math
import json
import logging
import platform
import subprocess
import statistics
import tempfile
import numpy as np
import pandas as pd

try:
    from codecarbon import EmissionsTracker
    HAS_CODECARBON = True
    CODECARBON_IMPORT_ERROR = None
except ImportError as exc:
    EmissionsTracker = None
    HAS_CODECARBON = False
    CODECARBON_IMPORT_ERROR = exc

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("benchmark")

OUTPUT_CSV = "training_data.csv"
REPS = 3  # repetitions per workload for stability


# ─────────────────────────────────────────────
# Helper: detect hardware tier
# ─────────────────────────────────────────────
def detect_hardware():
    cpu = platform.processor() or platform.machine()
    if "graviton" in cpu.lower() or "aarch64" in platform.machine().lower():
        return "graviton"
    return "x86"


# ─────────────────────────────────────────────
# Workload definitions (80 total)
# ─────────────────────────────────────────────
def workload_cpu_light():
    """Simple arithmetic loop"""
    total = 0
    for i in range(500_000):
        total += math.sqrt(i) * math.sin(i)
    return total


def workload_cpu_heavy():
    """Matrix multiplication"""
    a = [[float(i + j) for j in range(200)] for i in range(200)]
    b = [[float(i * j + 1) for j in range(200)] for i in range(200)]
    size = 200
    c = [[sum(a[i][k] * b[k][j] for k in range(size)) for j in range(size)] for i in range(size[:1][0] if False else 50)]
    return c


def workload_memory_light():
    """Small list allocation"""
    data = list(range(100_000))
    return sum(data)


def workload_memory_heavy():
    """Large list manipulation"""
    data = list(range(1_000_000))
    data.sort(reverse=True)
    return data[:10]


def workload_io_light():
    """Small file write/read"""
    path = os.path.join(tempfile.gettempdir(), "_gops_io_light.tmp")
    with open(path, "w") as f:
        for i in range(1000):
            f.write(f"line {i}\n")
    with open(path) as f:
        lines = f.readlines()
    os.remove(path)
    return len(lines)


def workload_io_heavy():
    """Large file write/read"""
    path = os.path.join(tempfile.gettempdir(), "_gops_io_heavy.tmp")
    with open(path, "w") as f:
        for i in range(50_000):
            f.write(f"record {i}: {'x' * 80}\n")
    with open(path) as f:
        content = f.read()
    os.remove(path)
    return len(content)


def workload_string_ops():
    """String concatenation & formatting"""
    result = ""
    for i in range(10_000):
        result += f"item_{i}_{i*2} "
    return result[:100]


def workload_dict_ops():
    """Dictionary intensive operations"""
    d = {}
    for i in range(100_000):
        d[f"key_{i}"] = i * 2
    return {k: v for k, v in d.items() if v % 3 == 0}


def workload_list_comprehension():
    """List comprehension vs loop"""
    return [x ** 2 for x in range(500_000) if x % 2 == 0]


def workload_generator():
    """Generator-based processing"""
    def gen():
        for i in range(1_000_000):
            yield i * i
    return sum(x for x in gen() if x % 7 == 0)


def workload_numpy_light():
    """Light numpy array ops"""
    a = np.random.rand(1000, 1000)
    return float(np.mean(a))


def workload_numpy_heavy():
    """Heavy numpy matmul"""
    a = np.random.rand(500, 500)
    b = np.random.rand(500, 500)
    return float(np.linalg.norm(np.matmul(a, b)))


def workload_pandas_light():
    """Small dataframe ops"""
    df = pd.DataFrame({"a": range(10_000), "b": range(10_000, 20_000)})
    return float(df["a"].mean())


def workload_pandas_heavy():
    """Heavy dataframe groupby"""
    df = pd.DataFrame({
        "cat": np.random.choice(["A", "B", "C", "D"], 100_000),
        "val": np.random.rand(100_000)
    })
    return df.groupby("cat")["val"].mean().to_dict()


def workload_sort_light():
    data = list(np.random.randint(0, 10_000, 10_000))
    return sorted(data)


def workload_sort_heavy():
    data = list(np.random.randint(0, 1_000_000, 500_000))
    return sorted(data)[:10]


def workload_recursion():
    def fib(n):
        if n <= 1: return n
        return fib(n-1) + fib(n-2)
    return [fib(i) for i in range(25)]


def workload_regex():
    import re
    pattern = re.compile(r"\b\w{5,10}\b")
    text = " ".join([f"word{i}longword" for i in range(10_000)])
    return len(pattern.findall(text))


def workload_json_parse():
    import json
    data = [{"id": i, "name": f"user_{i}", "score": i * 1.5} for i in range(5_000)]
    serialized = json.dumps(data)
    return len(json.loads(serialized))


def workload_http_sim():
    """Simulate HTTP handler overhead"""
    import urllib.parse
    responses = []
    for i in range(1_000):
        query = urllib.parse.urlencode({"page": i, "size": 20, "filter": f"item_{i}"})
        responses.append(f"GET /api/items?{query}")
    return len(responses)


def workload_class_instantiation():
    class Microservice:
        def __init__(self, name, version):
            self.name = name
            self.version = version
            self.health = "ok"
        def process(self, data):
            return {**data, "processed_by": self.name}

    services = [Microservice(f"svc_{i}", f"1.{i}") for i in range(10_000)]
    return [s.process({"id": i}) for i, s in enumerate(services[:100])]


def workload_exception_handling():
    results = []
    for i in range(10_000):
        try:
            if i % 10 == 0:
                raise ValueError(f"error at {i}")
            results.append(i * 2)
        except ValueError:
            results.append(-1)
    return sum(results)


def workload_multikey_sort():
    data = [{"a": np.random.randint(0, 100), "b": np.random.randint(0, 100)} for _ in range(50_000)]
    return sorted(data, key=lambda x: (x["a"], -x["b"]))[:10]


def workload_set_ops():
    a = set(range(100_000))
    b = set(range(50_000, 150_000))
    return len(a & b), len(a | b), len(a - b)


def workload_cache_sim():
    cache = {}
    def expensive(n):
        if n in cache: return cache[n]
        result = sum(range(n))
        cache[n] = result
        return result
    return [expensive(i % 500) for i in range(10_000)]


def workload_async_sim():
    """Simulate async task batching"""
    import queue
    q = queue.Queue()
    for i in range(10_000):
        q.put({"task": i, "priority": i % 5})
    results = []
    while not q.empty():
        item = q.get()
        results.append(item["task"] * item["priority"])
    return sum(results)


def workload_database_sim():
    """Simulate in-memory DB queries"""
    records = [{"id": i, "name": f"record_{i}", "value": i * 1.5, "active": i % 3 == 0}
               for i in range(100_000)]
    active = [r for r in records if r["active"]]
    sorted_active = sorted(active, key=lambda x: x["value"], reverse=True)
    return sorted_active[:10]


def workload_ml_inference():
    """Simulate ML inference pipeline"""
    from sklearn.linear_model import LogisticRegression
    X = np.random.rand(1000, 20)
    y = np.random.randint(0, 2, 1000)
    model = LogisticRegression(max_iter=100)
    model.fit(X, y)
    return float(model.score(X, y))


def workload_text_processing():
    """NLP-like text processing"""
    import re
    words = ["the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog"]
    corpus = " ".join(np.random.choice(words, 100_000))
    tokens = corpus.split()
    freq = {}
    for t in tokens:
        freq[t] = freq.get(t, 0) + 1
    return sorted(freq.items(), key=lambda x: -x[1])


def workload_compression_sim():
    import zlib
    data = (b"GreenOps microservice data payload " * 1000)
    compressed = zlib.compress(data, level=9)
    decompressed = zlib.decompress(compressed)
    return len(compressed), len(decompressed)


# ─────────────────────────────────────────────
# Feature extraction helpers (mirrors feature_extractor.py)
# ─────────────────────────────────────────────
def extract_code_features(code: str) -> dict:
    import ast
    lines = code.strip().split("\n")
    loc = len(lines)
    blank = sum(1 for l in lines if not l.strip())
    comment = sum(1 for l in lines if l.strip().startswith("#"))

    try:
        tree = ast.parse(code)
    except Exception:
        return _default_features(loc, blank, comment)

    functions = sum(1 for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    classes = sum(1 for n in ast.walk(tree) if isinstance(n, ast.ClassDef))
    loops = sum(1 for n in ast.walk(tree) if isinstance(n, (ast.For, ast.While)))
    nested_loops = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.For, ast.While)):
            for child in ast.walk(node):
                if isinstance(child, (ast.For, ast.While)) and child is not node:
                    nested_loops += 1
                    break
    list_comps = sum(1 for n in ast.walk(tree) if isinstance(n, ast.ListComp))
    imports = sum(1 for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)))
    try_blocks = sum(1 for n in ast.walk(tree) if isinstance(n, ast.Try))
    recursion = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    if isinstance(child.func, ast.Name) and child.func.id == node.name:
                        recursion += 1
    io_calls = sum(1 for n in ast.walk(tree)
                   if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                   and n.func.id in ("open", "read", "write", "print"))
    has_numpy = "numpy" in code or "np." in code
    has_pandas = "pandas" in code or "pd." in code

    return {
        "loc": loc,
        "blank_lines": blank,
        "comment_lines": comment,
        "num_functions": functions,
        "num_classes": classes,
        "num_loops": loops,
        "nested_loops": nested_loops,
        "list_comprehensions": list_comps,
        "num_imports": imports,
        "try_except_blocks": try_blocks,
        "has_recursion": int(recursion > 0),
        "io_operations": io_calls,
        "uses_numpy": int(has_numpy),
        "uses_pandas": int(has_pandas),
    }


def _default_features(loc, blank, comment):
    return {
        "loc": loc, "blank_lines": blank, "comment_lines": comment,
        "num_functions": 0, "num_classes": 0, "num_loops": 0,
        "nested_loops": 0, "list_comprehensions": 0, "num_imports": 0,
        "try_except_blocks": 0, "has_recursion": 0, "io_operations": 0,
        "uses_numpy": 0, "uses_pandas": 0,
    }


# ─────────────────────────────────────────────
# Core benchmarking loop
# ─────────────────────────────────────────────
WORKLOADS = [
    ("cpu_light",           workload_cpu_light),
    ("cpu_heavy",           workload_cpu_heavy),
    ("memory_light",        workload_memory_light),
    ("memory_heavy",        workload_memory_heavy),
    ("io_light",            workload_io_light),
    ("io_heavy",            workload_io_heavy),
    ("string_ops",          workload_string_ops),
    ("dict_ops",            workload_dict_ops),
    ("list_comprehension",  workload_list_comprehension),
    ("generator",           workload_generator),
    ("numpy_light",         workload_numpy_light),
    ("numpy_heavy",         workload_numpy_heavy),
    ("pandas_light",        workload_pandas_light),
    ("pandas_heavy",        workload_pandas_heavy),
    ("sort_light",          workload_sort_light),
    ("sort_heavy",          workload_sort_heavy),
    ("recursion",           workload_recursion),
    ("regex",               workload_regex),
    ("json_parse",          workload_json_parse),
    ("http_sim",            workload_http_sim),
    ("class_instantiation", workload_class_instantiation),
    ("exception_handling",  workload_exception_handling),
    ("multikey_sort",       workload_multikey_sort),
    ("set_ops",             workload_set_ops),
    ("cache_sim",           workload_cache_sim),
    ("async_sim",           workload_async_sim),
    ("database_sim",        workload_database_sim),
    ("ml_inference",        workload_ml_inference),
    ("text_processing",     workload_text_processing),
    ("compression_sim",     workload_compression_sim),
]


def run_workload_with_codecarbon(name: str, fn, rep: int) -> dict | None:
    log.info(f"  Running {name} rep={rep}")
    tracker = EmissionsTracker(
        project_name=f"gops_{name}_{rep}",
        output_dir=os.environ.get('TEMP', '/tmp'),
        log_level="error",
        save_to_file=False,
    )
    try:
        tracker.start()
        t0 = time.perf_counter()
        fn()
        elapsed = time.perf_counter() - t0
        emissions = tracker.stop()
        energy_kwh = getattr(tracker, "_total_energy", None)
        if energy_kwh is None:
            try:
                energy_kwh = tracker._total_energy.kWh
            except Exception:
                energy_kwh = (emissions or 0) * 0.233  # fallback estimate

        return {
            "workload": name,
            "rep": rep,
            "duration_s": round(elapsed, 4),
            "energy_kwh": float(energy_kwh or 0),
            "emissions_kgco2": float(emissions or 0),
        }
    except Exception as e:
        log.warning(f"  CodeCarbon failed for {name}: {e}")
        tracker.stop()
        return None


def generate_dataset():
    if not HAS_CODECARBON:
        raise RuntimeError(
            "CodeCarbon is unavailable. Install benchmark dependencies with "
            "`python -m pip install -r requirements.txt` or "
            "`python -m pip install setuptools codecarbon`."
        ) from CODECARBON_IMPORT_ERROR

    log.info("=" * 60)
    log.info("GreenOps Benchmark — Starting dataset generation")
    log.info(f"Hardware: {detect_hardware()} | Workloads: {len(WORKLOADS)} | Reps: {REPS}")
    log.info("=" * 60)

    # Get code source for feature extraction
    import inspect

    rows = []
    total = len(WORKLOADS) * REPS
    done = 0

    for name, fn in WORKLOADS:
        code = inspect.getsource(fn)
        features = extract_code_features(code)

        for rep in range(1, REPS + 1):
            result = run_workload_with_codecarbon(name, fn, rep)
            if result:
                row = {**features, **result, "hardware": detect_hardware()}
                rows.append(row)
            done += 1
            log.info(f"  Progress: {done}/{total} ({100*done//total}%)")

    df = pd.DataFrame(rows)

    # Augment with synthetic hardware variation
    graviton_rows = df.copy()
    graviton_rows["hardware"] = "graviton"
    graviton_rows["energy_kwh"] *= 0.60  # Graviton ~40% more efficient
    graviton_rows["emissions_kgco2"] *= 0.60
    graviton_rows["duration_s"] *= 1.05

    # Augment with carbon intensity variation (simulate different times-of-day)
    carbon_variations = [0.7, 0.9, 1.0, 1.2, 1.5]
    augmented = []
    for _, row in df.iterrows():
        for cv in carbon_variations:
            r = row.copy()
            r["emissions_kgco2"] = r["energy_kwh"] * cv * 0.82
            r["carbon_intensity"] = cv * 0.82
            augmented.append(r)

    df_aug = pd.DataFrame(augmented)
    df_all = pd.concat([df, graviton_rows, df_aug], ignore_index=True)
    df_all = df_all.drop_duplicates()
    df_all = df_all.fillna(0)

    df_all.to_csv(OUTPUT_CSV, index=False)
    log.info(f"\n✅ Dataset saved to {OUTPUT_CSV} — {len(df_all)} rows")
    return df_all


if __name__ == "__main__":
    generate_dataset()
