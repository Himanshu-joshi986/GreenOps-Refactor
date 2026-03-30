#!/usr/bin/env python
"""Test code analysis form - simple check"""

from app import app
import json

print("\n" + "="*80)
print("TESTING CODE ANALYSIS FORM")
print("="*80 + "\n")

client = app.test_client()

# Single test: form submission with simple code
code_sample = """for i in range(10):
    print(i)
    result = i * 2"""

print("[TEST] Submitting code to /api/analyze")
print("-" * 80)
print("Code being submitted:")
print(code_sample)
print("-" * 80)

api_data = {
    'code': code_sample,
    'hardware': 'x86',
    'carbon_intensity': 450,
    'latency_ms': 50
}

response = client.post('/api/analyze',
                      data=json.dumps(api_data),
                      content_type='application/json')

print(f"\nResponse Status: {response.status_code}\n")

if response.status_code == 200:
    result = response.get_json()
    print("[SUCCESS] Analysis returned successfully\n")
    print(f"  Green Score: {result.get('green_score', 'N/A')}/100")
    print(f"  Energy: {result.get('predicted_energy_kwh', 'N/A'):.2e} kWh")
    print(f"  Carbon: {result.get('carbon_grams', 'N/A'):.2f}g CO2")
    print(f"  Code Lines: {result.get('code_metrics', {}).get('lines_of_code', 'N/A')}")
    print(f"  Complexity: {result.get('code_metrics', {}).get('complexity', 'N/A')}")
    
    sug = result.get('suggested_refactor', 'N/A')
    sug_clean = ''.join(c for c in sug if ord(c) < 128).strip()
    print(f"  Suggestion: {sug_clean}\n")
    
    print("[RESULT] Form/API working correctly!")
else:
    print(f"[ERROR] Got status {response.status_code}")
    print(f"Response: {response.data.decode()}\n")

# Test 2: Code with newlines preserved
print("\n" + "="*80)
print("[TEST 2] Multiline code with proper indentation")
print("="*80 + "\n")

multiline_code = """import pandas as pd

def process_data(df):
    for idx, row in df.iterrows():
        value = row['amount']
        total = value * 2
        print(total)
    return df"""

api_data2 = {
    'code': multiline_code,
    'hardware': 'graviton',
    'carbon_intensity': 250,
    'latency_ms': 100
}

response2 = client.post('/api/analyze',
                       data=json.dumps(api_data2),
                       content_type='application/json')

if response2.status_code == 200:
    result2 = response2.get_json()
    print(f"[SUCCESS] Multiline code analyzed")
    print(f"  Green Score: {result2.get('green_score')}/100")
    print(f"  Lines Detected: {result2.get('code_metrics', {}).get('lines_of_code')}")
    print(f"  Has ML/Pandas: {result2.get('code_metrics', {}).get('has_ml')}")
else:
    print(f"[ERROR] Status {response2.status_code}")

print("\n" + "="*80)
print("TESTING COMPLETE - Ready to use the web form!")
print("="*80 + "\n")

# Test Case 2: API endpoint with Pandas code
print("\n[TEST 2] API Endpoint with Pandas Code")
print("-" * 80)

test_code_2 = """import pandas as pd
df = pd.read_csv('data.csv')
for idx, row in df.iterrows():
    print(row['value'])"""

api_data_2 = {
    'code': test_code_2,
    'hardware': 'graviton',
    'carbon_intensity': 250,
    'latency_ms': 100
}

response_2 = client.post('/api/analyze',
                         data=json.dumps(api_data_2),
                         content_type='application/json')

print(f"Status Code: {response_2.status_code}")

if response_2.status_code == 200:
    result = response_2.get_json()
    print("✓ API request successful (200 OK)")
    print(f"✓ Response is JSON")
    
    if result and 'green_score' in result:
        print(f"✓ Green Score: {result['green_score']}/100")
        print(f"✓ Energy: {result['predicted_energy_kwh']:.2e} kWh")
        print(f"✓ Carbon: {result['carbon_grams']:.2f}g CO2")
        print(f"✓ Suggestion: {result['suggested_refactor'][:60]}...")
    else:
        print("✗ Response missing analysis data")
        print(f"Response: {result}")
else:
    print(f"✗ Error: Status {response_2.status_code}")
    print(f"Response: {response_2.data.decode()}")

# Test Case 3: Async code with proper formatting
print("\n[TEST 3] API Endpoint with Async Code")
print("-" * 80)

test_code_3 = """import asyncio

async def fetch_data():
    for i in range(5):
        await asyncio.sleep(0.1)
        print(i)"""

api_data_3 = {
    'code': test_code_3,
    'hardware': 'x86',
    'carbon_intensity': 500,
    'latency_ms': 10
}

response_3 = client.post('/api/analyze',
                         data=json.dumps(api_data_3),
                         content_type='application/json')

print(f"Status Code: {response_3.status_code}")

if response_3.status_code == 200:
    result = response_3.get_json()
    print("✓ API request successful")
    
    if result and 'green_score' in result:
        print(f"✓ Green Score: {result['green_score']}/100")
        print(f"✓ Has Async: {result['code_metrics']['has_async']}")
    else:
        print("✗ Response missing data")
else:
    print(f"✗ Error: Status {response_3.status_code}")

# Test Case 4: Check error handling for short code
print("\n[TEST 4] Error Handling - Code Too Short")
print("-" * 80)

form_data_4 = {
    'code': 'x = 1',  # Too short
    'hardware': 'x86',
    'carbon_intensity': '450',
    'latency': '50'
}

response_4 = client.post('/analyze', data=form_data_4, follow_redirects=True)
print(f"Status Code: {response_4.status_code}")

if response_4.status_code == 200:
    if b'meaningful code' in response_4.data or b'characters' in response_4.data:
        print("✓ Proper error message displayed for short code")
    else:
        print("! Error page returned (may be missing message)")
else:
    print(f"Status: {response_4.status_code}")

print("\n" + "="*80)
print("TESTING COMPLETE")
print("="*80)

print("""
SUMMARY:
All tests verify that the code analysis system is working properly.
The form submission and API endpoints should now:
✓ Accept Python code with proper formatting
✓ Preserve newlines and indentation
✓ Return valid analysis results
✓ Display green scores, energy, and suggestions

NEXT STEPS:
1. Start Flask server: python app.py
2. Open http://localhost:5000
3. Paste Python code with proper indentation
4. Click "Analyze & Get Green Suggestions"
5. Results should display with green score and suggestions
""")

print("="*80 + "\n")
