#!/usr/bin/env python
"""Test API results display"""

import requests
import json
import time

# Make sure Flask is running
try:
    response = requests.get('http://localhost:5000/', timeout=2)
except:
    print("ERROR: Flask server not running on localhost:5000")
    print("Start it with: python app.py")
    exit(1)

print("\n" + "="*70)
print("TESTING API ENDPOINT - Results Display")
print("="*70 + "\n")

test_cases = [
    {
        'name': 'Simple Loop',
        'code': 'for i in range(10):\n    print(i)',
        'hardware': 'x86',
        'carbon_intensity': 450,
        'latency_ms': 50
    },
    {
        'name': 'Multiline Code with Indentation',
        'code': 'def calculate_total(items):\n    total = 0\n    for item in items:\n        total += item["price"]\n    return total',
        'hardware': 'graviton',
        'carbon_intensity': 250,
        'latency_ms': 100
    }
]

for i, test in enumerate(test_cases, 1):
    print(f"Test {i}: {test['name']}")
    print("-" * 70)
    
    data = {
        'code': test['code'],
        'hardware': test['hardware'],
        'carbon_intensity': test['carbon_intensity'],
        'latency_ms': test['latency_ms']
    }
    
    try:
        response = requests.post('http://localhost:5000/api/analyze', json=data, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n[SUCCESS] Analysis returned:")
            print(f"  - Green Score: {result.get('green_score', 'N/A')}/100")
            print(f"  - Energy: {result.get('predicted_energy_kwh', 'N/A'):.2e} kWh")
            print(f"  - Carbon: {result.get('carbon_grams', 'N/A'):.2f}g CO2")
            print(f"  - Lines: {result.get('code_metrics', {}).get('lines_of_code', 'N/A')}")
            print(f"  - Complexity: {result.get('code_metrics', {}).get('complexity', 'N/A')}")
            print(f"  - Suggestion: {result.get('suggested_refactor', 'N/A')[:60]}...")
        else:
            print(f"[ERROR] Status {response.status_code}: {response.text[:200]}")
    
    except Exception as e:
        print(f"[ERROR] Request failed: {str(e)}")
    
    print()

print("="*70)
print("Test complete! Now try in browser:")
print("1. Go to http://localhost:5000")
print("2. Paste code in the textarea")
print("3. Click 'Analyze & Get Green Suggestions'")
print("4. Results should display below the form")
print("="*70 + "\n")
