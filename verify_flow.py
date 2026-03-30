import requests
from bs4 import BeautifulSoup

code = """def analyze():
    total = 0
    for i in range(1000):
        for j in range(100):
            total += i*j
    return total"""

print('Step 1: Testing API response...')
r = requests.post('http://127.0.0.1:5000/api/analyze', json={'code': code})
if r.status_code == 200:
    data = r.json()
    print(f'  Status: {r.status_code}')
    print(f'  Green Score: {data.get("green_score")}')
    print(f'  Has all fields: {len(data) > 10}')
else:
    print(f'  Error: {r.status_code}')

print('\nStep 2: Fetching /result page...')
r = requests.get('http://127.0.0.1:5000/result')
print(f'  Status: {r.status_code}')
soup = BeautifulSoup(r.text, 'html.parser')

# Check elements
id_score = soup.find(id='scoreValue')
id_energy = soup.find(id='energyValue')  
print(f'  scoreValue element: {"found" if id_score else "MISSING"}')
print(f'  energyValue element: {"found" if id_energy else "MISSING"}')

# Check for sessionStorage code
if 'sessionStorage.getItem' in r.text:
    print(f'  SessionStorage code: FOUND')
else:
    print(f'  SessionStorage code: MISSING')
