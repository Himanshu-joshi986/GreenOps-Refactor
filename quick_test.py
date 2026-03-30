#!/usr/bin/env python
"""Quick test of analyze button - one pass to check everything"""

print("\n" + "="*70)
print("QUICK ANALYZE BUTTON TEST")
print("="*70 + "\n")

from benchmark import benchmark_code

# Test 1: Simple loop code
test_cases = [
    {
        'name': 'Simple Loop',
        'code': 'for i in range(10):\n    print(i)',
        'context': {'hardware': 'x86', 'carbon_intensity': 450, 'latency_ms': 50}
    },
    {
        'name': 'Pandas Operation',
        'code': 'import pandas as pd\ndf = pd.read_csv("data.csv")\nfor idx, row in df.iterrows():\n    print(row)',
        'context': {'hardware': 'graviton', 'carbon_intensity': 250, 'latency_ms': 100}
    },
    {
        'name': 'Async Code',
        'code': 'import asyncio\nasync def main():\n    for i in range(5):\n        await asyncio.sleep(1)\n        print(i)',
        'context': {'hardware': 'x86', 'carbon_intensity': 500, 'latency_ms': 10}
    }
]

all_passed = True

for i, test in enumerate(test_cases, 1):
    print(f"Test {i}: {test['name']}")
    print("-" * 70)
    
    result = benchmark_code(test['code'], test['context'])
    
    if result is None:
        print("  [FAIL] No result returned\n")
        all_passed = False
        continue
    
    # Check all required fields
    required = ['green_score', 'predicted_energy_kwh', 'suggested_refactor', 
                'carbon_grams', 'code_metrics']
    missing = [k for k in required if k not in result]
    
    if missing:
        print(f"  [FAIL] Missing fields: {missing}\n")
        all_passed = False
        continue
    
    # Display results
    print(f"  [OK] Green Score:    {result['green_score']}/100")
    print(f"  [OK] Energy:         {result['predicted_energy_kwh']:.2e} kWh")
    print(f"  [OK] Carbon Impact:  {result['carbon_grams']:.2f}g CO2")
    
    # Clean suggestion (remove emoji for console compatibility)
    suggestion = result['suggested_refactor']
    suggestion_clean = ''.join(c for c in suggestion if ord(c) < 128)
    print(f"  [OK] Suggestion:     {suggestion_clean.strip()}")
    
    print(f"  [OK] Code Metrics:   Lines={result['code_metrics']['lines_of_code']}, "
          f"Complexity={result['code_metrics']['complexity_score']}\n")

print("="*70)
if all_passed:
    print("[SUCCESS] ALL TESTS PASSED - ANALYZE BUTTON IS WORKING!")
    print("\nThe button will return:")
    print("  * Green Score (0-100) - How efficient the code is")
    print("  * Energy (kWh) - Predicted energy consumption")
    print("  * Carbon (grams) - CO2 emissions based on carbon intensity")
    print("  * Suggestion - Optimization recommendation")
else:
    print("[FAILED] SOME TESTS FAILED - Check errors above")
print("="*70 + "\n")
