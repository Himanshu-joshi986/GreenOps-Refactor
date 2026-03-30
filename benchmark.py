import joblib
import pandas as pd
import numpy as np
import os
import logging
from feature_extractor import FeatureExtractor
from context_integrator import get_context_factors

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the trained model once  
MODEL_PATH = 'energy_predictor.pkl'
model = None
model_loaded = False

def load_model():
    """Load the trained model"""
    global model, model_loaded
    if model_loaded:
        return model
    
    if os.path.exists(MODEL_PATH):
        try:
            model = joblib.load(MODEL_PATH)
            model_loaded = True
            logger.info(f"✓ Model successfully loaded from {MODEL_PATH}")
            return model
        except Exception as e:
            logger.error(f"✗ Error loading model: {e}")
            model_loaded = True
            model = None
            return None
    else:
        logger.warning(f"⚠ Model file {MODEL_PATH} not found - using fallback mode")
        model_loaded = True
        return None

def map_code_features_to_energy_features(code_features: dict, context_factors: dict) -> dict:
    """
    Map code analysis features to energy/hardware features for model prediction.
    Creates consistent, normalized features for XGBoost model.
    """
    
    # Extract code metrics with safe defaults
    num_lines = max(0, code_features.get('num_lines', 0))
    num_loops = max(0, code_features.get('num_loops', 0))
    num_async = max(0, code_features.get('num_async', 0))
    num_numpy = max(0, code_features.get('num_numpy_calls', 0))
    num_pandas = max(0, code_features.get('num_pandas_calls', 0)) 
    complexity = max(0, min(100, code_features.get('complexity_score', 0)))
    code_length = max(0, code_features.get('code_length', 0))
    
    has_loops = num_loops > 0
    has_ml = code_features.get('has_ml', 0) == 1
    has_io = code_features.get('has_io', 0) == 1
    
    # Execution duration estimation (seconds)
    base_duration = max(0.001, min(100, 0.05 + (num_lines * 0.002)))
    
    # Duration adjustments based on code patterns
    duration_multiplier = 1.0
    if num_loops > 0:
        duration_multiplier *= (1.0 + num_loops * 0.1)
    if has_ml:
        duration_multiplier *= 3.0
    if num_async > 0:
        duration_multiplier *= 0.6
    if num_numpy > 0 or num_pandas > 0:
        duration_multiplier *= 0.8
    
    execution_time_seconds = base_duration * duration_multiplier
    
    # Hardware configuration
    cpu_count = 2 + (num_pandas * 0.5)
    
    # Power draw estimation (Watts)
    base_cpu_power = 8.0 + (complexity * 0.2)
    graviton_factor = context_factors.get('graviton_factor', 1.0)
    cpu_power = base_cpu_power * graviton_factor
    cpu_power = max(3.0, min(60.0, cpu_power))
    
    gpu_power = 12.0 if has_ml else 0.0
    ram_power = 4.0
    
    # Energy consumption (kWh)
    total_power_watts = cpu_power + gpu_power + ram_power
    energy_consumed_kwh = (total_power_watts / 1000.0) * (execution_time_seconds / 3600.0)
    energy_consumed_kwh = max(0.0, energy_consumed_kwh)
    
    # Component energy breakdown
    cpu_energy_kwh = (cpu_power / 1000.0) * (execution_time_seconds / 3600.0)
    gpu_energy_kwh = (gpu_power / 1000.0) * (execution_time_seconds / 3600.0)
    ram_energy_kwh = (ram_power / 1000.0) * (execution_time_seconds / 3600.0)
    
    # Resource utilization (0-100%)
    if num_async > 0:
        cpu_utilization = min(60, 25 + (complexity * 0.3))
    elif has_loops:
        cpu_utilization = min(90, 35 + (num_loops * 8) + (complexity * 0.4))
    else:
        cpu_utilization = min(75, 25 + complexity)
    
    gpu_utilization = 50.0 if has_ml else 0.0
    ram_utilization = 25.0 + (num_pandas * 15.0) + (code_length / 100000.0 * 10)
    ram_utilization = min(90.0, ram_utilization)
    
    # Memory configuration
    ram_total_size = 4.0 + (4.0 if has_ml else 0.0)
    ram_used_gb = (ram_utilization / 100.0) * ram_total_size
    
    # I/O latency impact
    latency_penalty = context_factors.get('latency_penalty', 1.0)
    latency_adjusted_power = cpu_power * (1.0 + (latency_penalty - 1.0) * 0.15)
    
    # Emissions rate  
    carbon_intensity = context_factors.get('carbon_intensity', 450)
    emissions_rate = carbon_intensity
    
    # Water consumption estimate
    water_consumed = energy_consumed_kwh * 0.6
    
    # Compose feature dict that will be passed to model
    features = {
        'duration': execution_time_seconds,
        'emissions_rate': emissions_rate,
        'cpu_power': cpu_power,
        'gpu_power': gpu_power,
        'ram_power': ram_power,
        'cpu_energy': cpu_energy_kwh,
        'gpu_energy': gpu_energy_kwh,
        'ram_energy': ram_energy_kwh,
        'energy_consumed': energy_consumed_kwh,
        'water_consumed': water_consumed,
        'cpu_count': float(cpu_count),
        'gpu_count': 1.0 if has_ml else 0.0,
        'ram_total_size': ram_total_size,
        'cpu_utilization_percent': cpu_utilization,
        'gpu_utilization_percent': gpu_utilization,
        'ram_utilization_percent': ram_utilization,
        'ram_used_gb': ram_used_gb,
    }
    
    return features

