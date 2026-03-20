# GreenOps Refactor - Developer Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (Browser)                │
│  HTML + Bootstrap | CSS Gradients | JavaScript      │
└────────────────────┬────────────────────────────────┘
                     │ HTTP/JSON
                     ▼
┌─────────────────────────────────────────────────────┐
│              Flask Web Server (app.py)              │
│  Routes | API Endpoints | Error Handling           │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│           Analysis Engine & ML Model                │
│  benchmark_code_analysis() | energy_predictor.pkl  │
└─────────────────────────────────────────────────────┘
```

## Flask Application Structure

### Routes

```python
GET  /                    # Home page with form
POST /api/analyze        # Code analysis endpoint
GET  /result             # Results page
GET  /404               # Error page
GET  /500               # Server error page
```

### Key Functions

#### `benchmark_code_analysis(code, hardware, carbon_intensity, latency)`
Main analysis engine. Returns metrics dictionary with:
- `green_score`: 0-100 efficiency rating
- `predicted_energy_kwh`: Energy consumption estimate
- `carbon_grams`: CO2 equivalent
- `insights`: Optimization recommendations
- `improvements`: Quick win suggestions

#### `generate_insights(code, complexity, loc, hardware, latency)`
Creates personalized recommendations based on:
- Code complexity patterns
- Hardware selection
- Latency requirements
- Lines of code analysis

---

## Frontend Architecture

### Templates Hierarchy

```
base.html (Navigation & Footer)
├── index.html (Analysis Page)
├── result.html (Results Page)
├── 404.html (Error Page)
└── 500.html (Server Error)
```

### Key Components

#### Index Page Flow
1. User inputs code and parameters
2. Form validation on client-side
3. API call to `/api/analyze`
4. Results stored in sessionStorage
5. Redirect to result page

#### Result Page Flow
1. Load results from sessionStorage
2. Populate metrics
3. Create visualizations
4. Display recommendations
5. Offer export/share options

---

## Styling System

### CSS Organization

```css
/* Global Variables & Reset */
:root { --primary-green: #10b981; ... }

/* Typography */
h1, h2, h3, ...

/* Components */
.card, .metric-card, .suggestion-item

/* Utilities */
.text-success, .bg-dark, etc.

/* Responsive */
@media (max-width: 768px) { ... }
```

### Color Scheme

| Variable | Value | Usage |
|----------|-------|-------|
| --primary-green | #10b981 | Eco branding, accents |
| --primary-dark | #1e293b | Backgrounds, cards |
| --accent-warning | #f59e0b | Energy metrics |
| --accent-info | #0ea5e9 | Latency, info |
| --accent-danger | #ef4444 | High priority alerts |

### Responsive Breakpoints

```css
Desktop (1200px+)  : Full layout
Tablet (768px+)    : 2-column to 1-column
Mobile (320px+)    : Full-width, touch-friendly
```

---

## JavaScript Utilities

### Global API

```javascript
// File: static/script.js
window.GreenOps = {
  formatNumber(),
  getScoreColor(),
  showToast(),
  copyToClipboard(),
  apiCall(),
  SessionStorage,
  LocalStorage,
  BrowserCapabilities,
  trackEvent(),
  validateCode()
}
```

### Session Storage

```javascript
// Save analysis result
SessionStorage.set('analysisResult', {
  code, green_score, energy, carbon, ...
});

// Retrieve on result page
const result = SessionStorage.get('analysisResult');
```

### API Communication

```javascript
// Make API call
const result = await GreenOps.apiCall('/api/analyze', 'POST', {
  code,
  hardware,
  carbon_intensity,
  latency
});
```

---

## Extending the Application

### Adding a New Analysis Metric

1. **Backend (app.py)**
   ```python
   def benchmark_code_analysis(...):
       # Add calculation
       new_metric = calculate_something(code)
       result['new_metric'] = new_metric
       return result
   ```

2. **Frontend (templates/result.html)**
   ```html
   <div id="newMetricDisplay">
       <h5>New Metric</h5>
       <span id="metricValue">0</span>
   </div>
   ```

3. **Initialization (templates/result.html)**
   ```javascript
   document.getElementById('metricValue').textContent = data.new_metric;
   ```

### Adding Hardware Type

1. **Update index.html**
   ```html
   <option value="new_hw">New Hardware Type</option>
   ```

2. **Update app.py**
   ```python
   if hardware == "new_hw":
       insights['suggestions'].append({...})
   ```

### Adding Region

1. **Find regions map in index.html**
   ```javascript
   const regions = {
       '50': 'France (Nuclear)',
       '450': 'New Region'
   }
   ```

---

## Database Integration (Future)

### Schema Example
```sql
-- Results History
CREATE TABLE analyses (
  id INT PRIMARY KEY,
  code TEXT,
  green_score FLOAT,
  carbon_grams FLOAT,
  hardware VARCHAR,
  created_at TIMESTAMP
);

-- User Sessions
CREATE TABLE sessions (
  id VARCHAR PRIMARY KEY,
  user_id INT,
  created_at TIMESTAMP
);
```

### SQLAlchemy Integration
```python
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)

