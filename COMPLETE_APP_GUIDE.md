# GreenOps Application - Complete Guide

## ✅ What's Fixed & Improved

### 1. **Results Display Issue - FIXED** ❌→✅
**Problem:** After analysis, results weren't showing, scores were null/blank  
**Root Cause:** sessionStorage data wasn't being read properly on result page  
**Solution:** 
- Improved result_page.html with better error handling
- Added console logging for debugging
- Used try-catch blocks to prevent silent failures
- Added fallback message if no data found

### 2. **User Interface - REDESIGNED**
**Improvements:**
- **Left Column (70%):** Code input area with validation
- **Right Column (30%):** Sample code selector (sticky/always visible)
- **Sample Buttons:** 
  - 🔴 Poor Code (Score: 71.0) - Shows inefficiency
  - 🟡 Moderate Code (Score: 95.6) - Shows better but not optimized
  - 🟢 Excellent Code (Score: 97.1) - Shows best practices
- **Instructions:** Clear step-by-step guide for users

### 3. **Result Page - ENHANCED**
**Now Displays:**
- ✅ Green Score (0-100) with interpretation
- ✅ Energy Consumption (in µkWh and kWh)
- ✅ Carbon Footprint (in grams with annual tree offset)
- ✅ Code Metrics (LOC, complexity, functions, loops, patterns)
- ✅ Hardware Utilization (CPU, RAM, GPU progress bars)
- ✅ Analysis Context (hardware type, carbon intensity, region, latency)
- ✅ Main Optimization Suggestion (highlighted)
- ✅ Quick Wins List (5-10 actionable improvements)
- ✅ Charts (Energy breakdown pie chart, Carbon impact bar chart)
- ✅ Export Options (CSV download, JSON copy, Share)

### 4. **Data Flow - VERIFIED WORKING**
```
User Action           →  Browser Event
                       ↓
Fill Code/Select Sample → Click "Analyze"
                       ↓
Form Validates        → Check code length (min 20 chars)
                       ↓
API Request           → POST /api/analyze with code + context
                       ↓
Model Analysis        → Machine Learning predictions
                       ↓
API Response          → JSON with 18 data fields
                       ↓
Store in sessionStorage → sessionStorage.setItem('analysisResult', ...)
                       ↓
Redirect to /result   → window.location.href = '/result'
                       ↓
Result Page Loads     → Server renders result_page.html
                       ↓
JavaScript Executes   → Reads sessionStorage
                       ↓
Display Results       → Populates all HTML elements with data
                       ↓
Render Charts         → Chart.js creates visualizations
                       ↓
User Sees:
  • Green Score: ✓ Displayed
  • Energy: ✓ Displayed  
  • Carbon: ✓ Displayed
  • All Metrics: ✓ Displayed
  • Charts: ✓ Rendered
  • Quick Wins: ✓ Listed
```

## 🎯 How to Use the App

### **Method 1: Try Sample Code (Easiest for Testing)**
1. Open http://localhost:5000
2. Right side shows 3 sample buttons
3. Click "Poor Code" or "Moderate Code" or "Excellent Code"
4. Code loads into the textarea on the left (auto-filled)
5. Click "Analyze & Get Green Suggestions" button
6. Results page displays with all metrics and charts
7. Try different samples to compare scores

### **Method 2: Write Your Own Code**
1. Open http://localhost:5000
2. Clear the textarea (click "Clear" button)
3. Paste or type your Python code (min 20 characters)
4. Optionally adjust context parameters:
   - Hardware Type: Graviton (ARM) or x86
   - Carbon Intensity: Slider (50-800 gCO₂/kWh)
   - Latency: Input field
   - Region: Dropdown
5. Click "Analyze & Get Green Suggestions"
6. View detailed analysis

## 📊 Understanding the Results

### **Green Score (0-100)**
- **90-100:** Excellent - Well optimized, minimal improvements needed
- **70-89:** Good - Some optimizations available
- **50-69:** Average - Significant room for improvement  
- **0-49:** Poor - Major refactoring recommended

### **Energy Consumption**
- Measured in µkWh (microkilowatt-hours)
- Shows predicted energy per execution
- Lower is better

### **Carbon Footprint**
- Measured in grams of CO₂
- Based on region's carbon intensity
- Annual tree offset shows equivalent reforestation needed

### **Code Metrics**
- **LOC:** Total lines of code
- **Complexity:** Cyclomatic complexity score (lower = simpler)
- **Functions:** Number of function/method definitions
- **Loops:** Count of for/while loops (more loops = more processing)
- **Patterns:** Detected async, ML, or I/O operations

### **Hardware Utilization**
- **CPU %:** Percentage of CPU time
- **RAM %:** Percentage of memory used
- **GPU %:** GPU usage (0 if not applicable)

### **Quick Wins**
- 5-10 specific, actionable improvements
- Sorted by impact (highest first)
- Example: "Replace loop with numpy vectorization" or "Use caching for repeated queries"

## 🧪 Sample Code Characteristics

### **POOR Code (Score: 71.0)**
```python
import time, requests
def analyze_data(data):
    result = []
    for item in data:
        response = requests.get(f'http://api.example.com/data/{item}')
        for line in response.text.split('\n'):
            for char in line:
                if char != ' ':
                    result.append(char)
                    time.sleep(0.001)  # WAY too much I/O!
    return result
huge_list = [i for i in range(10000) for j in range(100)]
result = analyze_data(huge_list)
```
**Problems:**
- Triple nested loops (inefficient)
- I/O operations inside loops (major bottleneck)
- Sleeping in loop (time waste)
- List comprehension creates huge list (memory waste)

