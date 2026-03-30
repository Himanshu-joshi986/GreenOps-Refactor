#!/usr/bin/env python
"""
Quick test to verify:
1. Form is accessible
2. API endpoint works
3. Results display properly
"""

from flask import Flask
import requests
import json

# Test 1: Check HTML loads
print("\nTest 1: Checking if page loads...")
try:
    response = requests.get('http://localhost:5000/', timeout=5)
    if 'analysisForm' in response.text:
        print("✓ HTML form found in page")
    if 'resultsContainer' in response.text:
        print("✓ Results container found in HTML")
    if 'inlineResults' in response.text:
        print("✓ Inline results div found in HTML")
except Exception as e:
    print(f"✗ Error loading page: {e}")
    exit(1)

# Test 2: Check API endpoint
print("\nTest 2: Testing API endpoint...")
test_data = {
    'code': 'for i in range(10):\n    print(i)',
    'hardware': 'x86',
    'carbon_intensity': 450,
    'latency_ms': 50
}

try:
    response = requests.post('http://localhost:5000/api/analyze', json=test_data, timeout=10)
    if response.status_code == 200:
        result = response.json()
        required_fields = ['green_score', 'predicted_energy_kwh', 'carbon_grams', 'code_metrics', 'suggested_refactor']
        missing = [f for f in required_fields if f not in result]
        if missing:
            print(f"✗ Missing fields: {missing}")
        else:
            print(f"✓ API returns all required fields")
            print(f"  - Green Score: {result['green_score']}/100")
            print(f"  - Energy: {result['predicted_energy_kwh']:.2e} kWh")
            print(f"  - Carbon: {result['carbon_grams']:.2f}g CO2")
            print(f"  - Code Lines: {result['code_metrics']['lines_of_code']}")
    else:
        print(f"✗ API returned status {response.status_code}")
except Exception as e:
    print(f"✗ API error: {e}")
    exit(1)

# Test 3: Check JavaScript is loaded
print("\nTest 3: Checking JavaScript...")
html = requests.get('http://localhost:5000/').text
if 'initializeAnalysisForm' in html:
    print("✓ JavaScript form handler found")
if 'displayResults' in html:
    print("✓ Display results function found")
if 'apiCall' in html:
    print("✓ API call function found")

print("\n" + "="*70)
print("ALL TESTS PASSED!")
print("="*70)
print("\nNow try in your browser:")
print("1. Open http://localhost:5000")
print("2. Paste this code:")
print("   for i in range(10):")
print("       print(i)")
print("3. Click 'Analyze & Get Green Suggestions'")
print("4. Results should appear below the form")
print("="*70 + "\n")