def benchmark_code(code_snippet: str, context: dict):
    """
    Analyze code for energy efficiency using real model + code analysis + context.
    
    Args:
        code_snippet: Python code to analyze
        context: Dictionary with hardware, carbon_intensity, latency_ms, region
    
    Returns:
        Dictionary with comprehensive analysis results or None on error
    """
    try:
        # Load model (may return None if not available)
        model_instance = load_model()
        
        # Extract real code features using libcst
        extractor = FeatureExtractor()
        code_features = extractor.extract_features(code_snippet)
        
        # Get context factors (hardware, carbon, latency, region)
        context_factors = get_context_factors(context)
        
        # Map to energy features
        energy_features = map_code_features_to_energy_features(code_features, context_factors)
        
        # Make prediction
        if model_instance is not None:
            df = pd.DataFrame([energy_features])
            predicted_energy_kwh = float(model_instance.predict(df)[0])
            predicted_energy_kwh = max(0.0, predicted_energy_kwh)
            logger.info(f"✓ Model prediction: {predicted_energy_kwh:.6f} kWh")
        else:
            # Fallback calculation using energy_features directly
            predicted_energy_kwh = energy_features.get('energy_consumed', 0.0)
            logger.warning(f"⚠ Using fallback energy calculation: {predicted_energy_kwh:.6f} kWh")
        
        # Calculate green score
        green_score = calculate_green_score(code_features, context_factors, predicted_energy_kwh)
        
        # Generate refactoring suggestions
        suggestion = generate_suggestion(code_features, context_factors)
        quick_wins = generate_quick_wins(code_features, context_factors)
        
        # Calculate carbon footprint
        carbon_intensity = context_factors.get('carbon_intensity', 450)
        carbon_grams = predicted_energy_kwh * carbon_intensity
        
        # Calculate tree equivalents (1 tree = ~20kg CO2/year = 54.79g/day)
        tree_equivalents = carbon_grams / 54.79 * 365 / 1000
        
        # Build comprehensive result dictionary
        result = {
            'green_score': round(green_score, 1),
            'predicted_energy_kwh': round(predicted_energy_kwh, 8),
            'predicted_energy_mwh': round(predicted_energy_kwh * 1000000, 2),
            'suggested_refactor': suggestion,
            'quick_wins': quick_wins,
            'carbon_grams': round(carbon_grams, 3),
            'carbon_kg': round(carbon_grams / 1000, 6),
            'tree_equivalents': round(tree_equivalents, 2),
            'context_used': {
                'hardware': context.get('hardware', 'x86'),
                'carbon_intensity': carbon_intensity,
                'latency_ms': context.get('latency_ms', 50),
                'region': context.get('region', 'unknown')
            },
            'code_metrics': {
                'lines_of_code': code_features.get('num_lines', 0),
                'complexity_score': round(code_features.get('complexity_score', 0), 2),
                'num_loops': code_features.get('num_loops', 0),
                'num_functions': code_features.get('num_functions', 0),
                'has_async': bool(code_features.get('num_async', 0)),
                'has_ml': bool(code_features.get('has_ml', 0)),
                'has_io': bool(code_features.get('has_io', 0))
            },
            'energy_breakdown': {
                'cpu_energy_kwh': round(energy_features['cpu_energy'], 8),
                'gpu_energy_kwh': round(energy_features['gpu_energy'], 8),
                'ram_energy_kwh': round(energy_features['ram_energy'], 8)
            },
            'hardware_utilization': {
                'cpu_percent': round(energy_features['cpu_utilization_percent'], 1),
                'gpu_percent': round(energy_features['gpu_utilization_percent'], 1),
                'ram_percent': round(energy_features['ram_utilization_percent'], 1)
            }
        }
        
        logger.info(f"✓ Analysis complete: Score={result['green_score']}, Energy={result['predicted_energy_kwh']:.6f} kWh")
        return result
        
    except Exception as e:
        logger.error(f"✗ Benchmark error: {e}", exc_info=True)
        return None

