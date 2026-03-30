import requests
import json

# Test form submission
form_data = {
    'code': '''def calculate_fibonacci(n):
    """Calculate nth fibonacci number"""
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

result = calculate_fibonacci(10)
print(f"Result: {result}")''',
    'hardware': 'x86',
    'carbon_intensity': '450',
    'latency': '50',
    'region': 'us-east-1'
}

print("=" * 70)
print("TESTING FORM SUBMISSION")
print("=" * 70)

try:
    response = requests.post('http://localhost:5000/analyze', data=form_data, timeout=10)
    
    print(f"Status Code: {response.status_code}")
    print(f"Content Length: {len(response.text)} bytes")
    
    # Check if HTML contains actual data
    html = response.text
    
    checks = {
        'Result Page Title': '{% block title %}' not in html and '<title>' in html,
        'Success Alert': 'Analysis Complete' in html,
        'Green Score': '>94<' in html or '>93<' in html or 'scoreValue' in html,
        'Energy Value': 'energyValue' in html,
        'Carbon Value': 'carbonValue' in html,
        'Quick Wins': 'quickWinsList' in html,
        'Cards Present': 'card shadow-lg' in html,
        'Navigation': '<nav' in html,
    }
    
    print("\n" + "=" * 70)
    print("CONTENT CHECKS")
    print("=" * 70)
    
    for check_name, result in checks.items():
        status = "✓" if result else "✗"
        print(f"{status} {check_name}: {result}")
    
    # Try to extract a specific value
    import re
    score_match = re.search(r'<div[^>]*id="scoreValue"[^>]*>([^<]+)</div>', html)
    if score_match:
        print(f"\n✓ Score Value Found: {score_match.group(1)}")
    else:
        print(f"\n✗ Score Value Not Found")
        
    # Check for JavaScript errors
    if 'error' in html.lower() and 'console.error' in html:
        print("\n⚠ JavaScript console.error found in template")
        
    print("\n" + "=" * 70)
    print("FIRST 1000 CHARS OF RESPONSE:")
    print("=" * 70)
    print(html[:1000])
    
except requests.exceptions.ConnectionError:
    print("✗ ERROR: Cannot connect to Flask app at http://localhost:5000")
    print("  Make sure Flask is running!")
except Exception as e:
    print(f"✗ ERROR: {e}")
