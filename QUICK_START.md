# GreenOps Refactor - Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Step 1: Install Dependencies
```bash
cd d:\GreenOps-Refactor
pip install -r requirements.txt
```

### Step 2: Run the Application
```bash
python app.py
```

### Step 3: Open Browser
Navigate to **http://127.0.0.1:5000** 🎉

---

## 📋 What You Need

- **Python 3.8+** installed
- **Flask** (automatically installed)
- **Modern Web Browser** (Chrome, Firefox, Safari, Edge)
- **Internet Connection** (for CDN resources)

---

## 🎯 Using the Application

### Home Page Features

1. **Code Input Area**
   - Paste your Python code (10-10,000 characters)
   - Real-time character counter
   - Syntax highlighting support

2. **Context Parameters**
   - **Hardware**: Select Graviton (ARM) or x86
   - **Carbon Intensity**: Adjust slider from 50-800 gCO₂/kWh
   - **Latency**: Set SLA requirement (0-200ms)

3. **Quick Tips Panel**
   - Regional carbon intensity reference
   - Hardware impact comparison
   - Optimization suggestions

### Results Page Features

1. **Green Score Card**
   - Visual score display (0-100)
   - Performance interpretation
   - Real-time calculation

2. **Metrics Dashboard**
   - Energy consumption (µkWh)
   - Carbon footprint (grams CO₂)
   - Tree equivalents needed
   - Complexity analysis

3. **Optimization Recommendations**
   - Priority-ranked suggestions
   - Expected impact estimates
   - Hardware-specific advice
   - Quick win improvements

4. **Code Review**
   - Syntax-highlighted code display
   - Full analysis context
   - Download/share options

---

## 🎨 UI Highlights

✨ **Modern Design**
- Dark theme optimized for presentations
- Green gradient accents for eco-friendly branding
- Smooth animations and transitions

📱 **Responsive Layout**
- Works on desktop (1920px+)
- Tablet-friendly (768px+)
- Mobile optimized (320px+)

🌙 **Professional Aesthetic**
- Card-based layout
- Glassmorphism effects
- Premium gradients
- Accessible color contrast

---

## 🔧 Configuration

### Adjust Green Score Calculation
Edit `benchmark_code_analysis()` in `app.py`:
```python
# Modify these values to change scoring
base_score = 85
score_reduction = (complexity * 3) + (lines_of_code * 0.1)
```

### Add More Regions
In `templates/index.html`, add to carbon regions:
```javascript
'380': 'Your Region Name'
```

### Customize Colors
In `static/style.css`, modify CSS variables:
```css
--primary-green: #10b981;
--primary-dark: #1e293b;
```

---

## 📊 API Usage

Make direct API calls for integration:

```bash
curl -X POST http://127.0.0.1:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def process(): return 42",
    "hardware": "graviton",
    "carbon_intensity": 450,
    "latency": 50
  }'
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 5000 in use | Change port in app.py: `app.run(port=5001)` |
| Module not found | Install dependencies: `pip install -r requirements.txt` |
| Styles not loading | Hard refresh: `Ctrl+Shift+R` |
| Slow performance | Reduce code size or increase latency value |

---

## 📁 File Overview

| File | Purpose |
|------|---------|
| `app.py` | Main Flask application logic |
| `templates/base.html` | Shared navigation and footer |
| `templates/index.html` | Home and analysis form page |
| `templates/result.html` | Results and metrics display |
| `static/style.css` | All styling (2600+ lines) |
| `static/script.js` | Client-side interactions |
| `requirements.txt` | Python dependencies |

---

## 🎓 For Presentations

### Demo Flow
1. Open app at http://127.0.0.1:5000
2. Show sample code analysis
3. Adjust hardware/carbon parameters
4. Demonstrate result metrics
5. Download and share results

### Sample Code for Demo
```python
def calculate_order_total(items):
    total = 0
    for item in items:
        for modifier in item.get('modifiers', []):
            total += item['price'] * modifier['multiplier']
    return total
```

### Talking Points
- Real-world energy impact of code
- Hardware architecture differences
- Regional carbon intensity variation
- Optimization opportunities and savings

---

## 💡 Tips & Tricks

1. **Keyboard Shortcuts**
   - `Ctrl+J` or `Cmd+J`: Jump to analysis form
   - `Ctrl+K` or `Cmd+K`: Focus code input

2. **Best Results**
   - Use realistic code samples
   - Set accuracy carbon values for region
   - Consider actual latency requirements

3. **Sharing Results**
   - Download full report
   - Share via web
   - Use in presentations

---

## 📚 Learn More

- Full documentation in [README_FLASK.md](README_FLASK.md)
- Carbon intensity data: https://www.electricitymap.org
- Cloud carbon tools: https://www.cloudcarbonfootprint.org

---

## 🚀 Next Steps

1. ✅ Run the app
2. ✅ Try sample analysis
3. ✅ Explore metrics
4. ✅ Download results
5. ✅ Integrate with your workflow

---

**Need help?** Check the FAQ section in README_FLASK.md or review error messages in browser console.

Happy optimizing! 🌿
