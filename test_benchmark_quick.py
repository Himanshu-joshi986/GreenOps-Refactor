#!/usr/bin/env python
"""Test the benchmark integration"""
import sys
import os

# Ensure we're in the right directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from benchmark import benchmark_code

print("\n" + "="*70)
print("GREENOPS BENCHMARK INTEGRATION TEST")
print("="*70 + "\n")

# Test 1: Simple loop code
test_code_1 = """
def sum_numbers(n):
    total = 0
    for i in range(n):
        total += i
    return total

result = sum_numbers(100)
print(result)
"""

context_1 = {
    'hardware': 'x86',
    'carbon_intensity': 450,
    'latency_ms': 50,
    'region': 'us-east-1'
}

print("Test 1: Simple Loop Code")
print("-" * 70)
result_1 = benchmark_code(test_code_1, context_1)

if result_1:
    print(f"✓ Green Score:     {result_1['green_score']}/100")
    print(f"✓ Energy:          {result_1['predicted_energy_kwh']:.8f} kWh")
    print(f"✓ Carbon Impact:   {result_1['carbon_grams']:.3f}g CO2")
    print(f"✓ Suggestion:      {result_1['suggested_refactor']}")
    print(f"✓ Tree Equivalents:{result_1['tree_equivalents']:.2f}")
    print(f"✓ Code Metrics:    LOC={result_1['code_metrics']['lines_of_code']}, "
          f"Complexity={result_1['code_metrics']['complexity_score']}")
else:
    print("✗ FAILED - No result returned")

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70 + "\n")
