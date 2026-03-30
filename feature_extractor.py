import libcst as cst
import numpy as np

class FeatureExtractor:
    def extract_features(self, code: str):
        """Extract features from code as a dictionary"""
        try:
            tree = cst.parse_module(code)
        except:
            # Return default features dict if parsing fails
            return self._get_default_features()

        # Count various code patterns
        lines = code.splitlines()
        num_lines = len(lines)
        code_length = len(code)
        
        features = {
            'num_loops': code.count('for ') + code.count('while '),
            'num_list_comp': code.count('[') + code.count('for '),
            'num_numpy_calls': code.count('np.') + code.count('numpy.'),
            'num_pandas_calls': code.count('pd.') + code.count('pandas.'),
            'num_async': code.count('async def') + code.count('await '),
            'num_dicts': code.count('dict(') + code.count('{'),
            'num_deep_copies': code.count('copy.deepcopy') + code.count('deepcopy'),
            'code_length': code_length,
            'num_lines': num_lines,
            'has_io': 1 if any(x in code.lower() for x in ['open(', 'read(', 'write(', 'requests.', 'urllib']) else 0,
            'has_ml': 1 if any(x in code.lower() for x in ['sklearn', 'tensorflow', 'torch', 'xgboost']) else 0,
            'complexity_score': min(num_lines * 1.5, 100),  # normalized complexity
            'num_functions': code.count('def '),
            'num_classes': code.count('class '),
            'has_recursion': 1 if any(name in code for name in ['recursive', 'self.']) and 'def ' in code else 0,
            'has_io_ops': 1 if 'file' in code.lower() or 'stream' in code.lower() else 0,
            'avg_line_length': code_length / max(num_lines, 1),
        }

        return features

    def _get_default_features(self):
        """Return default features when parsing fails"""
        return {
            'num_loops': 0,
            'num_list_comp': 0,
            'num_numpy_calls': 0,
            'num_pandas_calls': 0,
            'num_async': 0,
            'num_dicts': 0,
            'num_deep_copies': 0,
            'code_length': 0,
            'num_lines': 0,
            'has_io': 0,
            'has_ml': 0,
            'complexity_score': 0,
            'num_functions': 0,
            'num_classes': 0,
            'has_recursion': 0,
            'has_io_ops': 0,
            'avg_line_length': 0,
        }