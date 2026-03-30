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

# Find console.error calls
errors = re.findall(r"console\.error\([^)]+\)", html)
if errors:
    print("Found console.error calls:")
    for error in errors:
        print(f"  {error}")

# Find if there are any syntax errors by checking for common JS error patterns
if 'uncaught' in html.lower():
    print("WARNING: Found 'uncaught' in HTML")
if 'syntaxerror' in html.lower():  
    print("WARNING: Found 'SyntaxError' in HTML")

# Check if initializeResults is defined and being called
if 'function initializeResults' in html:
    print("OK: initializeResults function is defined")
else:
    print("ERROR: initializeResults function NOT found")

# Check the exact line where initializeResults is called
match = re.search(r"if \(document\.readyState[^}]+\}", html, re.DOTALL)
if match:
    print("\nInitialization code found:")
    print(match.group(0)[:200])

# Check for syntax by finding all HTML script tags with errors
scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.DOTALL)
print(f"\nFound {len(scripts)} script tags")

# Look for the specific initialization block
init_block = re.search(r"function initializeResults\(\)[^}]+\}[^}]+\}", html, re.DOTALL)
if init_block:
    print("\ninitializeResults function found (first 300 chars):")
    print(init_block.group(0)[:300])
