"""
GreenOps Refactor — feature_extractor.py
Uses libcst + ast to extract energy-relevant code features.
"""

import ast
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger("feature_extractor")

try:
    import libcst as cst
    HAS_LIBCST = True
except ImportError:
    HAS_LIBCST = False
    log.warning("libcst not available; falling back to ast-only extraction")


# ─────────────────────────────────────────────
# Result dataclass
# ─────────────────────────────────────────────
@dataclass
class CodeFeatures:
    # Structure
    loc: int = 0
    blank_lines: int = 0
    comment_lines: int = 0
    num_functions: int = 0
    num_classes: int = 0
    num_imports: int = 0

    # Loops & comprehensions
    num_loops: int = 0
    nested_loops: int = 0
    list_comprehensions: int = 0
    generator_expressions: int = 0
    dict_comprehensions: int = 0

    # Control flow
    try_except_blocks: int = 0
    has_recursion: int = 0
    conditional_branches: int = 0

    # I/O & side effects
    io_operations: int = 0
    print_calls: int = 0
    network_calls: int = 0

    # Library usage
    uses_numpy: int = 0
    uses_pandas: int = 0
    uses_sklearn: int = 0
    uses_asyncio: int = 0
    uses_threading: int = 0

    # Complexity proxies
    max_depth: int = 0
    avg_function_length: float = 0.0
    global_vars: int = 0
    lambda_count: int = 0

    # Docstrings (module/class/function) — not counted as # comments; inflate LOC without execution cost
    docstring_lines: int = 0

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}

    def to_model_features(self) -> dict:
        """Features for the energy regressor (aligned with training preprocess)."""
        logical_loc = max(1, self.loc - int(self.comment_lines) - int(self.docstring_lines))
        return {
            "loc": logical_loc,
            "blank_lines": self.blank_lines,
            "comment_lines": self.comment_lines,
            "num_functions": self.num_functions,
            "num_classes": self.num_classes,
            "num_loops": self.num_loops,
            "nested_loops": self.nested_loops,
            "list_comprehensions": self.list_comprehensions,
            "num_imports": self.num_imports,
            "try_except_blocks": self.try_except_blocks,
            "has_recursion": self.has_recursion,
            "io_operations": self.io_operations,
            "uses_numpy": self.uses_numpy,
            "uses_pandas": self.uses_pandas,
        }


# ─────────────────────────────────────────────
# libcst visitor (rich analysis)
# ─────────────────────────────────────────────
if HAS_LIBCST:
    class EnergyVisitor(cst.CSTVisitor):
        def __init__(self):
            self.functions: list[str] = []
            self.classes = 0
            self.imports = 0
            self.loops = 0
            self.list_comps = 0
            self.gen_exps = 0
            self.dict_comps = 0
            self.try_blocks = 0
            self.lambdas = 0
            self.calls: list[str] = []
            self._depth = 0
            self._max_depth = 0
            self._loop_depth = 0
            self._max_loop_depth = 0
            self._current_function: Optional[str] = None
            self._function_lines: dict[str, int] = {}

        def visit_FunctionDef(self, node: cst.FunctionDef):
            name = node.name.value
            self.functions.append(name)
            self._current_function = name
            self._depth += 1
            self._max_depth = max(self._max_depth, self._depth)

        def leave_FunctionDef(self, node: cst.FunctionDef):
            self._depth -= 1

        def visit_ClassDef(self, node: cst.ClassDef):
            self.classes += 1

        def visit_Import(self, node: cst.Import):
            self.imports += 1

        def visit_ImportFrom(self, node: cst.ImportFrom):
            self.imports += 1

        def visit_For(self, node: cst.For):
            self.loops += 1
            self._loop_depth += 1
            self._max_loop_depth = max(self._max_loop_depth, self._loop_depth)

        def leave_For(self, node: cst.For):
            self._loop_depth -= 1

        def visit_While(self, node: cst.While):
            self.loops += 1

        def visit_ListComp(self, node: cst.ListComp):
            self.list_comps += 1

        def visit_GeneratorExp(self, node: cst.GeneratorExp):
            self.gen_exps += 1

        def visit_DictComp(self, node: cst.DictComp):
            self.dict_comps += 1

        def visit_Try(self, node: cst.Try):
            self.try_blocks += 1

        def visit_Lambda(self, node: cst.Lambda):
            self.lambdas += 1

        def visit_Call(self, node: cst.Call):
            if isinstance(node.func, cst.Name):
                self.calls.append(node.func.value)
            elif isinstance(node.func, cst.Attribute):
                if isinstance(node.func.value, cst.Name):
                    self.calls.append(f"{node.func.value.value}.{node.func.attr.value}")


