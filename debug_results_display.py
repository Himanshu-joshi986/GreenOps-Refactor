import requests
from bs4 import BeautifulSoup
import re

# Valid code sample
code_sample = '''def fibonacci(n):
    """Calculate fibonacci number"""
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

result = fibonacci(10)
print(f"Result: {result}")'''

print("=" * 80)
print("SUBMITTING FORM AND CHECKING RENDERED PAGE")
print("=" * 80)

try:
    response = requests.post('http://localhost:5000/analyze', data={
        'code': code_sample,
        'hardware': 'x86',
        'carbon_intensity': '450',
        'latency': '50',
        'region': 'us-east-1'
    })
    
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    
    print(f"\nResponse Status: {response.status_code}")
    print(f"Content Type: {response.headers.get('content-type', 'unknown')}")
    print(f"HTML Size: {len(html)} bytes")
    
    # Extract what would be VISIBLE on the page
    print("\n" + "=" * 80)
    print("VISIBLE TEXT ON RESULT PAGE (What user sees)")
    print("=" * 80)
    
    # Remove script tags to get only visible content
    for script in soup(["script", "style"]):
        script.decompose()
    
    visible_text = soup.get_text(separator='\n', strip=True)
    
    # Print first 2000 chars of visible content
    lines = visible_text.split('\n')
    print("\nFirst 40 lines of visible content:\n")
    for i, line in enumerate(lines[:40], 1):
        if line.strip():
            print(f"{i:2}. {line[:100]}")
    
    print("\n" + "=" * 80)
    print("KEY METRICS IN HTML")
    print("=" * 80)
    
    # Check for specific values
    scoreValue = soup.find(id='scoreValue')
    energyValue = soup.find(id='energyValue')
    carbonValue = soup.find(id='carbonValue')
    suggestion = soup.find(id='mainSuggestion')
    
    if scoreValue:
        print(f"✓ Green Score: {scoreValue.get_text(strip=True)}")
    else:
        print("✗ Green Score NOT FOUND")
        
    if energyValue:
        print(f"✓ Energy Value: {energyValue.get_text(strip=True)}")
    else:
        print("✗ Energy Value NOT FOUND")
        
    if carbonValue:
        print(f"✓ Carbon Value: {carbonValue.get_text(strip=True)}")
    else:
        print("✗ Carbon Value NOT FOUND")
        
    if suggestion:
        print(f"✓ Suggestion: {suggestion.get_text(strip=True)[:60]}...")
    else:
        print("✗ Suggestion NOT FOUND")
    
    print("\n" + "=" * 80)
    print("CHECKING FOR ERRORS")
    print("=" * 80)
    
    # Check for error messages
    errors = soup.find_all(['div', 'p'], class_='alert alert-danger')
    if errors:
        print("⚠ ERROR ALERTS FOUND:")
        for error in errors:
            print(f"  - {error.get_text(strip=True)[:100]}")
    else:
        print("✓ No error alerts found")
    
    # Check for specific problematic patterns
    if 'undefined' in html.lower() and '{' in html:
        print("⚠ Possible undefined variable or unprocessed template")
        
    if 'traceback' in html.lower():
        print("⚠ Python traceback in HTML - server error occurred")
        
    print("\n" + "=" * 80)
    print("SAVES HTML DUMP FOR INSPECTION")
    print("=" * 80)
    
    with open('result_page_dump.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("✓ Full HTML saved to: result_page_dump.html")
    print("  You can open this file in a browser to see exactly what's displayed")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
