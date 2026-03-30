import requests
from bs4 import BeautifulSoup

code = '''def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = fibonacci(10)
print(result)'''

response = requests.post('http://localhost:5000/analyze', data={
    'code': code,
    'hardware': 'x86',
    'carbon_intensity': '450',
    'latency': '50',
    'region': 'us-east-1'
})

html = response.text
soup = BeautifulSoup(html, 'html.parser')

# Elements that updateMetrics tries to access
required_elements = [
    'scoreValue',
    'scoreInterpretation',
    'energyValue', 
    'energyUnit',
    'locMetric',
    'complexityMetric',
    'carbonValue',
    'treeEquivalent',
    'carbonIntensity',
    'metric-loc',
    'metric-functions',
    'metric-loops',
    'metric-patterns',
    'cpu-percent',
    'cpu-bar',
    'ram-percent', 
    'ram-bar',
    'gpu-percent',
    'gpu-bar',
    'contextHardware',
    'contextCarbon',
    'contextLatency',
    'contextRegion',
    'mainSuggestion',
    'quickWinsList',
    'scoreChart',
    'energyChart',
    'carbonChart'
]

print("=" * 60)
print("CHECKING FOR REQUIRED DOM ELEMENTS")
print("=" * 60)

missing = []
found = []

for elem_id in required_elements:
    elem = soup.find(id=elem_id)
    if elem:
        found.append(elem_id)
        print(f"✓ {elem_id}")
    else:
        missing.append(elem_id)
        print(f"✗ {elem_id} - MISSING")

print("\n" + "=" * 60)
print(f"SUMMARY: {len(found)} found, {len(missing)} missing")
print("=" * 60)

if missing:
    print("\nMissing elements that updateMetrics needs:")
    for elem in missing:
        print(f"  - {elem}")