# ─────────────────────────────────────────────
# Main extractor class
# ─────────────────────────────────────────────
def _count_docstring_lines(code: str) -> int:
    """Lines occupied by module/class/function docstrings (AST-level, not # comments)."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return 0

    def lines_in_first_docstring(body: list) -> int:
        if not body:
            return 0
        first = body[0]
        if not isinstance(first, ast.Expr):
            return 0
        val = first.value
        if isinstance(val, ast.Constant) and isinstance(val.value, str):
            text = val.value
        else:
            return 0
        return text.count("\n") + 1

    n = lines_in_first_docstring(tree.body)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            n += lines_in_first_docstring(node.body)
    return n


class FeatureExtractor:
    IO_BUILTINS = {"open", "read", "write", "readline", "readlines", "close", "flush"}
    NETWORK_CALLS = {"requests.get", "requests.post", "requests.put", "requests.delete",
                     "httpx.get", "httpx.post", "urlopen", "socket.connect", "aiohttp"}

    def __init__(self, code: str):
        self.code = code
        self.lines = code.split("\n")

    def extract(self) -> CodeFeatures:
        features = CodeFeatures()

        # Line-level stats
        features.loc = len(self.lines)
        features.blank_lines = sum(1 for l in self.lines if not l.strip())
        features.comment_lines = sum(1 for l in self.lines if l.strip().startswith("#"))
        features.docstring_lines = _count_docstring_lines(self.code)

        # Library detection from raw source
        features.uses_numpy = int("numpy" in self.code or "import np" in self.code or "np." in self.code)
        features.uses_pandas = int("pandas" in self.code or "import pd" in self.code or "pd." in self.code)
        features.uses_sklearn = int("sklearn" in self.code or "from sklearn" in self.code)
        features.uses_asyncio = int("asyncio" in self.code or "async def" in self.code)
        features.uses_threading = int("threading" in self.code or "concurrent" in self.code)

        if HAS_LIBCST:
            self._extract_libcst(features)
        else:
            self._extract_ast(features)

        return features

    def _extract_libcst(self, features: CodeFeatures):
        try:
            tree = cst.parse_module(self.code)
            visitor = EnergyVisitor()
            tree.walk(visitor)

            features.num_functions = len(visitor.functions)
            features.num_classes = visitor.classes
            features.num_imports = visitor.imports
            features.num_loops = visitor.loops
            features.nested_loops = max(0, visitor._max_loop_depth - 1)
            features.list_comprehensions = visitor.list_comps
            features.generator_expressions = visitor.gen_exps
            features.dict_comprehensions = visitor.dict_comps
            features.try_except_blocks = visitor.try_blocks
            features.lambda_count = visitor.lambdas
            features.max_depth = visitor._max_depth

            # Recursion detection
            func_names = set(visitor.functions)
            features.has_recursion = int(any(c in func_names for c in visitor.calls))

            # I/O detection
            features.io_operations = sum(1 for c in visitor.calls if c in self.IO_BUILTINS)
            features.network_calls = sum(1 for c in visitor.calls if c in self.NETWORK_CALLS)
            features.print_calls = visitor.calls.count("print")

        except Exception as e:
            log.warning(f"libcst extraction failed: {e}, falling back to ast")
            self._extract_ast(features)

    def _extract_ast(self, features: CodeFeatures):
        try:
            tree = ast.parse(self.code)
        except SyntaxError as e:
            log.error(f"Syntax error in code: {e}")
            return

        func_names = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_names.add(node.name)
                features.num_functions += 1
            elif isinstance(node, ast.AsyncFunctionDef):
                func_names.add(node.name)
                features.num_functions += 1
            elif isinstance(node, ast.ClassDef):
                features.num_classes += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                features.num_imports += 1
            elif isinstance(node, (ast.For, ast.While)):
                features.num_loops += 1
            elif isinstance(node, ast.ListComp):
                features.list_comprehensions += 1
            elif isinstance(node, ast.GeneratorExp):
                features.generator_expressions += 1
            elif isinstance(node, ast.DictComp):
                features.dict_comprehensions += 1
            elif isinstance(node, ast.Try):
                features.try_except_blocks += 1
            elif isinstance(node, ast.Lambda):
                features.lambda_count += 1
            elif isinstance(node, ast.If):
                features.conditional_branches += 1
            elif isinstance(node, ast.Global):
                features.global_vars += len(node.names)

        # Nested loop detection
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                for child in ast.walk(node):
                    if isinstance(child, (ast.For, ast.While)) and child is not node:
                        features.nested_loops += 1
                        break

        # Recursion detection
        calls = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.add(node.func.attr)
        features.has_recursion = int(bool(func_names & calls))

        # I/O detection
        io_names = {"open", "read", "write", "readline"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                    if name in io_names:
                        features.io_operations += 1
                    elif name == "print":
                        features.print_calls += 1


# ─────────────────────────────────────────────
# Convenience function
# ─────────────────────────────────────────────
def extract_features(code: str) -> CodeFeatures:
    return FeatureExtractor(code).extract()


# ─────────────────────────────────────────────
# Quick test
# ─────────────────────────────────────────────
if __name__ == "__main__":
    sample = """
import numpy as np
import pandas as pd

def process_data(records):
    results = []
    for record in records:
        for item in record['items']:
            try:
                result = np.sqrt(item['value'])
                results.append(result)
            except Exception as e:
                print(f"Error: {e}")
    return results

class DataProcessor:
    def __init__(self):
        self.cache = {}
    
    def compute(self, data):
        return [x**2 for x in data if x > 0]
"""
    features = extract_features(sample)
    print("Extracted Features:")
    for k, v in features.to_dict().items():
        print(f"  {k}: {v}")
    print("\nModel Features:")
    print(features.to_model_features())
