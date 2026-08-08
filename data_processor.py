from flask import Flask, jsonify
import pandas as pd
import requests
import json
import math

app = Flask(__name__)

def _parse_numeric(col: pd.Series) -> pd.Series:
    """Extract the first numeric value from a messy string column."""
    return pd.to_numeric(
        col.astype(str).str.extract(r'([\d.]+)')[0], errors='coerce'
    ).fillna(0)

def _load_inventory(path: str) -> pd.DataFrame:
    """Load and clean the inventory CSV into a normalised DataFrame."""
    return (
        pd.read_csv(path)
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

def _call_granite(items: list, total_cost: float, weather: str, trend: str) -> str:
    """Send low-stock data and environmental context to the local Granite model."""
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

# This is the URL where your script will listen for the Mac guy
@app.route('/api/ai-advisor', methods=['GET'])
def ai_advisor_api():
    print("📥 Received request from Mac backend. Processing data...")

    try:
        # 1. LOAD AND CLEAN THE MESSY DATA
        df = _load_inventory('dummy_inventory1.csv')

        # 2. RUN BUSINESS LOGIC (Identify low stock & calculate buffer)
        low_stock = df[df['Stock'] <= df['Threshold']].copy()

        if low_stock.empty:
            return jsonify({"status": "Optimal", "ai_advice": "Inventory is fully stocked."})

        low_stock['Units to Order'] = (
            ((low_stock['Threshold'] * 1.2) - low_stock['Stock'])
            .apply(math.ceil)
            .clip(lower=0)
        )
        low_stock['Estimated Cost'] = low_stock['Units to Order'] * low_stock['Price_Num']

        total_cost = round(low_stock['Estimated Cost'].sum(), 2)
        report_cols = ["Item_Name", "Stock", "Units to Order", "Estimated Cost", "Supplier"]
        clean_items = low_stock[report_cols].to_dict(orient='records')

        # 3. ASK GRANITE AI FOR ADVICE
        print("🧠 Data cleaned! Pinging local IBM Granite AI with predictive context...")
        
        # --- MOCK CONTEXT FOR THE AI ---
        current_weather = "Heavy Monsoon Rains" 
        upcoming_trend = "Schools reopening next week"
        # -------------------------------
        
        ai_text = _call_granite(clean_items, total_cost, current_weather, upcoming_trend)

        # 4. PACKAGE EVERYTHING INTO JSON AND SEND TO MAC
        print("✅ Success! Sending JSON payload to Mac.")
        return jsonify({
            "status": "Restock Required",
            "total_cost_rupees": total_cost,
            "items_to_order": clean_items,
            "ai_advice": ai_text
        })

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": str(e)})

# Start the server on port 5000, listening to the local Wi-Fi (0.0.0.0)
if __name__ == '__main__':
    print("🚀 Kirana AI Backend Server is LIVE!")
    app.run(host='0.0.0.0', port=5000)