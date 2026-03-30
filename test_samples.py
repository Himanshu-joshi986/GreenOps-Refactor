import requests
import json

BASE = "http://127.0.0.1:5000"

POOR = """import time
import requests
def analyze_data(data):
    result = []
    for item in data:
        response = requests.get(f'http://api.example.com/data/{item}')
        for line in response.text.split('\\n'):
            for char in line:
                if char != ' ':
                    result.append(char)
                    time.sleep(0.001)
    return result
huge_list = [i for i in range(10000) for j in range(100)]
result = analyze_data(huge_list)"""

MODERATE = """import pandas as pd
import numpy as np
def process_data(df):
    total = 0
    count = 0
    for idx, row in df.iterrows():
        total += row['value']
        count += 1
    average = total / count if count > 0 else 0
    result = []
    for idx, row in df.iterrows():
        result.append(row['value'] - average)
    return result
data = pd.DataFrame({'value': np.random.rand(1000)})
result = process_data(data)"""

EXCELLENT = """import pandas as pd
import numpy as np
def process_data_optimized(df):
    values = df['value'].values
    average = np.mean(values)
    deviation = values - average
    result = np.asarray(deviation)
    return result
data = pd.DataFrame({'value': np.random.rand(10000)})
result = process_data_optimized(data)
print(f"Processed {len(result)} values efficiently")"""

print("\n" + "="*60)
print("TESTING THREE CODE QUALITY SAMPLES")
print("="*60)

for name, code in [("POOR", POOR), ("MODERATE", MODERATE), ("EXCELLENT", EXCELLENT)]:
    r = requests.post(f"{BASE}/api/analyze", json={"code": code}, timeout=10)
    if r.status_code == 200:
        data = r.json()
        print(f"\n{name:12} | Score: {data['green_score']:5.1f} | Energy: {data['predicted_energy_mwh']:.2e} µkWh")
    else:
        print(f"\n{name:12} | ERROR")

print("\n" + "="*60)
