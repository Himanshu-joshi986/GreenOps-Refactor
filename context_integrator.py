import requests
import os

def get_context_factors(context: dict):
    """Get context-based factors and return them as features"""
    factors = {}
    
    # Hardware factor (real AWS Graviton savings vs x86)
    hardware = context.get('hardware', 'x86').lower()
    factors['hardware_x86'] = 1.0 if hardware == 'x86' else 0.0
    factors['hardware_graviton'] = 1.0 if hardware == 'graviton' else 0.0
    factors['hardware_arm'] = 1.0 if hardware == 'arm' else 0.0
    factors['graviton_factor'] = 0.4 if hardware == 'graviton' else 1.0
    
    # Carbon intensity (real API or fallback)
    carbon_intensity = context.get('carbon_intensity', 450)
    try:
        resp = requests.get(
            "https://api.electricitymaps.com/v3/carbon-intensity/latest?zone=IN-MH",
            timeout=5,
            headers={"auth-token": os.getenv("ELECTRICITYMAPS_API_KEY", "")}
        )
        if resp.status_code == 200:
            carbon_intensity = resp.json().get('carbonIntensity', carbon_intensity)
    except Exception as e:
        print(f"Carbon intensity API unavailable: {e}, using default")
    
    factors['carbon_intensity'] = carbon_intensity
    factors['carbon_intensity_normalized'] = min(carbon_intensity / 1000.0, 1.0)  # normalize to 0-1
    
    # Latency penalty (higher latency = worse for energy)
    latency_ms = context.get('latency_ms', 50)
    factors['latency_ms'] = latency_ms
    factors['latency_penalty'] = 1.0 + (latency_ms / 1000.0)
    factors['latency_normalized'] = min(latency_ms / 200.0, 1.0)  # normalize with 200ms as ceiling
    
    # Add deployment region factor
    region = context.get('region', 'us-east-1')
    factors['region_us'] = 1.0 if 'us' in region.lower() else 0.0
    factors['region_eu'] = 1.0 if 'eu' in region.lower() else 0.0
    factors['region_asia'] = 1.0 if 'asia' in region.lower() or 'ap' in region.lower() else 0.0
    
    return factors