class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Text)
    green_score = db.Column(db.Float)
```

---

## Testing

### Unit Tests Example (pytest)

```python
# test_analysis.py
import pytest
from app import benchmark_code_analysis

def test_green_score_calculation():
    result = benchmark_code_analysis("def f(): pass", "graviton", 450, 50)
    assert 0 <= result['green_score'] <= 100

def test_energy_prediction():
    result = benchmark_code_analysis("x" * 100, "graviton", 450, 50)
    assert result['predicted_energy_kwh'] > 0

def test_carbon_calculation():
    result = benchmark_code_analysis("def f(): pass", "graviton", 500, 50)
    assert result['carbon_grams'] > 0
```

### Run Tests
```bash
pip install pytest
pytest test_analysis.py -v
```

---

## Performance Optimization

### Frontend Optimization

```javascript
// Debounce slider input
const debouncedSlider = debounce(() => {
    updateDisplay();
}, 300);

input.addEventListener('input', debouncedSlider);
```

### Backend Optimization

```python
# Cache model loading
energy_model = joblib.load('energy_predictor.pkl')  # Load once

# Use generators for large datasets
def process_codes(codes):
    for code in codes:
        yield benchmark_code_analysis(code, ...)
```

### Asset Optimization

```html
<!-- Minify CSS/JS in production -->
<link rel="stylesheet" href="style.min.css">
<script src="script.min.js" async defer></script>

<!-- Use CDN for libraries -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0"></script>
```

---

## Security

### Input Validation

```python
# Server-side validation
code_length = len(code.strip())
if code_length < 10:
    return {'error': 'Code too short'}, 400
if code_length > 10000:
    return {'error': 'Code too long'}, 400

# No eval() or exec() of user code
```

### CSRF Protection (Production)

```python
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)

@app.route('/api/analyze', methods=['POST'])
@csrf.protect
def analyze():
    ...
```

### XSS Prevention

```html
<!-- Jinja2 auto-escapes -->
{{ user_input }}  <!-- Safe -->

<!-- For code display, use innerText not innerHTML -->
element.innerText = userCode;  <!-- Safe -->
```

---

## Monitoring & Logging

### Flask Logging

```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"Analysis complete: score={result['green_score']}")
logger.error(f"Analysis failed: {str(e)}")
```

### Performance Monitoring

```javascript
// Monitor page load
if (performance.timing) {
    const loadTime = performance.timing.loadEventEnd - 
                     performance.timing.navigationStart;
    console.log(`Page load time: ${loadTime}ms`);
}
```

---

## Deployment Checklist

- [ ] Update requirements.txt
- [ ] Set Flask `debug=False`
- [ ] Configure SECRET_KEY environment variable
- [ ] Set security headers
- [ ] Enable HTTPS
- [ ] Configure CORS if needed
- [ ] Add rate limiting
- [ ] Setup logging/monitoring
- [ ] Create backup strategy
- [ ] Document environment variables
- [ ] Test error pages

---

## Common Tasks

### Change Primary Color
1. Update CSS variable in `static/style.css`:
   ```css
   --primary-green: #new-color;
   ```

### Adjust Score Calculation
1. Modify `benchmark_code_analysis()` in `app.py`
2. Update weights and thresholds

### Add New Chart
1. Reference Chart.js in base template (already included)
2. Add canvas in result.html:
   ```html
   <canvas id="myChart"></canvas>
   ```
3. Initialize in script:
   ```javascript
   new Chart(document.getElementById('myChart'), {...})
   ```

### Change Font
1. Import from Google Fonts in base.html
2. Update CSS:
   ```css
   body { font-family: 'New Font', sans-serif; }
   ```

---

## Troubleshooting Development

| Issue | Solution |
|-------|----------|
| Hot reload not working | Install `python-dotenv` and set `FLASK_ENV=development` |
| Static files not updating | Clear browser cache or set `SEND_FILE_MAX_AGE_DEFAULT = 0` in app.py |
| Template errors | Check indentation and variable names in Jinja2 |
| JavaScript errors | Open browser console (F12) and check for errors |
| Slow analysis | Add caching or optimize `benchmark_code_analysis()` |

---

## Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Bootstrap 5](https://getbootstrap.com/docs/5.3/)
- [Chart.js](https://www.chartjs.org/)
- [Highlight.js](https://highlightjs.org/)
- [MDN Web Docs](https://developer.mozilla.org/)

---

**Last Updated:** March 2026
**Version:** 2.0
