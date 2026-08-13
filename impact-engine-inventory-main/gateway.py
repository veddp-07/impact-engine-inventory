from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
# CORS is required so the i7 frontend laptop isn't blocked by security rules
CORS(app) 

# YOUR Windows laptop IP goes here!
AI_SERVER_URL = "http://10.124.126.153:5000/api/ai-advisor"

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    print("📥 Frontend is asking for data. Pinging the Windows AI Server...")
    
    # Grab the trend from the frontend URL (default to General if none provided)
    trend = request.args.get('trend', 'General Daily Sales')

    try:
        # 1. Mac server calls YOUR Windows server
        response = requests.get(f"{AI_SERVER_URL}?trend={trend}", timeout=15)
        response.raise_for_status()
        
        # 2. He grabs your giant JSON block
        ai_data = response.json()
        print("✅ Grabbed the JSON from Windows! Sending to Frontend...")

        # 3. He sends it exactly as-is to the i7 laptop
        return jsonify(ai_data)

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection failed: {e}")
        return jsonify({"error": "AI Backend is down or unreachable."}), 500

if __name__ == '__main__':
    # He runs on port 8000 to keep things separate
    print("💻 Mac Middleman Server is LIVE on port 8000!")
    app.run(host='0.0.0.0', port=8005)