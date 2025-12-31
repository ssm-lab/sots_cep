import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as ctx

# Load CSV
df = pd.read_csv("app_examples/experiment_example/data/original/Beach_Water_and_Weather_Sensor_Locations_20250918.csv")

# Filter to selected beaches
BEACHES = ["Calumet Beach", "Montrose Beach", "63rd Street Beach"]
df_beaches = df[df["Sensor Name"].isin(BEACHES)]

# Convert to GeoDataFrame
gdf = gpd.GeoDataFrame(
    df_beaches,
    geometry=gpd.points_from_xy(df_beaches["Longitude"], df_beaches["Latitude"]),
    crs="EPSG:4326"
).to_crs(epsg=3857)  # Convert to Web Mercator for contextily tiles

# Plot
fig, ax = plt.subplots(figsize=(8, 8))
gdf.plot(ax=ax, color="dodgerblue", markersize=100, edgecolor="black")

# Add basemap tiles
ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)

# Add labels
for idx, row in gdf.iterrows():
    ax.text(row.geometry.x + 200, row.geometry.y + 200, row["Sensor Name"], fontsize=9)

# Remove axes and set bounds
ax.set_axis_off()
ax.set_title("Selected Chicago Beach Sensors", fontsize=12, pad=10)

# Save as PNG
plt.savefig( "app_examples/experiment_example/data/beaches_map.png", dpi=300, bbox_inches="tight")
plt.show()