def calculate_green_score(code_features: dict, context_factors: dict, predicted_energy: float) -> float:
    """
    Calculate green score (0-100) based on code characteristics and energy prediction.
    Higher score = more efficient code.
    """
    score = 100.0
    
    # Complexity penalty (5-20 points)
    complexity = code_features.get('complexity_score', 0)
    score -= min(20, complexity * 0.25)
    
    # Loop penalty if not vectorized (15 points max)
    loops = code_features.get('num_loops', 0)
    numpy_calls = code_features.get('num_numpy_calls', 0)
    if loops > 2 and numpy_calls == 0 and code_features.get('num_pandas_calls', 0) == 0:
        score -= 15
    
    # Async/await bonus (+8 points)
    if code_features.get('num_async', 0) > 0:
        score += 8
    
    # List comprehension bonus (+5 points)
    if code_features.get('num_list_comp', 0) > 0:
        score += 5
    
    # I/O operations penalty (-10 points)
    if code_features.get('has_io', 0):
        score -= 10
    
    # ML operations penalty (-8 points, but add back if quantization hints exist)
    if code_features.get('has_ml', 0):
        score -= 8
    
    # Latency impact (-5 to -15 points)
    latency_norm = context_factors.get('latency_normalized', 0)
    score -= latency_norm * 15
    
    # Energy-based penalty (0-10 points for very high energy)
    if predicted_energy > 0.0001:
        energy_penalty = min(10, predicted_energy * 100000)
        score -= energy_penalty
    
    # Clamp to 0-100
    return max(0.0, min(100.0, score))

def generate_suggestion(code_features: dict, context_factors: dict) -> str:
    """
    Generate main optimization suggestion based on code analysis and context.
    """
    
    # Hardware-specific suggestions
    if context_factors.get('hardware_graviton', 0) == 1.0:
        loops = code_features.get('num_loops', 0)
        numpy_calls = code_features.get('num_numpy_calls', 0)
        if loops > 3 and numpy_calls == 0:
            return "Switch to NumPy vectorization - saves ~50% energy on Graviton ARM architecture"
    
    # Async/await for I/O operations
    if context_factors.get('latency_ms', 0) > 60:
        if code_features.get('has_io', 0) == 1 and code_features.get('num_async', 0) == 0:
            return "Convert I/O operations to async/await - reduce latency and energy waste"
    
    # Loop optimization
    loops = code_features.get('num_loops', 0)
    if loops > 2:
        if code_features.get('num_list_comp', 0) == 0:
            return "Replace for-loops with list comprehensions - 15-20% energy reduction"
    
    # Pandas vectorization
    if code_features.get('num_pandas_calls', 0) > 0:
        return "Use vectorized Pandas operations instead of iterrows() - 30-40% energy savings"
    
    # ML model optimization
    if code_features.get('has_ml', 0) == 1:
        if code_features.get('num_lines', 0) > 100:
            return "Consider model quantization or distillation - energy-efficient inference"
    
    # General refactoring
    if code_features.get('complexity_score', 0) > 50:
        return "Refactor complex logic into smaller functions - improves clarity and efficiency"
    
    return "Code is well-optimized! Profile at runtime for further micro-optimizations"

def generate_quick_wins(code_features: dict, context_factors: dict) -> list:
    """Generate list of quick optimization opportunities."""
    wins = []
    
    # Check for common inefficiencies
    if code_features.get('num_loops', 0) > 2:
        wins.append("Use list comprehensions instead of for loops")
    
    if code_features.get('has_io', 0):
        wins.append("Add connection pooling for I/O operations")
    
    if code_features.get('num_pandas_calls', 0) > 0:
        wins.append("Vectorize Pandas operations")
    
    if code_features.get('num_async', 0) == 0 and code_features.get('has_io', 0):
        wins.append("Implement async/await for I/O")
    
    if code_features.get('has_ml', 0):
        wins.append("Consider batch processing for ML inference")
    
    if code_features.get('complexity_score', 0) > 50:
        wins.append("Break down complex functions")
    
    return wins if wins else ["Profile code for specific bottlenecks"]
