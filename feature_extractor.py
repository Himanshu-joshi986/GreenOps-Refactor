import libcst as cst
import ast
import numpy as np

class FeatureExtractor:
    def extract_features(self, code: str):
        # Use libcst for lossless parsing + rich features
        tree = cst.parse_module(code)
        
        # Basic features (expand this)
        features = {
            'num_loops': code.count('for ') + code.count('while '),
            'num_list_comp': code.count('[') + code.count('for ') if '[' in code else 0,
            'num_numpy_calls': code.count('np.') + code.count('numpy.'),
            'num_async': code.count('async def') + code.count('await '),
            'num_dicts': code.count('{}') + code.count('dict('),
            'code_length': len(code),
            'complexity_score': len(code.splitlines())  # simple proxy for hot-paths
        }
        
        # Return as numpy array for model
        return np.array(list(features.values()))

# Test it
if __name__ == "__main__":
    sample_code = "import numpy as np\narr = np.arange(1000000)\nprint(np.sum(arr))"
    extractor = FeatureExtractor()
    print(extractor.extract_features(sample_code))