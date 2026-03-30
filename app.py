from flask import Flask, render_template, request, flash, jsonify
from benchmark import benchmark_code
import json
import logging

app = Flask(__name__)
app.secret_key = "greenops-secure-key-2026"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze code for energy efficiency (form-based)"""
    try:
        # Get form data
        code = request.form.get('code', '').strip()
        hardware = request.form.get('hardware', 'x86')
        carbon = request.form.get('carbon_intensity', '450')
        latency = request.form.get('latency', '50')
        region = request.form.get('region', 'us-east-1')

        # Validate code input
        if len(code) < 20:
            flash("Please paste a meaningful code snippet (min 20 characters)", "danger")
            return render_template('index.html')

        # Parse numeric inputs safely
        try:
            carbon = float(carbon)
            latency = float(latency)
        except ValueError:
            flash("Invalid carbon intensity or latency values", "danger")
            return render_template('index.html')

        logger.info(f"Processing analysis: hw={hardware}, carbon={carbon}, latency={latency}")

        # Prepare context for benchmark
        context = {
            "hardware": hardware or "x86",
            "carbon_intensity": carbon or 450,
            "latency_ms": latency or 50,
            "region": region or "us-east-1"
        }

        # Run benchmark
        result = benchmark_code(code, context)

        if not result:
            logger.error("Benchmark returned None")
            flash("Analysis failed. Please check your code and try again.", "danger")
            return render_template('index.html')

        logger.info(f"✓ Analysis successful: score={result.get('green_score')}")

        # Pass results to template
        return render_template('result.html', result=result, code=code)

    except Exception as e:
        logger.error(f"✗ Error in analyze: {str(e)}", exc_info=True)
        flash(f"Error: {str(e)}", "danger")
        return render_template('index.html')

@app.route('/result')
def result():
    """Result page - displays analysis results"""
    # This page will read from sessionStorage in the client
    # Just render a shell page that will display sessionStorage data
    return render_template('result_page.html')

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """API endpoint for code analysis (JSON)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        code = data.get('code', '').strip()
        
        context = {
            "hardware": data.get('hardware', 'x86'),
            "carbon_intensity": float(data.get('carbon_intensity', 450)),
            "latency_ms": float(data.get('latency_ms', 50)),
            "region": data.get('region', 'us-east-1')
        }

        if len(code) < 20:
            return jsonify({'error': 'Code snippet too short (minimum 20 characters)'}), 400

        logger.info(f"API analyze: hw={context['hardware']}, carbon={context['carbon_intensity']}")

        result = benchmark_code(code, context)
        
        if not result:
            logger.error("Benchmark returned None for API request")
            return jsonify({'error': 'Analysis failed - model error'}), 500

        logger.info(f"✓ API analysis successful: score={result.get('green_score')}")
        return jsonify(result), 200

    except ValueError as e:
        logger.warning(f"Invalid value in API request: {e}")
        return jsonify({'error': f'Invalid numeric value: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"✗ API Error: {str(e)}", exc_info=True)
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)