from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import requests
import json
import math

app = Flask(__name__)
CORS(app)

def _parse_numeric(col):
    return pd.to_numeric(col.astype(str).str.extract(r'([\d.]+)')[0], errors='coerce').fillna(0)

def _load_inventory(file_or_path):
    return (
        pd.read_csv(file_or_path)
        .dropna(subset=['Item Name'])
        .drop_duplicates()
        .assign(
            Category  = lambda x: x['Category'].astype(str).str.title().str.strip(),
            Item_Name = lambda x: x['Item Name'].astype(str).str.strip(),
            Supplier  = lambda x: x['Supplier'].fillna('Unknown Supplier').astype(str).str.strip(),
            Stock     = lambda x: _parse_numeric(x['Current Stock']),
            Threshold = lambda x: _parse_numeric(x['Reorder Threshold']),
            Price_Num = lambda x: _parse_numeric(x['Price']),
        )
    )

def _call_granite(items, total_cost, weather, trend):
    prompt = (
        f"You are a professional business advisor for an Indian Kirana store. "
        f"The current weather is '{weather}' and the upcoming local trend is '{trend}'. "
        f"Here is your current low stock data: {json.dumps(items)}. "
        f"The total cost to restock current inventory is ₹{total_cost}. "
        f"Write a short, professional 3 to 4 sentence alert to the store owner. "
        f"First, tell them what to prioritize from the low stock list. "
        f"Second, act as a predictive strategist: suggest 1 or 2 completely NEW product categories "
        f"they should immediately buy from wholesale to prepare for the '{weather}' weather and '{trend}' trend."
    )
    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "granite3.1-dense:8b", "prompt": prompt, "stream": False},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("response", "Error reading AI.")
    except requests.exceptions.ConnectionError:
        return "AI unavailable: Ollama is not running on this machine."
    except requests.exceptions.Timeout:
        return "AI unavailable: Ollama timed out after 30 seconds."

@app.route('/api/ai-advisor', methods=['POST'])
def ai_advisor_api():
    trend = request.args.get('trend', 'Schools reopening next week')
    weather = request.args.get('weather', 'Heavy Monsoon Rains')
    uploaded = request.files.get('file')

    try:
        df = _load_inventory(uploaded if uploaded else 'dummy_inventory1.csv')
        low_stock = df[df['Stock'] <= df['Threshold']].copy()

        if low_stock.empty:
            return jsonify({"status": "Optimal", "ai_advice": "Inventory is fully stocked.",
                             "items_to_order": [], "total_cost_rupees": 0})

        low_stock['Units to Order'] = (
            ((low_stock['Threshold'] * 1.2) - low_stock['Stock']).apply(math.ceil).clip(lower=0)
        )
        low_stock['Estimated Cost'] = low_stock['Units to Order'] * low_stock['Price_Num']
        total_cost = round(low_stock['Estimated Cost'].sum(), 2)

        report_cols = ["Item_Name", "Stock", "Units to Order", "Estimated Cost", "Supplier"]
        clean_items = low_stock[report_cols].to_dict(orient='records')

        ai_text = _call_granite(clean_items, total_cost, weather, trend)

        return jsonify({
            "status": "Restock Required",
            "total_cost_rupees": total_cost,
            "items_to_order": clean_items,
            "ai_advice": ai_text
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Kirana AI Backend is LIVE on port 5000!")
    app.run(host='0.0.0.0', port=5000)