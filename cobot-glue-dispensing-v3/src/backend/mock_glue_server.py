"""
Mock Glue Weight Server

This script starts a local Flask server that simulates the glue weight endpoints
used by the GlueCell system. It provides three endpoints for three glue meters
with simulated weight data that changes over time.

Usage:
    python mock_glue_server.py

Endpoints:
    http://localhost:5000/weight1
    http://localhost:5000/weight2
    http://localhost:5000/weight3

Each endpoint returns JSON with the current weight value that simulates
glue consumption over time.
"""

from flask import Flask, jsonify
import time
import random
import threading

app = Flask(__name__)

# Initial weights for each glue meter (in grams)
weights = {
    1: 5000.0,  # Starts at 5000g
    2: 7500.0,  # Starts at 7500g
    3: 3000.0   # Starts at 3000g
}

# Consumption rates (grams per second) - INCREASED FOR TESTING
consumption_rates = {
    1: 50.0,   # Fast consumption - 50g/s
    2: 75.0,   # Very fast consumption - 75g/s
    3: 30.0    # Medium consumption - 30g/s
}

# Lock for thread-safe weight updates
weight_lock = threading.Lock()

def simulate_weight_changes():
    """Background thread that simulates glue consumption"""
    while True:
        time.sleep(1)  # Update every second

        with weight_lock:
            for meter_id in weights.keys():
                # Decrease weight by consumption rate
                weights[meter_id] -= consumption_rates[meter_id]

                # Add some random fluctuation (±0.5g)
                weights[meter_id] += random.uniform(-0.5, 0.5)

                # Don't go below 0
                if weights[meter_id] < 0:
                    weights[meter_id] = 0

@app.route('/weights')
def get_weights():
    """Main endpoint that returns all weights - matches production format"""
    with weight_lock:
        return jsonify({
            "weight1": round(weights[1], 2),
            "weight2": round(weights[2], 2),
            "weight3": round(weights[3], 2),
            "timestamp": time.time()
        })

@app.route('/weight1')
def weight1():
    """Endpoint for glue meter 1 (individual access)"""
    with weight_lock:
        current_weight = round(weights[1], 2)

    return jsonify({
        "weight": current_weight,
        "unit": "g",
        "timestamp": time.time()
    })

@app.route('/weight2')
def weight2():
    """Endpoint for glue meter 2 (individual access)"""
    with weight_lock:
        current_weight = round(weights[2], 2)

    return jsonify({
        "weight": current_weight,
        "unit": "g",
        "timestamp": time.time()
    })

@app.route('/weight3')
def weight3():
    """Endpoint for glue meter 3 (individual access)"""
    with weight_lock:
        current_weight = round(weights[3], 2)

    return jsonify({
        "weight": current_weight,
        "unit": "g",
        "timestamp": time.time()
    })

@app.route('/reset/<int:meter_id>/<float:new_weight>')
def reset_weight(meter_id, new_weight):
    """Endpoint to reset a specific meter's weight (for testing)"""
    if meter_id not in weights:
        return jsonify({"error": f"Invalid meter_id: {meter_id}"}), 400

    with weight_lock:
        weights[meter_id] = new_weight

    return jsonify({
        "message": f"Weight for meter {meter_id} reset to {new_weight}g",
        "meter_id": meter_id,
        "new_weight": new_weight
    })

@app.route('/status')
def status():
    """Endpoint to get status of all meters"""
    with weight_lock:
        current_weights = {k: round(v, 2) for k, v in weights.items()}

    return jsonify({
        "meters": current_weights,
        "consumption_rates": consumption_rates,
        "timestamp": time.time()
    })

@app.route('/')
def index():
    """Root endpoint with usage information"""
    return """
    <h1>Mock Glue Weight Server</h1>
    <p>Available endpoints:</p>
    <ul>
        <li><a href="/weight1">/weight1</a> - Glue Meter 1</li>
        <li><a href="/weight2">/weight2</a> - Glue Meter 2</li>
        <li><a href="/weight3">/weight3</a> - Glue Meter 3</li>
        <li><a href="/status">/status</a> - All meters status</li>
        <li>/reset/&lt;meter_id&gt;/&lt;new_weight&gt; - Reset meter weight (e.g., /reset/1/5000)</li>
    </ul>

    <h2>Configuration</h2>
    <p>Update your glue_cell_config.json to use these URLs:</p>
    <pre>
    "url": "http://localhost:5000/weight1"
    "url": "http://localhost:5000/weight2"
    "url": "http://localhost:5000/weight3"
    </pre>
    """

if __name__ == '__main__':
    print("=" * 60)
    print("Starting Mock Glue Weight Server")
    print("=" * 60)
    print("\nEndpoints:")
    print("  http://localhost:5000/weight1")
    print("  http://localhost:5000/weight2")
    print("  http://localhost:5000/weight3")
    print("  http://localhost:5000/status")
    print("\nUpdate your glue_cell_config.json URLs to:")
    print('  "url": "http://localhost:5000/weight1"')
    print('  "url": "http://localhost:5000/weight2"')
    print('  "url": "http://localhost:5000/weight3"')
    print("\nStarting weight simulation thread...")
    print("=" * 60)

    # Start background thread for weight simulation
    simulation_thread = threading.Thread(target=simulate_weight_changes, daemon=True)
    simulation_thread.start()

    # Start Flask server
    app.run(host='0.0.0.0', port=5000, debug=False)