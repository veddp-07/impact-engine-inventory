import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# 1. Set the visual style for the judges
plt.style.use('dark_background') # Looks very "hacker/developer" for a hackathon
sns.set_palette("muted")

def _parse_numeric(col: pd.Series) -> pd.Series:
    """Extract numeric values cleanly."""
    return pd.to_numeric(
        col.astype(str).str.extract(r'([\d.]+)')[0], errors='coerce'
    ).fillna(0)

print("📊 Loading Kirana Inventory Data for Visualization...")

# 2. Load and Clean Data
df = pd.read_csv('dummy_inventory1.csv')
df.dropna(subset=['Item Name'], inplace=True)
df.drop_duplicates(inplace=True)

df['Item_Name'] = df['Item Name'].astype(str).str.strip()
df['Stock'] = _parse_numeric(df['Current Stock'])
df['Threshold'] = _parse_numeric(df['Reorder Threshold'])

# Sort by lowest stock first for better visual impact
df = df.sort_values(by='Stock', ascending=True)

# ---------------------------------------------------------
# MOCK CONTEXT FOR THE JUDGES (Matches your AI backend)
current_weather = "Heavy Monsoon Rains"
upcoming_trend = "Schools reopening next week"
# ---------------------------------------------------------

# 3. Create the Visualization
fig, ax = plt.subplots(figsize=(12, 7))

# X locations for the groups
x = np.arange(len(df['Item_Name']))
width = 0.35  # width of the bars

# Plot Thresholds (The goal)
rects1 = ax.bar(x - width/2, df['Threshold'], width, label='Reorder Threshold (Minimum Needed)', color='#4C72B0')

# Plot Current Stock (The reality)
# Highlight bars in RED if they are below the threshold, GREEN if they are good
stock_colors = ['#C44E52' if stock <= thresh else '#55A868' for stock, thresh in zip(df['Stock'], df['Threshold'])]
rects2 = ax.bar(x + width/2, df['Stock'], width, label='Current Stock', color=stock_colors)

# Add labels and custom multi-line title showing the Weather Context!
ax.set_ylabel('Number of Units', fontsize=12)

chart_title = (
    "Kirana Store Inventory Health Analysis\n"
    f"Active AI Context: Weather = '{current_weather}' | Trend = '{upcoming_trend}'"
)
ax.set_title(chart_title, fontsize=15, fontweight='bold', pad=15)

ax.set_xticks(x)
ax.set_xticklabels(df['Item_Name'], rotation=45, ha='right', fontsize=10)
ax.legend()

# Add a horizontal grid to make it easier to read
ax.yaxis.grid(True, linestyle='--', alpha=0.5)
ax.xaxis.grid(False)

# Tweak spacing to prevent clipping of tick-labels
fig.tight_layout()

print("📈 Displaying Graph! (Close the graph window to stop the script)")
plt.show()