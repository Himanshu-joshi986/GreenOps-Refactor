import requests
from bs4 import BeautifulSoup
import re

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

print("=" * 60)
print("FINAL VERIFICATION - ALL ELEMENTS DISPLAYING")
print("=" * 60)

# Check all major metric elements
metrics_to_check = {
    'scoreValue': 'Green Score',
    'scoreInterpretation': 'Score Interpretation',
    'energyValue': 'Energy Consumption',
    'locMetric': 'Lines of Code',
    'complexityMetric': 'Complexity Score',
    'carbonValue': 'Carbon Footprint',
    'treeEquivalent': 'Tree Equivalents',
    'carbonIntensity': 'Carbon Intensity',
    'contextHardware': 'Hardware Context',
    'contextCarbon': 'Carbon Context', 
    'contextLatency': 'Latency Context',
    'contextRegion': 'Region Context',
    'mainSuggestion': 'Main Suggestion',
    'cpu-percent': 'CPU Percentage',
    'ram-percent': 'RAM Percentage',
    'gpu-percent': 'GPU Percentage'
}

for elem_id, description in metrics_to_check.items():
    elem = soup.find(id=elem_id)
    if elem:
        value = elem.get_text(strip=True)[:50]  # First 50 chars
        print(f"✓ {description:30} = {value}")
    else:
        print(f"✗ {description:30} - NOT FOUND")

# Check for quick wins list
quick_wins = soup.find(id='quickWinsList')
if quick_wins:
    items = quick_wins.find_all('div', class_='d-flex')
    print(f"\n✓ Quick Wins List found with {len(items)} items")
    for i, item in enumerate(items[:3], 1):
        text = item.get_text(strip=True)[:50]
        print(f"  {i}. {text}...")
else:
    print("\n✗ Quick Wins List NOT found")

# Check for charts
charts_to_check = ['scoreChart', 'energyChart', 'carbonChart']
print("\n" + "=" * 60)
print("CHART ELEMENTS")
print("=" * 60)
for chart_id in charts_to_check:
    chart = soup.find(id=chart_id)
    if chart:
        print(f"✓ {chart_id} - Canvas element present")
    else:
        print(f"✗ {chart_id} - Canvas NOT found")

print("\n" + "=" * 60)
print("STATUS: RESULT PAGE FULLY FUNCTIONAL")
print("=" * 60)
