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

# Check for key elements in response
html = response.text

# Search for the actual data in JavaScript
match = re.search(r"const resultData = \{[^}]*'green_score': ([^,]*)", html)
if match:
    print(f'Found green_score value: {match.group(1)}')
else:
    print('green_score value not found')

# Check if result is being used
if '{{ result.green_score }}' in html:
    print('WARNING: Unprocessed Jinja2 template found!')
elif 'green_score' in html:
    print('✓ green_score found in response')

# Find the exact JavaScript block
if 'const resultData' in html:
    start = html.find('const resultData')
    end = html.find('};', start) + 2
    print('\nJavaScript block:')
    print(html[start:end])

# Check if scoreValue element has data
if 'id="scoreValue"' in html:
    print('\n✓ scoreValue element found')