### **MODERATE Code (Score: 95.6)**
```python
import pandas as pd, numpy as np
def process_data(df):
    total = 0
    count = 0
    for idx, row in df.iterrows():  # iterrows is slow!
        total += row['value']
        count += 1
    average = total / count if count > 0 else 0
    result = []
    for idx, row in df.iterrows():  # Looping again!
        result.append(row['value'] - average)
    return result
data = pd.DataFrame({'value': np.random.rand(1000)})
result = process_data(data)
```
**Issues:**
- Uses pandas iterrows (slower than vectorized)
- Loops twice (inefficient)
- Manual averaging instead of pandas/numpy built-ins
- Not fully utilizing pandas capabilities

### **EXCELLENT Code (Score: 97.1)**
```python
import pandas as pd, numpy as np
def process_data_optimized(df):
    values = df['value'].values  # Extract numpy array
    average = np.mean(values)     # Vectorized operation
    deviation = values - average  # Vectorized operation
    result = np.asarray(deviation)
    return result
data = pd.DataFrame({'value': np.random.rand(10000)})
result = process_data_optimized(data)
print(f"Processed {len(result)} values efficiently")
```
**Advantages:**
- Fully vectorized operations (no loops)
- Uses numpy for speed
- Single pass through data
- Pre-allocated arrays
- Minimal memory footprint

## 💾 Export & Sharing

### **Download CSV**
- Exports key metrics to CSV file
- Includes: Green Score, Energy, Carbon, Complexity, etc.
- Timestamped filename (e.g., greenops-2026-03-31.csv)

### **Copy JSON**
- Copies complete analysis result as JSON
- All 18 data fields included
- Can be pasted into other tools or saved

## 🔧 Technical Details

### **API Endpoint: POST /api/analyze**
**Input:**
```json
{
  "code": "def test(): return sum(range(100))",
  "hardware": "x86",
  "carbon_intensity": 450,
  "latency_ms": 50,
  "region": "us-east-1"
}
```

**Output (Example):**
```json
{
  "green_score": 97.8,
  "predicted_energy_kwh": 4.448e-05,
  "predicted_energy_mwh": 4.448e-11,
  "carbon_grams": 0.02,
  "carbon_kg": 0.00002,
  "tree_equivalents": 0.0000275,
  "code_metrics": {
    "lines_of_code": 5,
    "complexity_score": 1.5,
    "num_functions": 1,
    "num_loops": 1,
    "has_async": false,
    "has_ml": false,
    "has_io": false
  },
  "context_used": {
    "hardware": "x86",
    "carbon_intensity": 450,
    "latency_ms": 50,
    "region": "us-east-1"
  },
  "energy_breakdown": {
    "cpu_energy_kwh": 4.2e-05,
    "gpu_energy_kwh": 0,
    "ram_energy_kwh": 2.48e-06
  },
  "hardware_utilization": {
    "cpu_percent": 45,
    "ram_percent": 32,
    "gpu_percent": 0
  },
  "quick_wins": [
    "Replace loop with list comprehension",
    "Consider using generator expression"
  ],
  "suggested_refactor": "..."
}
```

## 🐛 Troubleshooting

### **Issue: Results show "--" or "null"**
**Solution:** 
1. Clear browser cache
2. Open DevTools (F12) → Console tab
3. Check for JavaScript errors
4. Reload page and try again
5. Try with sample code first

### **Issue: "No analysis data" error**
**Solution:**
1. Make sure code is at least 20 characters
2. Click "Analyze" button again
3. Check browser console for error messages
4. Verify Flask server is running

### **Issue: Charts not rendering**
**Solution:**
1. JSON data may be incomplete
2. Try different code sample
3. Check browser console for Chart.js errors
4. Verify canvas elements exist in HTML

## 📝 Files Modified

### **Core Application Files**
- `app.py` - Flask routes and API endpoints ✅ Working
- `benchmark.py` - ML model predictions ✅ Working
- `feature_extractor.py` - Code analysis ✅ Working

### **Frontend Files (Updated)**
- `templates/index.html` - Improved two-column layout with samples
- `templates/result_page.html` - Enhanced results with all metrics & charts
- `static/script.js` - Form submission and storage handling
- `static/style.css` - Styling (no changes needed)

### **Documentation (Created)**
- `USAGE_GUIDE.html` - Interactive usage guide
- This file - Complete reference

## 🚀 Next Steps

1. **Open the app:** http://localhost:5000
2. **Try samples:** Click Poor/Moderate/Excellent buttons
3. **Analyze your code:** Paste Python code and click Analyze
4. **Review results:** See all metrics, charts, and suggestions
5. **Export data:** Download CSV or copy JSON
6. **Share:** Use exported data with your team

## ✨ Features Summary

- ✅ ML-based code energy analysis
- ✅ Real-time Green Score (0-100)
- ✅ Carbon footprint calculation
- ✅ Code quality metrics
- ✅ Hardware impact analysis
- ✅ Regional carbon intensity
- ✅ Optimization suggestions
- ✅ Quick wins list
- ✅ Data visualization (charts)
- ✅ CSV/JSON export
- ✅ Pre-loaded sample code
- ✅ Responsive design
- ✅ Professional UI

---

**Version:** 2.0  
**Last Updated:** March 31, 2026  
**Status:** ✅ Production Ready
