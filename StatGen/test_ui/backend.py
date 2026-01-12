"""
StatGen Test UI Backend
A separate Flask app for testing the LLM-powered stat generation.
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request, jsonify
from llm_client import generate_creature_stats
from stat_engine import validate_creature

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        creature_label = data.get('label', 'unknown')
        confidence = data.get('confidence', 1.0)
        
        # Step 1: Call LLM
        raw_creature = generate_creature_stats(creature_label, confidence)
        
        if "error" in raw_creature:
            return jsonify({"error": raw_creature["error"]}), 500
        
        # Step 2: Validate with Engine
        validated_creature, warnings = validate_creature(raw_creature)
        
        return jsonify({
            "creature": validated_creature,
            "warnings": warnings,
            "raw_llm_output": raw_creature  # For debugging
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    import webbrowser
    from threading import Timer
    
    def open_browser():
        webbrowser.open("http://127.0.0.1:5001")
    
    Timer(1.5, open_browser).start()
    print("Starting StatGen Test UI on http://127.0.0.1:5001")
    app.run(debug=False, port=5001)
