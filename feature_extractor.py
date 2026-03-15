import libcst as cst
import numpy as np

class FeatureExtractor:
    def extract_features(self, code: str):
        try:
            tree = cst.parse_module(code)
        except:
            return np.zeros(20)  # fallback if parsing fails

        features = {
            'num_loops': code.count('for ') + code.count('while '),
            'num_list_comp': code.count('[ ]') + code.count('for ') if '[' in code else 0,
            'num_numpy_calls': code.count('np.') + code.count('numpy.'),
            'num_pandas_calls': code.count('pd.'),
            'num_async': code.count('async def') + code.count('await '),
            'num_dicts': code.count('dict(') + code.count('{'),
            'num_deep_copies': code.count('copy.deepcopy'),
            'code_length': len(code),
            'num_lines': len(code.splitlines()),
            'has_io': 1 if any(x in code.lower() for x in ['open(', 'read(', 'write(', 'requests.']) else 0,
            'has_ml': 1 if any(x in code.lower() for x in ['sklearn', 'tensorflow', 'torch', 'xgboost']) else 0,
            'complexity_score': len(code.splitlines()) * 1.5,  # proxy for hot-paths
        }

        # Convert to array (20 features)
        return np.array(list(features.values()) + [0]*5)  # pad to 20 for consistency