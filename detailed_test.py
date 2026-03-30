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

# Parse with BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')

# Check for specific elements that should display data
elements_to_check = [
    'scoreValue',
    'scoreInterpretation',
    'energyValue',
    'energyUnit',
    'locMetric',
    'complexityMetric',
    'carbonValue',
    'treeEquivalent'
]

print("=" * 60)
print("CHECKING RENDERED HTML FOR DATA ELEMENTS")
print("=" * 60)

for elem_id in elements_to_check:
    elem = soup.find(id=elem_id)
    if elem:
        text_content = elem.get_text(strip=True)
        print(f"✓ {elem_id}: '{text_content}'")
    else:
        print(f"✗ {elem_id}: NOT FOUND")

print("\n" + "=" * 60)
print("CHECKING JAVASCRIPT DATA")
print("=" * 60)

# Check if the JavaScript has the data
match = re.search(r"const resultData = \{([^}]+)\}", html)
if match:
    data_block = match.group(1)
    # Extract green_score
    score_match = re.search(r"'green_score':\s*([\d.]+)", data_block)
    if score_match:
        print(f"✓ JavaScript green_score: {score_match.group(1)}")
    
    # Extract energy
    energy_match = re.search(r"'predicted_energy_kwh':\s*([\d.e-]+)", data_block)
    if energy_match:
        print(f"✓ JavaScript predicted_energy_kwh: {energy_match.group(1)}")
        
print("\n" + "=" * 60)
print("CHECKING FOR JAVASCRIPT ERRORS")
print("=" * 60)

# Check if updateMetrics is called
if 'updateMetrics(resultData)' in html:
    print("✓ updateMetrics(resultData) is being called")
else:
    print("✗ updateMetrics is NOT being called")

# Check if initializeCharts is called
if 'initializeCharts(resultData)' in html:
    print("✓ initializeCharts(resultData) is being called")
else:
    print("✗ initializeCharts is NOT being called")

# Check for console errors
if 'console.error' in html:
    print("⚠ console.error found in HTML")
    
print("\n" + "=" * 60)
print("CHECKING FOR ALERT ELEMENTS")
print("=" * 60)

# Check if there's an alert or error message
alert = soup.find('div', class_='alert')
if alert:
    print(f"Alert found: {alert.get_text(strip=True)[:100]}")
else:
    print("No alert found (good - page should render normally)")

print("\n" + "=" * 60)
print("First 500 chars of HTML body:")
print("=" * 60)
body = soup.find('body')
if body:
    body_html = str(body)
    print(body_html[:500])
