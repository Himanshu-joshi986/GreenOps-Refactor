from flask import Flask, render_template, request, jsonify
import joblib
import json
import traceback
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "greenops-secure-key-2026"

# Load model if exists
try:
    energy_model = joblib.load('energy_predictor.pkl')
except FileNotFoundError:
    energy_model = None

def benchmark_code_analysis(code_snippet, hardware, carbon_intensity, latency):
    """Analyze code and return metrics"""
    try:
        # Estimate metrics based on code characteristics
        lines_of_code = len(code_snippet.strip().split('\n'))
        complexity = len([line for line in code_snippet.split('\n') if 'for' in line or 'while' in line])
        
        # Calculate green score (0-100)
        base_score = 85
        score_reduction = (complexity * 3) + (lines_of_code * 0.1)
        green_score = max(10, min(100, base_score - score_reduction))
        
        # Predict energy consumption (kWh)
        predicted_energy_kwh = (lines_of_code * 0.00001) + (complexity * 0.0005) + 0.0001
        
        # Carbon emissions
        carbon_grams = predicted_energy_kwh * carbon_intensity
        
        # Generate insights and suggestions
        insights = generate_insights(code_snippet, complexity, lines_of_code, hardware, latency)
        
        return {
            'green_score': round(green_score, 1),
            'predicted_energy_kwh': round(predicted_energy_kwh, 6),
            'predicted_energy_mwh': round(predicted_energy_kwh * 1000, 3),
            'carbon_grams': round(carbon_grams, 2),
            'carbon_kg': round(carbon_grams / 1000, 4),
            'carbon_intensity': carbon_intensity,
            'hardware': hardware,
            'latency': latency,
            'complexity_score': complexity,
            'loc': lines_of_code,
            'insights': insights['suggestions'],
            'improvements': insights['improvements'],
            'estimated_co2_tree_equivalents': round(carbon_grams / 21000, 2),  # Trees needed to offset
            'context_used': f"Hardware: {hardware} | Carbon: {carbon_intensity} gCO₂/kWh | Latency: {latency}ms"
        }
    except Exception as e:
        return None

def generate_insights(code, complexity, loc, hardware, latency):
    """Generate professional insights and suggestions"""
    insights = {
        'suggestions': [],
        'improvements': []
    }
    
    # Hardware-specific suggestions
    if hardware == "x86":
        insights['suggestions'].append({
            'title': 'Consider ARM Architecture',
            'description': 'Graviton processors offer better energy efficiency (up to 40% lower power)',
            'priority': 'high',
            'impact': '~15% energy savings'
        })
    
    # Code optimization suggestions
    if complexity > 3:
        insights['suggestions'].append({
            'title': 'Reduce Loop Complexity',
            'description': 'Reduce nested loops and optimize algorithmic efficiency',
            'priority': 'high',
            'impact': '~25% energy reduction'
        })
    
    if loc > 100:
        insights['suggestions'].append({
            'title': 'Refactor Code Size',
            'description': 'Break down into smaller microservices for better resource allocation',
            'priority': 'medium',
            'impact': '~10% energy reduction'
        })
    
    if latency > 100:
        insights['suggestions'].append({
            'title': 'Optimize Latency',
            'description': 'High latency indicates potential bottlenecks. Consider caching or async operations',
            'priority': 'medium',
            'impact': '~8% energy reduction'
        })
    
    # Default suggestions if needed
    if not insights['suggestions']:
        insights['suggestions'].append({
            'title': 'Great Job!',
            'description': 'Your code is already optimized. Monitor performance metrics regularly.',
            'priority': 'low',
            'impact': 'Maintain current efficiency'
        })
    
    insights['improvements'] = [
        '✓ Use list comprehensions instead of loops',
        '✓ Implement caching for repeated computations',
        '✓ Use native libraries for heavy lifting',
        '✓ Optimize database queries',
        '✓ Consider async/await for I/O operations',
        '✓ Profile code regularly for bottlenecks'
    ]
    
    return insights

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """API endpoint for code analysis"""
    try:
        data = request.json
        code = data.get('code', '').strip()
        hardware = data.get('hardware', 'graviton')
        carbon = float(data.get('carbon_intensity', 450))
        latency = float(data.get('latency', 50))
        
        if not code or len(code) < 10:
            return jsonify({'error': 'Code snippet too short (min 10 characters)'}), 400
        
        if len(code) > 10000:
            return jsonify({'error': 'Code snippet too long (max 10000 characters)'}), 400
        
        result = benchmark_code_analysis(code, hardware, carbon, latency)
        
        if not result:
            return jsonify({'error': 'Analysis failed'}), 500
        
        return jsonify(result), 200
    
    except Exception as e:
        print(f"Error in /api/analyze: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/result')
def result_page():
    """Legacy route for backward compatibility"""
    return render_template('result.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
