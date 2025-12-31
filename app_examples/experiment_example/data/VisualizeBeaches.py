import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as ctx

plt.rcParams["font.family"] = "Times New Roman"
df = pd.read_csv("app_examples/experiment_example/data/original/Beach_Water_and_Weather_Sensor_Locations_20250918.csv")

# Filter to selected beaches
BEACHES = ["Calumet Beach", "Montrose Beach", "63rd Street Beach"]
df_beaches = df[df["Sensor Name"].isin(BEACHES)]

# Convert to GeoDataFrame
gdf = gpd.GeoDataFrame(
    df_beaches,
    geometry=gpd.points_from_xy(df_beaches["Longitude"], df_beaches["Latitude"]),
    crs="EPSG:4326"
).to_crs(epsg=3857)

# Plot
fig, ax = plt.subplots(figsize=(7, 7))
gdf.plot(ax=ax, color="lightblue", markersize=120, edgecolor="black", zorder=3)

# Add basemap
ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, zoom=12)

# Dynamic label placement
for _, row in gdf.iterrows():
    name = row["Sensor Name"]
    x, y = row.geometry.x, row.geometry.y

    if "Montrose" in name:
        ax.text(x + -3000, y + 900, name, fontsize=9, ha="left", color="black", zorder=4)
    elif "63rd" in name:
        ax.text(x, y + 900, name, fontsize=9, ha="center", color="black", zorder=4)
    elif "Calumet" in name:
        ax.text(x + 3000, y + 900, name, fontsize=9, ha="right", color="black", zorder=4)

ax.set_axis_off()
ax.set_title("")

buffer = 4000
xmin, ymin, xmax, ymax = gdf.total_bounds
ax.set_xlim(xmin - buffer, xmax + buffer)
ax.set_ylim(ymin - buffer, ymax + buffer)

plt.savefig("app_examples/experiment_example/data/beaches_map.png", dpi=300, bbox_inches="tight")
plt.show()
