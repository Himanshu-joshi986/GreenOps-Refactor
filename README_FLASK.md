# GreenOps Refactor - Professional UI

A modern, production-ready Flask application for carbon-aware code optimization and energy efficiency analysis. Features context-aware suggestions, real-time metrics, and beautiful visualizations designed for enterprise seminar presentations.

## Features

✨ **Professional Design**
- Modern gradient UI with dark theme optimized for presentations
- Responsive design for desktop and mobile
- Smooth animations and transitions
- Custom syntax highlighting for Python code

📊 **Advanced Analytics**
- Real-time green score calculation (0-100)
- Energy consumption prediction
- Carbon footprint tracking with tree equivalents
- Complexity analysis and optimization metrics
- Interactive charts and visualizations

🎯 **Context-Aware Features**
- Hardware type selection (Graviton/x86)
- Regional carbon intensity simulation
- Latency SLA configuration
- Hardware impact comparison

💡 **Smart Recommendations**
- Prioritized optimization suggestions
- Hardware-specific advice
- Code improvement quick wins
- Estimated energy/carbon savings per recommendation

🔒 **Production Ready**
- Error handling and validation
- Session management
- Performance optimized
- Syntax highlighting with Highlight.js
- Chart.js for visualizations

## Project Structure

```
greenops-refactor/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── benchmark.py                    # Code analysis module
├── feature_extractor.py           # ML feature extraction
├── training_model.py              # Model training
├── energy_predictor.pkl           # Pre-trained model
│
├── templates/
│   ├── base.html                  # Base template (navbar, footer)
│   ├── index.html                 # Home/analysis page
│   ├── result.html                # Results display page
│   ├── 404.html                   # Error page
│   └── 500.html                   # Server error page
│
└── static/
    ├── style.css                  # Professional styling (2600+ lines)
    └── script.js                  # Client-side utilities and interactivity
```

## Installation & Setup

### 1. Clone or Download Repository
```bash
cd d:\GreenOps-Refactor
```

### 2. Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python app.py
```

The application will start at `http://127.0.0.1:5000`

## Usage

### For Analysis

1. **Paste Code**: Enter your Python microservice code (10-10,000 characters)
2. **Set Context**:
   - **Hardware**: Choose between Graviton (ARM) or x86 processors
   - **Carbon Intensity**: Select or adjust for your region (50-800 gCO₂/kWh)
   - **Latency**: Set your maximum acceptable latency in milliseconds
3. **Analyze**: Click "Analyze & Get Green Suggestions"
4. **Review Results**: See your green score, energy usage, and carbon footprint
5. **Export**: Download report or share results

### API Endpoints

#### POST /api/analyze
Analyze code and get metrics.

**Request:**
```json
{
  "code": "def process_order(): ...",
  "hardware": "graviton",
  "carbon_intensity": 450,
  "latency": 50
}
```

**Response:**
```json
{
  "green_score": 75.5,
  "predicted_energy_kwh": 0.000125,
  "predicted_energy_mwh": 0.125,
  "carbon_grams": 56.25,
  "carbon_kg": 0.0563,
  "carbon_intensity": 450,
  "hardware": "graviton",
  "latency": 50,
  "complexity_score": 3,
  "loc": 45,
  "insights": [...],
  "improvements": [...],
  "estimated_co2_tree_equivalents": 0.0027,
  "context_used": "Hardware: GRAVITON | Carbon: 450 gCO₂/kWh | Latency: 50ms"
}
```

## Green Scoring Algorithm

The green score calculation considers:

- **Lines of Code**: Baseline efficiency
- **Complexity Score**: Loop and conditional depth
- **Hardware Type**: Architecture efficiency differences
- **Carbon Intensity**: Regional energy source impact
- **Latency Requirements**: Performance vs. efficiency trade-off

Scores:
- **80-100**: Excellent optimization
- **60-79**: Good optimization
- **40-59**: Average - room for improvement
- **Below 40**: Needs significant refactoring

## Carbon Intensity by Region

The application includes regional references:

| Region | gCO₂/kWh | Primary Sources |
|--------|----------|-----------------|
| France | ~50 | Nuclear (70%) |
| Canada | ~80 | Hydroelectric |
| UK | ~200 | Renewables (40%) |
| Global Average | ~450 | Mixed sources |
| Germany | ~380 | 50% Renewable |

## Customization

### Modify Scoring Algorithm
Edit `benchmark_code_analysis()` in `app.py` to adjust the green score calculation.

### Add More Hardware Types
Extend the `hardware` select in [templates/index.html](templates/index.html#L102) and add logic in `app.py`.

### Update Regional Data
Modify the carbon regions mapping in [templates/index.html](templates/index.html#L251).

### Customize Styling
All CSS is in [static/style.css](static/style.css) with organized sections for easy modification.

## Performance Optimization

The UI includes several optimizations:

- **CSS Variables** for easy theming
- **Debounced Range Inputs** to reduce event firing
- **Lazy Loading** for charts and images
- **Optimized Asset Loading** with CDN
- **Minimized Repaints** through CSS containment

## Browser Support

- **Chrome/Edge**: Full support (2023+)
- **Firefox**: Full support (115+)
- **Safari**: Full support (16.4+)
- **Mobile**: iOS Safari 16+, Chrome Android

## Deployment

### Local Development
```bash
python app.py
```

### Production with Gunicorn
```bash
pip install gunicorn
gunicorn app:app --bind 0.0.0.0:5000 --workers 4
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

```bash
docker build -t greenops-refactor .
docker run -p 5000:5000 greenops-refactor
```

### AWS/Azure/GCP
1. Package with appropriate runtime
2. Set environment variables
3. Configure secrets for sensitive data
4. Use application logs for monitoring

## Environment Variables

```bash
# .env
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=your-secret-key-here
```

## Troubleshooting

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :5000
kill -9 <PID>
```

### CSS/JS Not Loading
- Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
- Clear browser cache
- Check static file paths

### Chart Not Rendering
- Ensure Chart.js CDN is accessible
- Check browser console for errors
- Verify data format in result.html

### Code Analysis Failing
- Validate code isn't too short (<10 chars) or too long (>10000 chars)
- Check Flask logs for detailed errors
- Ensure energy_predictor.pkl exists

## Security Considerations

- Code input is validated server-side
- No code is stored unless explicitly saved
- Session data expires after browser close
- CSRF protection ready (implement in production)
- XSS protection through template escaping
- SQL injection N/A (no database)

## Future Enhancements

- [ ] User accounts and result history
- [ ] Batch code analysis
- [ ] Integration with GitHub
- [ ] Real ML model for better predictions
- [ ] Database for analytics
- [ ] Mobile app version
- [ ] API authentication
- [ ] Advanced reporting features
- [ ] Team collaboration features
- [ ] Carbon offset suggestions

## Development

### Adding New Features

1. **Backend Logic**: Add to [app.py](app.py)
2. **Frontend UI**: Add to templates
3. **Styling**: Add to [static/style.css](static/style.css)
4. **JavaScript**: Add to [static/script.js](static/script.js)

### Code Style
- Python: PEP 8
- HTML: Semantic, accessible markup
- CSS: BEM-like naming convention
- JavaScript: Modern ES6+

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

See [LICENSE](LICENSE) file for details.

## Support & Resources

- **Documentation**: See README sections above
- **Issues**: Create an issue in the repository
- **Demo**: Run `python app.py` and visit http://localhost:5000

## Contact

For questions or suggestions, please reach out or create an issue.

---

**Built with ❤️ for a sustainable future** 🌿

Version 2.0 | Last Updated: March 2026
