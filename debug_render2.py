import requests
import re

# Make a form submission
form_data = {
    'code': '''def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = fibonacci(10)
print(result)''',
    'hardware': 'x86',
    'carbon_intensity': '450',
    'latency': '50',
    'region': 'us-east-1'
}

response = requests.post('http://localhost:5000/analyze', data=form_data)

# Save the response to a file
with open('response.html', 'w') as f:
    f.write(response.text)

# Check for specific elements
html = response.text

# Check for scoreValue element and what's inside it
if 'id="scoreValue"' in html:
    match = re.search(r'<div[^>]*id="scoreValue"[^>]*>([^<]*)</div>', html)
    if match:
        print(f"scoreValue content: '{match.group(1)}'")

# Check for energyValue element
if 'id="energyValue"' in html:
    match = re.search(r'<div[^>]*id="energyValue"[^>]*>([^<]*)</div>', html)
    if match:
        print(f"energyValue content: '{match.group(1)}'")

# Check if updateMetrics is defined
if 'function updateMetrics' in html:
    print("✓ updateMetrics function is defined")

# Check if DOMContentLoaded event is set
if 'DOMContentLoaded' in html:
    print("✓ DOMContentLoaded event listener is set")

# Check for Chart.js
if 'Chart' in html:
    print("✓ Chart.js library is loaded")

print("\nHTML saved to response.html")
print(f"Response length: {len(html)} bytes")
